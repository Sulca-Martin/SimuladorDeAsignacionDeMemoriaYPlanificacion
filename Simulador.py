import sys
import os

def main():
        
    while True:
        print("Seleccione una opcion:")
        print("1. Leer archivo CSV")
        print("2. Elegir archivo CSV")
        print("3. Acerca del simulador")
        print("4. Salir")
        opcion = input("Opcion: ").strip()
        clear_pantalla()
        if opcion == "1":
            try:
                with open("principal.csv", "r", newline="", encoding="utf-8-sig") as archivo:
                    lector = archivo.read()
                    print(lector)
            except FileNotFoundError:
                print("No existe el archivo CSV. Por favor, cree un archivo CSV con el nombre 'principal.csv' para continuar.")
        elif opcion == "2":
            nombre_archivo = input("Ingrese el nombre del archivo CSV (con extensión .csv): ").strip()
            try:
                with open(nombre_archivo, "r", newline="", encoding="utf-8-sig") as archivo:
                    lector = archivo.read()
                    print(lector)
            except FileNotFoundError:
                print(f"No se encontró el archivo '{nombre_archivo}'. Por favor, asegúrese de que el archivo exista.")
        elif opcion == "3":
            print("\nSimulador de CSV - Version 1.0")
            print("Desarrollado por el grupo 5\n")
        elif opcion == "4":
            print("Saliendo del simulador.")
            return
        else:
            print("Opcion invalida. Por favor intente de nuevo.\n")
        input()
        clear_pantalla()
    
def clear_pantalla():
    if sys.platform.startswith("win"):
        _ = os.system("cls")
    else:
        _ = os.system("clear")
        
if __name__ == "__main__":
    main()
