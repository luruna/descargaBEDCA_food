# -----------------------------------------------------------------------------
# GASTRO-MINER CONFIGURATION KERNEL
# -----------------------------------------------------------------------------
# Este módulo define los parámetros estáticos, los endpoints de red y
# el esquema de datos objetivo para el motor de extracción.
# -----------------------------------------------------------------------------

# --- Compatibilidad: permitir importar desde ./src/ si existe (legacy layout) ---
import os
import sys
here = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(here, 'src')
if os.path.isdir(src_dir) and src_dir not in sys.path:
	sys.path.insert(0, src_dir)

# -----------------------------------------------------------------------------
# --- ESQUEMA DE DATOS (DATA SCHEMA) ---

# Identificadores primarios del recurso, usados para la llave primaria del CSV.
# ¡ACTUALIZACIÓN CRÍTICA! Se ha confirmado que 'f_eng_name' es la etiqueta 
# (tag) correcta para obtener el nombre en inglés, según la inspección del 
# código fuente de la web.
BASIC_LIST = ('f_id', 'f_ori_name', 'f_eng_name', 'sci_name', 'edible_portion')

# Vector de atributos nutricionales extendidos (Target Features)
DETAIL_LIST = (
    'alcohol (etanol)', 'energía, total', 'grasa, total (lipidos totales)',
    'proteina, total', 'agua (humedad)', 'carbohidratos', 'fibra, dietetica total',
    'ácido graso 22:6 n-3 (ácido docosahexaenóico)', 'ácido graso 20:5 (ácido eicosapentaenóico)',
    'ácido graso 12:0 (láurico)', 'ácido graso 14:0 (ácido mirístico)',
    'ácido graso 16:0 (ácido palmítico)', 'ácido graso 18:0 (ácido esteárico)',
    'ácido graso 18:1 n-9 cis (ácido oléico)', 'ácido graso 18:2',
    'ácido graso 18:3', 'ácido graso 20:4 n-6  (ácido araquidónico)',
    'ácidos grasos, monoinsaturados totales',
    'ácidos grasos, poliinsaturados totales',
    'ácidos grasos saturados totales','ácidos grasos, trans totales',
    'colesterol',
    'Vitamina A equivalentes de retinol de actividades de retinos y carotenoides',
    'Vitamina D',
    'Viamina E equivalentes de alfa tocoferol de actividades de vitámeros E',
    'folato, total', 'equivalentes de niacina, totales', 'riboflavina',
    'tiamina', 'Vitamina B-12', 'Vitamina B-6, Total',
    'Vitamina C (ácido ascórbico)', 'calcio', 'hierro, total', 'potasio',
    'magnesio', 'sodio', 'fósforo', 'ioduro', 'selenio, total', 'zinc (cinc)'
)

# --- PERSISTENCIA (IO SETTINGS) ---
CSV_OUTPUT_FILE = "nutritional-info.csv"
# El encabezado se actualiza automáticamente al modificar BASIC_LIST
CSV_HEADER = BASIC_LIST + DETAIL_LIST 
EMPTY = 'NA'  # Marcador para valores nulos o no disponibles

# --- CONECTIVIDAD (NETWORK ENDPOINTS) ---
HOME_URL = "http://www.bedca.net"
URL = HOME_URL + "/bdpub/procquery.php"
ROBOTS_URL = HOME_URL + "/robots.txt"

# Identidad del Agente: Es buena práctica identificarse claramente ante el servidor
USER_AGENT = 'GastroMiner-Bot/2.2 (Educational Research)'
HEADERS = {'Content-Type': 'text/xml', 'User-Agent': USER_AGENT}

# --- TUNING DE RENDIMIENTO (CONCURRENCY & THROTTLING) ---

# Número de hilos de ejecución paralela.
MAX_WORKERS = 10 

# Latencia inyectada entre peticiones (Throttling) en segundos.
FIXED_DELAY = 0.1 

# --- PAYLOADS XML (PROTOCOL BUFFERS) ---

# Query Nivel 1: Descubrimiento de IDs
IDS_REQUEST = """<foodquery>
	<type level="1"/>
	<selection>
		<atribute name="f_id"/>
	</selection>
	<condition>
		<cond1>
			<atribute1 name="f_origen"/>
		</cond1>
		<relation type="EQUAL"/>
		<cond3>BEDCA</cond3>
	</condition>
	<order ordtype="ASC">
		<atribute3 name="f_id"/>
	</order>
</foodquery>"""

# Query Nivel 2: Extracción Profunda (Prefijo)
DETAILS_REQUEST_INI = """<foodquery>
	<type level="2"/>
	<selection>
		<atribute name="f_id"/>
		<atribute name="f_ori_name"/>
        <atribute name="f_eng_name"/> <!-- Etiqueta confirmada para el nombre en inglés -->
		<atribute name="sci_name"/>
		<atribute name="edible_portion"/>
		<atribute name="f_origen"/>
		<atribute name="c_id"/>
		<atribute name="c_ori_name"/>
		<atribute name="componentgroup_id"/>
		<atribute name="best_location"/>
		<atribute name="v_unit"/>
		<atribute name="u_id"/>
		<atribute name="u_descripcion"/>
		<atribute name="value_type"/>
		<atribute name="vt_descripcion"/>
		<atribute name="mu_id"/>
		<atribute name="mu_descripcion"/>
	</selection>
	<condition>
		<cond1>
			<atribute1 name="f_id"/>
		</cond1>
		<relation type="EQUAL"/>
		<cond3>"""

# Query Nivel 2: Extracción Profunda (Sufijo)
DETAILS_REQUEST_FIN = """</cond3>
	</condition>
	<condition>
		<cond1>
			<atribute1 name="publico"/>
		</cond1>
		<relation type="EQUAL"/>
		<cond3>1</cond3>
	</condition>
	<order ordtype="ASC">
		<atribute3 name="componentgroup_id"/>
	</order>
</foodquery>"""