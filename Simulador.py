import csv
import os
import sys
from dataclasses import dataclass

MEMORIA_SO = 100             
MEMORIA_USUARIOS = 450       
MAX_PROCESOS_ARCHIVO = 10    
GRADO_MULTIPROG = 5           

NUEVO = "Nuevo"
LISTO = "Listo"
LISTO_SUSP = "Listo y Suspendido"
EJECUCION = "Ejecución"
TERMINADO = "Terminado"


@dataclass(eq=False)
class Proceso:
    id: str
    tam: int
    arribo: int
    irrupcion: int
    restante: int = 0
    estado: str = NUEVO
    fin: int = None

    def __post_init__(self):
        self.restante = self.irrupcion


#lectura de csv
def _es_entero(txt):
    try:
        int(txt)
        return True
    except ValueError:
        return False


def cargar_procesos(ruta):
    with open(ruta, "r", newline="", encoding="utf-8-sig") as f:
        muestra = f.read(2048)
        f.seek(0)
        try:
            dialecto = csv.Sniffer().sniff(muestra, delimiters=",;\t")
        except csv.Error:
            dialecto = csv.excel
        filas = list(csv.reader(f, dialecto))

    procesos, ids = [], set()
    for n, fila in enumerate(filas, start=1):
        fila = [c.strip() for c in fila if c.strip() != ""]
        if not fila:
            continue
        if n == 1 and not all(_es_entero(c) for c in fila[1:4]):
            continue  # encabezado
        if len(fila) < 4 or not all(_es_entero(c) for c in fila[1:4]):
            print(f"[!] Fila {n} inválida, se ignora: {fila}")
            continue
        pid, tam, arribo, irr = fila[0], int(fila[1]), int(fila[2]), int(fila[3])
        if pid in ids:
            print(f"[!] Fila {n}: id '{pid}' repetido, se ignora.")
            continue
        if tam <= 0 or irr <= 0 or arribo < 0:
            print(f"[!] Fila {n}: valores no válidos, se ignora.")
            continue
        if tam > MEMORIA_USUARIOS:
            print(f"[!] Fila {n}: {pid} pide {tam}K y solo hay {MEMORIA_USUARIOS}K "
                  f"para usuarios; nunca podría ejecutarse. Se ignora.")
            continue
        ids.add(pid)
        procesos.append(Proceso(pid, tam, arribo, irr))

    if len(procesos) > MAX_PROCESOS_ARCHIVO:
        print(f"[!] Se permiten máximo {MAX_PROCESOS_ARCHIVO} procesos; "
              f"se toman los primeros {MAX_PROCESOS_ARCHIVO}.")
        procesos = procesos[:MAX_PROCESOS_ARCHIVO]
    return procesos


#algorimos de memoria y particones
class Memoria:
    def __init__(self):
        self.particiones = [
            {"inicio": MEMORIA_SO, "tam": MEMORIA_USUARIOS, "pid": None, "usado": 0}
        ]

    def asignar_best_fit(self, p):
        huecos = [x for x in self.particiones if x["pid"] is None and x["tam"] >= p.tam]
        if not huecos:
            return False
        h = min(huecos, key=lambda x: (x["tam"], x["inicio"]))
        if h["tam"] > p.tam:
            idx = self.particiones.index(h)
            self.particiones.insert(
                idx, {"inicio": h["inicio"], "tam": p.tam, "pid": p.id, "usado": p.tam}
            )
            h["inicio"] += p.tam
            h["tam"] -= p.tam
        else:
            h["pid"] = p.id
            h["usado"] = p.tam
        return True

    def liberar(self, pid):
        for x in self.particiones:
            if x["pid"] == pid:
                x["pid"] = None
                x["usado"] = 0
                break
        # Unir huecos libres contiguos
        fusionadas = []
        for x in self.particiones:
            if fusionadas and fusionadas[-1]["pid"] is None and x["pid"] is None:
                fusionadas[-1]["tam"] += x["tam"]
            else:
                fusionadas.append(x)
        self.particiones = fusionadas

    def mostrar(self):
        print("Tabla de particiones de memoria:")
        print(f"  {'Id':<5}{'Inicio':>8}{'Tamaño':>9}  {'Proceso':<9}{'Frag. interna':>14}")
        print(f"  {'SO':<5}{'0K':>8}{str(MEMORIA_SO) + 'K':>9}  {'(sistema)':<9}{'-':>14}")
        for i, x in enumerate(self.particiones, start=1):
            pid = x["pid"] if x["pid"] is not None else "libre"
            frag = f"{x['tam'] - x['usado']}K" if x["pid"] is not None else "-"
            print(f"  {i:<5}{str(x['inicio']) + 'K':>8}{str(x['tam']) + 'K':>9}  "
                  f"{pid:<9}{frag:>14}")

# simulacion 
class Simulador:
    def __init__(self, procesos):
        self.pendientes = sorted(procesos, key=lambda p: (p.arribo, p.id))  # aún no llegaron
        self.total = len(procesos)
        self.todos = list(procesos)
        self.memoria = Memoria()
        self.nuevos = []         
        self.listos = []          
        self.suspendidos = []     
        self.terminados = []
        self.cpu = None
        self.t = 0
        self.eventos = []
        self.hubo_liberacion = False   

    def en_sistema(self):
        return len(self.listos) + len(self.suspendidos) + (1 if self.cpu else 0)

    def admitir(self):
        if self.hubo_liberacion:
            self.hubo_liberacion = False
            for p in list(self.suspendidos):
                if self.memoria.asignar_best_fit(p):
                    self.suspendidos.remove(p)
                    p.estado = LISTO
                    self.listos.append(p)
                    self.eventos.append(f"{p.id} pasa de Listo/Suspendido a Listo "
                                        f"(se le asignó memoria)")
        while self.nuevos and self.en_sistema() < GRADO_MULTIPROG:
            p = self.nuevos.pop(0)
            if self.suspendidos:
                p.estado = LISTO_SUSP
                self.suspendidos.append(p)
                self.eventos.append(f"{p.id} admitido -> al final de Listos y Suspendidos "
                                    f"(ya había suspendidos)")
            elif self.memoria.asignar_best_fit(p):
                p.estado = LISTO
                self.listos.append(p)
                self.eventos.append(f"{p.id} admitido y cargado en memoria")
            else:
                p.estado = LISTO_SUSP
                self.suspendidos.append(p)
                self.eventos.append(f"{p.id} admitido pero sin memoria -> Listo y Suspendido")

    def planificar(self):
        candidatos = list(self.listos)
        if self.cpu:
            candidatos.append(self.cpu)
        if not candidatos:
            return
        mejor = min(candidatos, key=lambda p: (p.restante, p is not self.cpu, p.arribo))
        if mejor is self.cpu:
            return
        if self.cpu:
            self.cpu.estado = LISTO
            self.listos.append(self.cpu)
            self.eventos.append(f"{self.cpu.id} desalojado por {mejor.id} (SRTF)")
        self.listos.remove(mejor)
        mejor.estado = EJECUCION
        self.cpu = mejor


    @staticmethod
    def _fmt_cola(cola):
        if not cola:
            return "vacía"
        return ", ".join(f"{p.id}(rest={p.restante}, {p.tam}K)" for p in cola)

    def mostrar_estado(self):
        print("\n" + "=" * 64)
        print(f"t = {self.t}  |  " + " ; ".join(self.eventos))
        print("=" * 64)
        if self.cpu:
            print(f"Procesador: ejecutando {self.cpu.id} "
                  f"(restante {self.cpu.restante} de {self.cpu.irrupcion})")
        else:
            print("Procesador: ocioso")
        self.memoria.mostrar()
        print("Cola de Listos (por menor restante):",
              self._fmt_cola(sorted(self.listos, key=lambda p: (p.restante, p.arribo))))
        print("Cola de Listos y Suspendidos:", self._fmt_cola(self.suspendidos))
        print("Nuevos esperando admisión:", self._fmt_cola(self.nuevos))
        print(f"Procesos en el sistema: {self.en_sistema()}/{GRADO_MULTIPROG}")

    def informe(self):
        print("\n" + "=" * 64)
        print("INFORME ESTADÍSTICO")
        print("=" * 64)
        print(f"{'Proceso':<10}{'Arribo':>8}{'Irrup.':>8}{'Fin':>6}{'Retorno':>9}{'Espera':>8}")
        suma_ret = suma_esp = 0
        for p in sorted(self.todos, key=lambda p: (p.arribo, p.id)):
            if p.fin is None:
                print(f"{p.id:<10}{'(no terminó)':>39}")
                continue
            retorno = p.fin - p.arribo
            espera = retorno - p.irrupcion
            suma_ret += retorno
            suma_esp += espera
            print(f"{p.id:<10}{p.arribo:>8}{p.irrupcion:>8}{p.fin:>6}{retorno:>9}{espera:>8}")
        n = len(self.terminados)
        if n:
            print(f"\nTiempo de retorno promedio: {suma_ret / n:.2f}")
            print(f"Tiempo de espera promedio:  {suma_esp / n:.2f}")
            t_final = max(p.fin for p in self.terminados)
            print(f"Rendimiento del sistema: {n} trabajos / {t_final} unidades "
                  f"= {n / t_final:.4f} trabajos por unidad de tiempo")


    def correr(self):
        while True:

            while self.pendientes and self.pendientes[0].arribo <= self.t:            
                p = self.pendientes.pop(0)
                self.nuevos.append(p)
                self.eventos.append(f"Llega {p.id}")
            self.admitir()
            self.planificar()
            if self.eventos:
                self.mostrar_estado()
                self.eventos.clear()
                if len(self.terminados) < self.total:
                    input("\n[Enter] para continuar al próximo evento...")
            if len(self.terminados) == self.total:
                break
            if self.cpu is None:
                if self.pendientes:
                    self.t = self.pendientes[0].arribo
                    continue
                print("[!] No quedan procesos ejecutables; la simulación se detiene.")
                break
            self.cpu.restante -= 1
            self.t += 1
            if self.cpu.restante == 0:
                p = self.cpu
                p.estado = TERMINADO
                p.fin = self.t
                self.memoria.liberar(p.id)
                self.hubo_liberacion = True
                self.terminados.append(p)
                self.eventos.append(f"Termina {p.id}")
                self.cpu = None
        self.informe()


# Menu

def ejecutar(nombre_archivo):
    try:
        procesos = cargar_procesos(nombre_archivo)
    except FileNotFoundError:
        print(f"No se encontró el archivo '{nombre_archivo}'. "
              f"Por favor, asegúrese de que el archivo exista.")
        return
    if not procesos:
        print("El archivo no contiene procesos válidos.")
        return
    print(f"Procesos cargados desde '{nombre_archivo}':")
    print(f"  {'Id':<8}{'Tamaño':>8}{'Arribo':>8}{'Irrup.':>8}")
    for p in procesos:
        print(f"  {p.id:<8}{str(p.tam) + 'K':>8}{p.arribo:>8}{p.irrupcion:>8}")
    input("\n[Enter] para iniciar la simulación...")
    Simulador(procesos).correr()


def main():
    while True:
        print("Seleccione una opcion:")
        print("1. Simular con principal.csv")
        print("2. Elegir archivo CSV")
        print("3. Acerca del simulador")
        print("4. Salir")
        opcion = input("Opcion: ").strip()
        clear_pantalla()
        if opcion == "1":
            ejecutar("principal.csv")
        elif opcion == "2":
            nombre_archivo = input("Ingrese el nombre del archivo CSV (con extensión .csv): ").strip()
            ejecutar(nombre_archivo)
        elif opcion == "3":
            print("\nSimulador de memoria (MVT, Best-Fit) y planificación SRTF - Version 2.0")
            print("Desarrollado por el grupo 5\n")
        elif opcion == "4":
            print("Saliendo del simulador.")
            return
        else:
            print("Opcion invalida. Por favor intente de nuevo.\n")
        input("\n[Enter] para volver al menú...")
        clear_pantalla()


def clear_pantalla():
    if sys.platform.startswith("win"):
        _ = os.system("cls")
    else:
        _ = os.system("clear")


if __name__ == "__main__":
    main()