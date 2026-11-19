"""Obtener un token sin mostrarlo ni guardarlo. Servidor --demo."""
import os
import requests

# --demo es una decisión explícita para usar la clave pública de este ejemplo.
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--demo', action='store_true')
args = parser.parse_args()
clave = ('clave-publica-solo-para-la-demo' if args.demo else os.environ['CONJURO_API_KEY'])
respuesta = requests.post('http://127.0.0.1:8765/sesiones',
                          headers={'X-API-Key': clave}, timeout=(3.05, 8))
respuesta.raise_for_status()
datos = respuesta.json()
token = datos['access_token']
print('HTTP:', respuesta.status_code)
print('Tipo:', datos['token_type'], '| Vigencia:', datos['expires_in'], 'segundos')
print('Token recibido; no se imprime. En este ejemplo no es un JWT ni un flujo OAuth.')
