# -----------------------------------------------------------------------------
# DISCOVERER DE NOMBRES DE ALIMENTOS (NAME DISCOVERER)
# -----------------------------------------------------------------------------
# Script independiente y minimalista para probar qué etiqueta (tag) XML de la
# API de BEDCA devuelve el nombre del alimento en inglés.
# Solo procesa las primeras 10 referencias para una respuesta rápida.
# -----------------------------------------------------------------------------

import os
import sys
# Compatibilidad con layout antiguo: permitir importar desde ./src/ si existe
here = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(here, 'src')
if os.path.isdir(src_dir) and src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from bs4 import BeautifulSoup
import requests
import time

# --- CONSTANTES REQUERIDAS ---
URL = "http://www.bedca.net/bdpub/procquery.php"
USER_AGENT = 'NameDiscoverer-Bot/1.0 (Testing Name Fields)'
HEADERS = {'Content-Type': 'text/xml', 'User-Agent': USER_AGENT}
LIMIT = 10  # Número de alimentos a probar
START_INDEX = 100 # Nuevo: Índice de inicio para omitir los primeros registros vacíos que suelen estar incompletos.
EMPTY = 'NA'  # Marcador para campos no encontrados en el XML

# Lista de tags a probar. 'f_ori_name' y 'sci_name' se incluyen como referencia.
NAME_FIELDS_TO_TEST = [
    'f_ori_name',    # Nombre en español (Referencia)
    'sci_name',      # Nombre científico (Referencia)
    'eur_name',      # Ya sabemos que este es propenso a errores
    'f_eng_name',    # Hipótesis 1 (f_ + eng_name)
    'english_name',  # Hipótesis 2 (Nombre directo)
    'f_name_en',     # Hipótesis 3 (f_name + en)
    'f_description_en' # Hipótesis 4 (Descripción en inglés)
]

# Query Nivel 1: Descubrimiento de IDs (Idéntica a la usada en constants.py)
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


def get_catalog_ids(session):
    """Realiza la petición inicial para obtener todos los identificadores de alimentos."""
    print(">>> 1. Obteniendo IDs de alimentos...")
    try:
        r = session.post(URL, data=IDS_REQUEST)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml-xml")
        ids = [node.get_text() for node in soup.find_all('f_id')]
        return ids
    except Exception as e:
        print(f"[ERROR] Fallo obteniendo catálogo maestro: {e}")
        return []

def build_details_payload(food_id):
    """Construye el payload XML de detalle, incluyendo solo los campos que queremos probar."""
    # Construir la sección <selection> dinámicamente
    selection_xml = "\n".join([f'<atribute name="{tag}"/>' for tag in NAME_FIELDS_TO_TEST])
    
    # Construir el payload completo de Nivel 2, minimalista.
    payload = f"""<foodquery>
	<type level="2"/>
	<selection>
        {selection_xml}
	</selection>
	<condition>
		<cond1>
			<atribute1 name="f_id"/>
		</cond1>
		<relation type="EQUAL"/>
		<cond3>{food_id}</cond3>
	</condition>
	<condition>
		<cond1>
			<atribute1 name="publico"/>
		</cond1>
		<relation type="EQUAL"/>
		<cond3>1</cond3>
	</condition>
</foodquery>"""
    return payload

def test_name_fields(session, food_id):
    """Envía la consulta para un solo ID y extrae los campos de nombre a prueba."""
    payload = build_details_payload(food_id)
    time.sleep(0.1) # Breve delay para no saturar
    
    try:
        response = session.post(URL, data=payload)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "lxml-xml")
        results = {}
        
        # Extraer el valor para cada tag que estamos probando
        for tag in NAME_FIELDS_TO_TEST:
            node = soup.find(tag)
            # Guardamos el texto o nuestro marcador EMPTY si no se encuentra el nodo
            results[tag] = node.getText().strip() if node else EMPTY
            
        return results

    except Exception as e:
        print(f"\n[ERROR] Fallo en ID {food_id}: {e}")
        return None

def display_results(all_results):
    """Imprime los resultados de las pruebas en un formato tabular."""
    print("\n" + "="*80)
    print(f"| PRUEBA DE CAMPO DE NOMBRE EN INGLÉS (Resultados de {len(all_results)} alimentos) |")
    print("="*80)

    # Imprimir cabecera de la tabla
    header = "ID" + "".join([f"| {tag:<{max(len(tag), 15)}}" for tag in NAME_FIELDS_TO_TEST])
    print(header)
    print("-" * 80)
    
    # Imprimir filas de datos
    for food_id, data in all_results.items():
        row = f"{food_id:<3}"
        for tag in NAME_FIELDS_TO_TEST:
            value = data.get(tag, 'NA')
            # Truncar valores largos para mantener la tabla legible
            display_value = value[:15].ljust(15) if len(value) > 15 else value.ljust(15)
            row += f"| {display_value}"
        print(row)
    
    print("="*80)
    print("\nInstrucción: El campo correcto es aquel que devuelve consistentemente el nombre en inglés y no 'NA' o datos corruptos.")


# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    session = requests.Session()
    session.headers.update(HEADERS)
    
    food_ids = get_catalog_ids(session)
    
    if not food_ids:
        sys.exit(1)
        
    # Limitar la prueba
    # Usamos START_INDEX para saltarnos los primeros 100 IDs que parecen estar vacíos.
    test_ids = food_ids[START_INDEX:START_INDEX + LIMIT]
    print(f">>> 2. Probando campos en IDs a partir del índice {START_INDEX} ({len(test_ids)} alimentos)...")
    
    results = {}
    for i, f_id in enumerate(test_ids):
        print(f"\r  -> Consultando ID {f_id} ({i+1}/{len(test_ids)})...", end='', flush=True)
        data = test_name_fields(session, f_id)
        if data:
            results[f_id] = data

    display_results(results)
    
    print("\nProceso de descubrimiento finalizado.")