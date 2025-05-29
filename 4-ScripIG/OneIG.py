from instagrapi import Client
import openpyxl
import os
import time
import random
import json
import concurrent.futures
import threading
from json.decoder import JSONDecodeError
from instagrapi.exceptions import (
    PrivateError,
    UserNotFound,
    PleaseWaitFewMinutes,
    ChallengeRequired,
    UserError,
    ClientError
)

# Credenciales
USERNAME = "zerodeep720"
PASSWORD = "Zero123..."

# Configuración del Usuario
cl = Client()
cl.delay_range = (20, 30)  

# Control de resultados y sincronización
result_lock = threading.Lock()
processed_results = []
target_count = 5  
should_stop = threading.Event() 

# Función de espera inteligente
def smart_sleep(min_time=20, max_time=30):
    base_delay = random.uniform(min_time, max_time)
    jitter = random.uniform(0, 5)  
    time_to_sleep = base_delay + jitter
    time.sleep(time_to_sleep)
    return time_to_sleep

def is_account_private(username):
    # Verifica si una cuenta es privada
    try:
        user_info = cl.user_info_by_username(username)
        if user_info and hasattr(user_info, 'is_private'):
            return user_info.is_private
        return False
    except Exception as e:
        print(f"Error verificando privacidad de @{username}: {e}")
        return None

def get_last_post_date(user_id, is_private=False):
    # Obtiene la fecha de la publicación más reciente
    if is_private:
        return "No disponible (cuenta privada)"
    
    try:
        posts, end_cursor = cl.user_medias_paginated(user_id, 5)
        if posts:
            last_post = max(posts, key=lambda x: x.taken_at)
            last_date = last_post.taken_at.replace(tzinfo=None)
            return last_date
        else:
            return "Sin publicaciones"
    except Exception as e:
        error_msg = str(e)
        print(f"Error obteniendo fecha: {error_msg[:50]}")
        return f"Error: {error_msg[:30]}"

def get_user_info_safely(user_id, username):
    # Obtener información del usuario de forma segura
    try:
        return cl.user_info_by_username(username), True
    except Exception as e:
        if "user not found" in str(e).lower():
            return None, False
        pass
        
    try:
        return cl.user_info(user_id), True
    except Exception as e:
        error_str = str(e).lower()
        
        if "jsondecodeerror" in error_str:
            try:
                time.sleep(3)
                user_data = cl.user_short_gql(user_id)
                if user_data:
                    return user_data, True
            except Exception:
                pass
        return None, False

def process_follower_complete(follower_id, follower, target_username):
    global processed_results
    
    if should_stop.is_set():
        return None
    
    try:
        print(f"🧵 Procesando: @{follower.username}")
        
        is_private = is_account_private(follower.username)
        
        if is_private is True:
            print(f"🔒 @{follower.username} es una cuenta privada - saltando")
            return None
            
        print(f"🔓 @{follower.username} es una cuenta pública - procesando")
        
        follower_info, success = get_user_info_safely(follower_id, follower.username)
        
        if not success:
            print(f"❌ No se pudo obtener información para @{follower.username}")
            return None
        
        last_date = get_last_post_date(follower_info.pk, False)
        
        result = {
            "target": target_username,
            "username": getattr(follower_info, 'username', follower.username),
            "full_name": getattr(follower_info, 'full_name', 'No disponible'),
            "phone": getattr(follower_info, 'contact_phone_number', 'No disponible') or 'No disponible',
            "email": getattr(follower_info, 'public_email', 'No disponible') or 'No disponible',
            "url": f"https://www.instagram.com/{follower.username}/",
            "last_date": last_date
        }
        
        with result_lock:
            processed_results.append(result)
            current_count = len(processed_results)
            print(f"✅ Procesado {current_count}/{target_count}: @{follower.username}")
            
            if current_count >= target_count:
                should_stop.set()
                print("🏁 Objetivo alcanzado! Señalizando para detener otros hilos.")
        
        return result
        
    except Exception as e:
        print(f"❌ Error procesando @{follower.username}: {e}")
        return None

# Función principal con agrupación inteligente
def main():
    try:
        # Manejo de sesión
        if os.path.exists("session.json"):
            cl.load_settings("session.json")
            cl.login(USERNAME, PASSWORD)
        else:
            cl.login(USERNAME, PASSWORD)
            cl.dump_settings("session.json")
        
        print(f"\n✅ Sesión iniciada como @{USERNAME}")
        
        # Cuenta objetivo
        target_username = "elcorteingles"
        user_id = cl.user_id_from_username(target_username)
        
        # Preparar Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Seguidores"
        ws.append([
            "IG Pagina",
            "IG Usuario", 
            "Nombre completo",
            "Numero de telefono",
            "Correo electronico", 
            "URL del ig del usuario",
            "Ultima fecha de publicación"
        ])
        
        # Obtener seguidores en pequeños lotes
        print("⏳ Obteniendo 30 seguidores iniciales...")
        followers = cl.user_followers(user_id, amount=15)
        followers_list = list(followers.items())
        random.shuffle(followers_list)
        
        print(f"📋 Iniciando procesamiento paralelo de {len(followers_list)} seguidores...")
        
        # Procesar en paralelo directamente con 2 workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Enviar todos los seguidores a procesar
            futures = {
                executor.submit(process_follower_complete, fid, f, target_username): (fid, f)
                for fid, f in followers_list
            }
            
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                if should_stop.is_set():
                    for f in futures:
                        if not f.done():
                            f.cancel()
                    break
                    
                if i > 0 and i % 2 == 0:
                    time.sleep(random.uniform(3, 7))
        
        # Guardar resultados en Excel
        print(f"\n✓ Procesamiento completado. Guardando {len(processed_results)} resultados...")
        
        for result in processed_results:
            ws.append([
                result["target"],
                result["username"],
                result["full_name"],
                result["phone"],
                result["email"],
                result["url"],
                result["last_date"]
            ])
        
        # Guardar archivo final
        wb.save("seguidores.xlsx")
        print(f"\n✅ Archivo 'seguidores.xlsx' generado correctamente con {len(processed_results)} usuarios.")
        cl.logout()
        
    except Exception as e:
        print(f"\n❌ Error general: {e}")
    finally:
        try:
            cl.logout()
        except:
            pass

if __name__ == "__main__":
    main()