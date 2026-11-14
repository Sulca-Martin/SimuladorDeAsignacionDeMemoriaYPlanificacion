import csv
import sys
import os


def leer_csv(ruta):
    try:
        with open(ruta, "r", newline="", encoding="utf-8-sig") as archivo:
            lector = csv.DictReader(archivo)
            return lector.fieldnames, list(lector)
    except FileNotFoundError:
        print(f"Error: no se encontro el archivo '{ruta}'")
        return None, None
    except PermissionError:
        print(f"Error: sin permisos para leer '{ruta}'")
        return None, None
    except UnicodeDecodeError:
        print(f"Error: no se pudo decodificar '{ruta}' (verifique la codificacion)")
        return None, None


def mostrar(columnas, filas):
    if not columnas:
        print("El archivo CSV esta vacio o no tiene encabezados.")
        return
    print(" | ".join(columnas))
    print("-" * (len(" | ".join(columnas))))
    for fila in filas:
        print(" | ".join(str(fila.get(col, "")) for col in columnas))
    print(f"\nTotal de filas: {len(filas)}")


def main():
        
    while True:
        print("Seleccione una opcion:")
        print("1. Leer archivo CSV")
        print("2. Acerca del simulador")
        print("3. Salir")
        opcion = input("Opcion: ").strip()
        clear_pantalla()
        if opcion == "1":
            try:
                with open("prueba.csv", "r", newline="", encoding="utf-8-sig") as archivo:
                    lector = archivo.read()
                    print(lector)
            except FileNotFoundError:
                print("No existe el archivo CSV. Por favor, cree un archivo CSV con el nombre 'prueba.csv' para continuar.")
            
        elif opcion == "2":
            print("\nSimulador de CSV - Version 1.0")
            print("Desarrollado por el grupo 5\n")
        elif opcion == "3":
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
