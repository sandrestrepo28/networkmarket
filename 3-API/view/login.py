import customtkinter as ctk
import tkinter.messagebox as tkmb
from controller.login_true import verificar_login
from controller.api_pokemon import get_pokemon

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("400x400")
app.title("Login de Usuario")

def mostrar_pokemon():
    for widget in frame.winfo_children():
        widget.destroy()

    label = ctk.CTkLabel(master=frame, text='Buscar Pokémon')
    label.pack(pady=12, padx=10)
    
    search_entry = ctk.CTkEntry(master=frame, placeholder_text="Nombre del Pokémon")
    search_entry.pack(pady=12, padx=10)

    result_label = ctk.CTkLabel(master=frame, text='')
    result_label.pack(pady=12, padx=10)

    def search():
        name = search_entry.get().strip().replace(" ", "")
        info = get_pokemon(name)
        if info:
            result = (
                f"---Información del Pokémon---\n"
                f"Nombre: {info['name']}\n"
                f"Experiencia base: {info['base_experience']}\n"
                f"Tipo: {info['type']}\n"
                f"Altura: {info['height']}\n"
                f"Peso: {info['weight']}"
            )
        else:
            result = "Pokémon no encontrado."
        result_label.configure(text=result)

    search_button = ctk.CTkButton(master=frame, text='Buscar', command=search)
    search_button.pack(pady=12, padx=10)
    

def login():

    username = user_entry.get()
    password = user_pass.get()
    
    if verificar_login(username, password):
        tkmb.showinfo(title="Login Exitoso", message="Has iniciado sesión correctamente")
        mostrar_pokemon()
    elif user_entry.get() == username and user_pass.get() != password:
        tkmb.showwarning(title='Contraseña incorrecta', message='Por favor verifica tu contraseña')
    elif user_entry.get() != username and user_pass.get() == password:
        tkmb.showwarning(title='Usuario incorrecto', message='Por favor verifica tu usuario')
    else:
        tkmb.showerror(title="Error de inicio de sesión", message="Usuario y contraseña inválidos")


frame = ctk.CTkFrame(master=app)
frame.pack(pady=20,padx=40,fill='both',expand=True)

label = ctk.CTkLabel(master=frame,text='Login de Usuario')
label.pack(pady=12,padx=10)

user_entry= ctk.CTkEntry(master=frame,placeholder_text="Usuario")
user_entry.pack(pady=12,padx=10)

user_pass= ctk.CTkEntry(master=frame,placeholder_text="Contraseña",show="*")
user_pass.pack(pady=12,padx=10)

button = ctk.CTkButton(master=frame,text='Login',command=login)
button.pack(pady=12,padx=10)

app.mainloop()