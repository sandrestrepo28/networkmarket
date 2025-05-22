import random

def numero_mas_frecuente(lista):
    return min(set(lista), key=lambda x: (-lista.count(x), x))

print("Bienvenido al menu de listas, por favor elige una opcion")
print("⚠️\x1b[33m  Solo se aceptan números enteros\x1b[0m")
print("--Menu de listas--")

while True:

    print("1| Crear lista")
    print("2| Crear lista automatica")
    print("3| Salir")
    opc = input("Elige una opcion: ")

    if opc == "1":
        print("Crear lista manual")
        
        lista = []
        while True:
            numero = input("Introduce un numero (o 'fin' para terminar): ")
            if numero.lower() == "fin":
                break
            try:
                lista.append(int(numero))
            except ValueError:
                print("⚠️\x1b[33m  Solo se aceptan números enteros positivos y enteros\x1b[0m")
        print("Lista creada:", lista)
        print("El número más frecuente es:", numero_mas_frecuente(lista))
        
    elif opc == "2":
        print("Crear lista automatica")
                
        lista = [random.randint(1, 15) for _ in range(15)]
        print("Lista creada:", lista)
        print("El número más frecuente es:", numero_mas_frecuente(lista))
        
    elif opc == "3":
        print("Saliendo...")
        break
    else:
        print("⚠️\x1b[33m  Opcion no valida\x1b[0m")