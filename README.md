# GastroMiner (NutriScraper)

Extracción concurrente de datos nutricionales desde la base de datos BEDCA. Este repositorio contiene el motor principal de extracción, configuración y un script auxiliar para descubrir etiquetas XML de nombre en inglés.

**Contenido principal**
- `main.py` — lanzador principal que inicializa y ejecuta `GastroMiner`.
- `GastroMiner.py` — motor de extracción y clase principal `GastroMiner`.
- `descubridosnombres.py` — script auxiliar para probar etiquetas XML de nombres.
- `constants.py` — configuración, payloads XML y parámetros (p. ej. `constants.IDS_REQUEST`).
- `requirements.txt` — dependencias Python necesarias.

**Requisitos**
- Python 3.8 o superior (recomendado).
- Entorno virtual (recomendado para aislar dependencias).

**Instalación (entorno virtual)**

Windows (PowerShell):
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux / macOS:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Uso**

- Ejecutar el motor principal:
```
python main.py
```

- Ejecutar el script de descubrimiento de nombres (pruebas):
```
python descubridosnombres.py
```

El motor crea el fichero de salida `nutritional-info.csv` (nombre definido en `constants.py`).

**Configuración y ajustes**
- Ajusta la concurrencia y el throttling en `constants.py` (`MAX_WORKERS`, `FIXED_DELAY`).
- Cambia el `USER_AGENT` en `constants.py` si vas a ejecutar a gran escala y quieres identificarte de forma distinta.
- El motor verifica `constants.ROBOTS_URL` antes de ejecutar para respetar la política de `robots.txt`.

**Notas de desarrollo**
- Se añadió un bloque de compatibilidad en los módulos para permitir que el proyecto funcione si el código se ubicaba previamente bajo una carpeta `src/` (inserta `./src` en `sys.path` si existe).
- El parsing XML usa `BeautifulSoup` con el parser `lxml-xml`.

**Problemas comunes**
- Si recibes errores de importación, asegúrate de estar ejecutando desde la raíz del proyecto donde se encuentran los scripts o activa el entorno virtual.
- Si la red falla al obtener `robots.txt` o los endpoints, revisa conectividad y proxies.

**Licencia y uso**
Uso y distribución para fines educativos y de investigación. Ajusta el comportamiento del bot y la identificación (`USER_AGENT`) según el uso que vayas a dar.
