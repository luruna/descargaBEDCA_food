# -----------------------------------------------------------------------------
# MOTOR DE EXTRACCIÓN GASTRO-MINER
# -----------------------------------------------------------------------------
# Implementa un sistema de web scraping altamente optimizado para la base de
# datos nutricional de BEDCA, utilizando concurrencia (multi-threading) y
# persistencia de conexiones HTTP (Keep-Alive).
# -----------------------------------------------------------------------------

import os
import sys
# Compatibilidad con layout antiguo: permitir importar módulos desde ./src/
here = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(here, 'src')
if os.path.isdir(src_dir) and src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from bs4 import BeautifulSoup
import constants
import csv
import requests
import sys
import time
import urllib.robotparser
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class GastroMiner:
    """
    Clase principal del motor de extracción de datos nutricionales.
    Gestiona la conexión, la orquestación de tareas concurrentes y la
    escritura segura de resultados a disco.
    """

    def __init__(self):
        """
        Inicializa el motor minero.
        Configura la sesión HTTP persistente y los mecanismos de sincronización.
        """
        # Sesión HTTP: Estrategia Keep-Alive
        # Usar requests.Session permite reutilizar la conexión TCP subyacente
        # para múltiples peticiones (método Keep-Alive), lo que reduce la latencia
        # de establecimiento de conexión en cada una de las peticiones concurrentes.
        self.session = requests.Session()
        self.session.headers.update(constants.HEADERS)
        
        # Sincronización: Mutex (Lock) para la Sección Crítica
        # Este candado evita 'race conditions' (condiciones de carrera) al escribir
        # en el fichero CSV, asegurando que solo un hilo acceda a la operación I/O
        # a la vez.
        self.csv_lock = threading.Lock()

        # Inicialización del fichero de persistencia con las cabeceras
        self._initialize_storage()

    def _initialize_storage(self):
        """Crea y prepara el fichero CSV de salida escribiendo la línea de cabecera."""
        try:
            # Uso de encoding='utf-8' para manejar correctamente caracteres especiales.
            with open(constants.CSV_OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvFile:
                writer = csv.writer(csvFile)
                writer.writerow(constants.CSV_HEADER)
            print(f"[*] Fichero CSV '{constants.CSV_OUTPUT_FILE}' inicializado con éxito.")
        except IOError as e:
            print(f"[FATAL] Error crítico inicializando almacenamiento: {e}")
            sys.exit(1)

    def execute(self):
        """
        Método maestro que orquesta el proceso completo de minería de datos.
        """
        # Validación de política de acceso
        if not self._accessGranted():
            print("[ACCESO DENEGADO] El fichero robots.txt impide la ejecución.")
            sys.exit(1)
            
        # Extracción del catálogo de IDs (etapa secuencial)
        print(">>> Iniciando secuencia de mapeo de IDs de alimentos...")
        food_ids = self._get_catalog_ids()
        total_foods = len(food_ids)
        print(f">>> Catálogo indexado: {total_foods} referencias encontradas.")
        print(f">>> Desplegando enjambre de {constants.MAX_WORKERS} workers para extracción paralela.")

        # Orquestación de Concurrencia (Thread Pool)
        # ThreadPoolExecutor maneja el pool de hilos y su ciclo de vida.
        with ThreadPoolExecutor(max_workers=constants.MAX_WORKERS) as executor:
            # Mapeamos cada ID a una tarea asíncrona (_mine_food_data)
            future_to_food = {executor.submit(self._mine_food_data, f_id): f_id for f_id in food_ids}
            
            completed_count = 0
            # as_completed devuelve los resultados a medida que los hilos terminan.
            for future in as_completed(future_to_food):
                food_id = future_to_food[future]
                try:
                    data_row = future.result()
                    if data_row:
                        # Escritura atómica: uso del Lock para garantizar integridad del CSV
                        with self.csv_lock:
                            self._persist_data(data_row)
                    
                    completed_count += 1
                    # Log de progreso
                    if completed_count % 25 == 0 or completed_count == total_foods:
                        self._print_progress(completed_count, total_foods)

                except Exception as exc:
                    print(f"\n[ERROR WORKER] Fallo en nodo {food_id}: {exc}")

    def _accessGranted(self):
        """Verifica la directiva de 'Allow' en el fichero robots.txt para el USER_AGENT definido."""
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(constants.ROBOTS_URL)
        try:
            rp.read()
            return rp.can_fetch(constants.USER_AGENT, constants.URL)
        except Exception:
            # Si la lectura falla (ej. error de red), asumimos permiso por defecto.
            return True

    def _get_catalog_ids(self):
        """Realiza la petición inicial para obtener todos los identificadores de alimentos."""
        try:
            r = self.session.post(constants.URL, data=constants.IDS_REQUEST)
            r.raise_for_status() # Lanza una excepción para códigos de error HTTP
            soup = BeautifulSoup(r.text, "lxml-xml")
            # Uso de list comprehension para recolección eficiente
            return [node.get_text() for node in soup.find_all('f_id')]
        except Exception as e:
            print(f"[ERROR RED] Fallo obteniendo catálogo maestro. Revise el endpoint: {e}")
            sys.exit(1)

    def _mine_food_data(self, food_id):
        """
        [WORKER METHOD]
        Función ejecutada por cada hilo para extraer y estructurar los detalles
        nutricionales de un único alimento (ID).
        """
        try:
            food_data_map = {}
            # Construcción del payload XML específico
            payload = constants.DETAILS_REQUEST_INI + str(food_id) + constants.DETAILS_REQUEST_FIN
            
            # Aplicación del Throttling (latencia fija)
            time.sleep(constants.FIXED_DELAY)
            
            # Petición a la API usando la sesión persistente
            response = self.session.post(constants.URL, data=payload)
            
            if response.status_code != 200:
                print(f"\n[WARN] Error HTTP {response.status_code} para ID {food_id}. Saltando registro.")
                return None

            soup = BeautifulSoup(response.content, "lxml-xml")
            
            # 1. Extracción de Metadatos Básicos (Ej: f_id, f_ori_name, sci_name, eur_name)
            # El bucle itera sobre la lista BASIC_LIST actualizada en constants.py.
            for tag in constants.BASIC_LIST:
                node = soup.find(tag)
                # Uso de operador ternario para manejo conciso de nulos
                food_data_map[tag] = node.getText() if node else constants.EMPTY
            
            # 2. Extracción de Componentes Nutricionales
            components = soup.find_all('foodvalue')
            for comp in components:
                name_node = comp.find("c_ori_name")
                key_name = name_node.getText() if name_node else "Unknown"
                
                val_node = comp.find("best_location")
                value = val_node.getText() if val_node else ""
                
                # Lógica de fallback: si el valor numérico ('best_location') es nulo,
                # se usa el tipo de valor ('value_type') como marcador.
                if not value:
                    type_node = comp.find("value_type")
                    food_data_map[key_name] = type_node.getText() if type_node else constants.EMPTY
                else:
                    food_data_map[key_name] = value
            
            # Normalización del diccionario a formato de lista (fila CSV)
            return self._normalize_for_csv(food_data_map)

        except AttributeError as e:
            # Captura específica para errores de parsing XML (ej. tag no encontrado)
            print(f"\n[ERROR PARSING] ID {food_id}: Error de atributo. Datos incompletos.")
            return None
        except Exception as e:
            # Captura para errores inesperados (ej. problemas de red temporales)
            print(f"\n[EXCEPCIÓN WORKER] ID {food_id}: {e}")
            return None

    def _normalize_for_csv(self, data_map): 
        """Convierte el diccionario de datos a una lista, asegurando el orden correcto (CSV_HEADER)."""
        # Si una columna esperada no está en el mapa, se rellena con el marcador EMPTY.
        return [data_map.get(col, constants.EMPTY) for col in constants.CSV_HEADER]

    def _persist_data(self, row):
        """Escribe una fila al disco. Debe ser invocado bajo el control de self.csv_lock."""
        try:
            # Abrir en modo 'a' (append) para añadir la fila
            with open(constants.CSV_OUTPUT_FILE, 'a', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow(row)
        except Exception as e:
            print(f"[ERROR I/O] Fallo crítico escribiendo disco: {e}. Abortando.")
            # Un error de escritura crítica debería detener la ejecución
            sys.exit(1)

    def _print_progress(self, current, total):
        """Visualización de progreso en consola mediante una barra de carga."""
        percent = (current / total) * 100
        # Barra ASCII simple para feedback visual
        bar_length = 50
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        print(f"\rProgreso: |{bar}| {percent:.1f}% ({current}/{total})", end='', flush=True)