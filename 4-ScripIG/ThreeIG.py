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
USERNAME = "TU_USUARIO"
PASSWORD = "TU_CONTRASENA"

# Configuración del Usuario
cl = Client()
cl.delay_range = (20, 30)  

# Control de resultados y sincronización para cada cuenta
def create_account_controls():
    return {
        "result_lock": threading.Lock(),
        "processed_results": [],
        "target_count": 5,  
        "should_stop": threading.Event() 
    }

# Diccionario para almacenar controles por cuenta
account_controls = {}

# Función de espera inteligente
def smart_sleep(min_time=20, max_time=30):
    base_delay = random.uniform(min_time, max_time)
    jitter = random.uniform(0, 5)  
    time_to_sleep = base_delay + jitter
    print(f"Esperando {time_to_sleep:.1f} segundos...")
    time.sleep(time_to_sleep)
    return time_to_sleep

# Verificar si una cuenta es privada
def is_account_private(username):
    try:
        user_info = cl.user_info_by_username(username)
        if user_info and hasattr(user_info, 'is_private'):
            return user_info.is_private
        return False
    except Exception as e:
        print(f"Error verificando privacidad de @{username}: {e}")
        return None

# Obtiene la fecha de la publicación más reciente
def get_last_post_date(user_id, is_private=False):
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

# Obtiene información del usuario de forma segura
def get_user_info_safely(user_id, username):
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

# Procesa un seguidor específico
def process_follower_complete(follower_id, follower, target_username):

    controls = account_controls[target_username]
    
    if controls["should_stop"].is_set():
        return None
    
    try:
        print(f"🧵 [{target_username}] Procesando: @{follower.username}")
        
        is_private = is_account_private(follower.username)
        
        if is_private is True:
            print(f"🔒 [{target_username}] @{follower.username} es una cuenta privada - saltando")
            return None
            
        print(f"🔓 [{target_username}] @{follower.username} es una cuenta pública - procesando")
        
        follower_info, success = get_user_info_safely(follower_id, follower.username)
        
        if not success:
            print(f"❌ [{target_username}] No se pudo obtener información para @{follower.username}")
            return None
        
        last_date = get_last_post_date(follower_info.pk, False)

        # Crear resultado
        result = {
            "target": target_username,
            "username": getattr(follower_info, 'username', follower.username),
            "full_name": getattr(follower_info, 'full_name', 'No disponible'),
            "phone": getattr(follower_info, 'contact_phone_number', 'No disponible') or 'No disponible',
            "email": getattr(follower_info, 'public_email', 'No disponible') or 'No disponible',
            "url": f"https://www.instagram.com/{follower.username}/",
            "last_date": last_date
        }
        
        # Guardar resultado
        with controls["result_lock"]:
            controls["processed_results"].append(result)
            current_count = len(controls["processed_results"])
            print(f"✅ [{target_username}] Procesado {current_count}/{controls['target_count']}: @{follower.username}")
            
            if current_count >= controls['target_count']:
                controls["should_stop"].set()
                print(f"🏁 [{target_username}] Objetivo alcanzado! Señalizando para detener otros hilos.")
        
        return result
        
    except Exception as e:
        print(f"❌ [{target_username}] Error procesando @{follower.username}: {e}")
        return None

# Procesa una cuenta de Instagram específica
def process_single_account(target_username, wb, ws):
    
    print(f"\n🎯 INICIANDO PROCESAMIENTO DE @{target_username.upper()} 🎯")
    
    # Inicializar controles para esta cuenta
    account_controls[target_username] = create_account_controls()
    controls = account_controls[target_username]
    
    try:
        user_id = cl.user_id_from_username(target_username)
        
        # Obtener seguidores
        print(f"⏳ Obteniendo 15 seguidores de @{target_username}...")
        followers = cl.user_followers(user_id, amount=15)
        followers_list = list(followers.items())
        random.shuffle(followers_list)  
        
        print(f"📋 Iniciando procesamiento paralelo de {len(followers_list)} seguidores de @{target_username}...")
        
        # Procesar en paralelo con 2 workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(process_follower_complete, fid, f, target_username): (fid, f)
                for fid, f in followers_list
            }
            
            # Mostrar progreso
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                if controls["should_stop"].is_set():
                    for f in futures:
                        if not f.done():
                            f.cancel()
                    break
                    
                # Pequeña pausa para dar espacio entre inicios de solicitudes
                if i > 0 and i % 2 == 0:
                    time.sleep(random.uniform(3, 7))
        
        # Guardar resultados en Excel
        print(f"✓ Procesamiento de @{target_username} completado. {len(controls['processed_results'])} resultados.")
        
        for result in controls["processed_results"]:
            ws.append([
                result["target"],
                result["username"],
                result["full_name"],
                result["phone"],
                result["email"],
                result["url"],
                result["last_date"]
            ])
            
        # Guardar un Excel de respaldo después de cada cuenta
        wb.save(f"seguidores_hasta_{target_username}.xlsx")
        print(f"Progreso guardado hasta @{target_username}")
        
        return len(controls["processed_results"])
        
    except Exception as e:
        print(f"❌ Error procesando cuenta @{target_username}: {e}")
        return 0

# Función principal
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
        
        # Preparar Excel (único para todas las cuentas)
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
        
        # Lista de cuentas a procesar
        target_accounts = ["elcorteingles", "mercadona", "carrefoures"]
        total_processed = 0
        
        # Procesar cada cuenta secuencialmente
        for i, account in enumerate(target_accounts):
            count = process_single_account(account, wb, ws)
            total_processed += count
            
            if i < len(target_accounts) - 1:
                next_account = target_accounts[i+1]
                if i == 0:  
                    pause_time = 90
                    print(f"⏱️ Pausa de {pause_time} segundos antes de procesar @{next_account}...")
                else:
                    pause_time = 120
                    print(f"⏱️ Pausa de {pause_time} segundos antes de procesar @{next_account}...")
            time.sleep(pause_time)

        # Guardar archivo final
        wb.save("seguidores_todas_cuentas.xlsx")
        print(f"\n✅ Archivo 'seguidores_todas_cuentas.xlsx' generado correctamente con {total_processed} usuarios.")
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