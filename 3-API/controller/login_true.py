from model.database import validar_usuario

def verificar_login(username, password):
    if validar_usuario(username, password):
        return True
    else:
        return False