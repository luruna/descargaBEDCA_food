# -----------------------------------------------------------------------------
# GASTRO-MINER LAUNCHER
# -----------------------------------------------------------------------------
# Punto de entrada principal para la ejecución del motor de extracción de datos.
# Gestiona el ciclo de vida de la aplicación, control de errores y métricas.
# -----------------------------------------------------------------------------

import os
import sys
# Compatibilidad con layout antiguo: permitir importar `GastroMiner` desde ./src/
here = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(here, 'src')
if os.path.isdir(src_dir) and src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from GastroMiner import GastroMiner
import datetime
import time

def print_banner():
    """Imprime un banner estilizado para mejorar la presentación en consola."""
    print(r"""
   ______            __               __  ___   _                 
  / ____/____ ______/ /_ _____ ____  /  |/  /  (_)____   ___   _____
 / / __ / __ `/ ___/ __// ___// __ \/ /|_/ /  / // __ \ / _ \ / ___/
/ /_/ // /_/ (__  ) /_ / /   / /_/ / /  / /  / // / / //  __// /    
\____/ \__,_/____/\__//_/    \____/_/  /_/  /_//_/ /_/ \___//_/     
    
    >> MOTOR DE EXTRACCIÓN NUTRICIONAL v2.1 <<
    """)

if __name__ == "__main__":
    print_banner()

    # 1. Inicialización del Motor (Control de Dependencias)
    print("[*] Inicializando núcleo del sistema (GastroMiner)...")
    try:
        # Se crea la instancia de la clase principal, que inicializa la sesión HTTP y el fichero CSV.
        data_miner = GastroMiner()
    except Exception as e:
        print(f"[!] ERROR FATAL al inicializar GastroMiner. Verifique constantes y permisos de I/O: {e}")
        sys.exit(1)

    # 2. Configuración de Tiempos
    start_timestamp = datetime.datetime.now()
    start_perf_counter = time.time()
    
    print(f"[*] Hora de inicio de la secuencia: {start_timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
    print("[*] Iniciando proceso de minería de datos concurrente...")
    print("-" * 60)

    # 3. Ejecución del Proceso Principal (Secuencia Crítica)
    try:
        data_miner.execute()
    except KeyboardInterrupt:
        # Manejo de la interrupción de teclado (Ctrl+C)
        print("\n\n[!] Interrupción manual detectada (SIGINT). Deteniendo el proceso limpiamente.")
        sys.exit(0)
    except Exception as e:
        # Captura de cualquier otra excepción no manejada
        print(f"\n[!] ERROR NO CONTROLADO durante la ejecución: {e}")
        sys.exit(1)

    # 4. Cálculo de Métricas Finales
    end_timestamp = datetime.datetime.now()
    end_perf_counter = time.time()
    elapsed_seconds = end_perf_counter - start_perf_counter
    
    # Formato de tiempo total en minutos y segundos
    mins, secs = divmod(elapsed_seconds, 60)

    print("-" * 60)
    print(">> INFORME DE EJECUCIÓN <<")
    print(f"[*] Hora de finalización : {end_timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"[*] Tiempo de minería    : {int(mins)}m {int(secs)}s ({elapsed_seconds:.2f} segundos)")
    print("[*] Estado               : OPERACIÓN COMPLETADA EXITOSAMENTE")
    print("-" * 60)