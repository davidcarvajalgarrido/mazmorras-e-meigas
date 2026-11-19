"""De JSON a diccionarios/listas; usar --offline para ensayar."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cliente import METEO_URL, obtener_json, extraer_franjas, elegir_ritual

parser = argparse.ArgumentParser()
parser.add_argument('--offline', action='store_true')
args = parser.parse_args()
url = 'http://127.0.0.1:8765/meteo/prediccion' if args.offline else METEO_URL
datos = obtener_json(url, params={'idConc': 15078})
print('Tipos Python:', type(datos).__name__, type(datos['predConcello']['listaPredDiaConcello']).__name__)
for franja in extraer_franjas(datos):
    print(franja['fecha'], franja['franja'], franja['probabilidad_lluvia'])
print('Ritual elegido:', elegir_ritual(extraer_franjas(datos)))
