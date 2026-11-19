"""Primera petición: ejecutar --offline para usar el oráculo local."""
import argparse
import requests

parser = argparse.ArgumentParser()
parser.add_argument('--offline', action='store_true')
args = parser.parse_args()
url = ('http://127.0.0.1:8765/meteo/prediccion' if args.offline else
       'https://servizos.meteogalicia.gal/mgrss/predicion/jsonPredConcellos.action')
respuesta = requests.get(url, params={'idConc': 15078},
                         headers={'Accept': 'application/json'}, timeout=(3.05, 8))
print('URL:', respuesta.url)
print('HTTP:', respuesta.status_code)
print('Tipo:', respuesta.headers.get('Content-Type'))
respuesta.raise_for_status()
print(respuesta.text)
