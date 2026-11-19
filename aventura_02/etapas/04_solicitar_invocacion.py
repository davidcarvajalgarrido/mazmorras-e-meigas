"""POST y consulta posterior, con meteorología sintética. Servidor --demo."""
import sys
from pathlib import Path
import requests
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cliente import obtener_json, extraer_franjas, elegir_ritual, autenticar, CLAVE_DEMO

base = 'http://127.0.0.1:8765'
datos = obtener_json(base + '/meteo/prediccion', params={'idConc': 15078})
ritual = elegir_ritual(extraer_franjas(datos))
token = autenticar(base, CLAVE_DEMO)
cabeceras = {'Authorization': 'Bearer ' + token}
respuesta = requests.post(base + '/invocaciones', json=ritual,
                          headers=cabeceras, timeout=(3.05, 8))
respuesta.raise_for_status()
print('HTTP:', respuesta.status_code)
print('Location:', respuesta.headers.get('Location'))
creada = respuesta.json()
consulta = requests.get(base + '/invocaciones/' + creada['id'],
                        headers=cabeceras, timeout=(3.05, 8))
consulta.raise_for_status()
print(consulta.json())
