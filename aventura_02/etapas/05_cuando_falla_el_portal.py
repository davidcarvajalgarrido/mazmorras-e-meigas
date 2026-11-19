"""Errores reproducibles: requiere servidor --demo. No toca MeteoGalicia."""
import sys
import uuid
from pathlib import Path
import requests
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cliente import obtener_json, extraer_franjas, autenticar, CLAVE_DEMO

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--base', default='http://127.0.0.1:8765')
base = parser.parse_args().base.rstrip('/')
for titulo, respuesta in [
    ('Credencial incorrecta', requests.post(base + '/sesiones', headers={'X-API-Key': 'incorrecta'}, timeout=3)),
    ('Recurso inexistente', requests.get(base + '/no-existe', timeout=3))
]:
    print(titulo, '->', respuesta.status_code, respuesta.json())
token = autenticar(base, CLAVE_DEMO)
r = requests.post(base + '/invocaciones', json={'criatura': 'patata_cosmica'},
                  headers={'Authorization': 'Bearer ' + token}, timeout=3)
print('Ritual inválido ->', r.status_code, r.json())
try:
    obtener_json(base + '/laboratorio/json-roto', intentos=1)
except requests.exceptions.JSONDecodeError:
    print('HTTP 200, pero el cuerpo no es JSON válido')
try:
    extraer_franjas(obtener_json(base + '/laboratorio/datos-incompletos'))
except ValueError as error:
    print(error)
try:
    obtener_json(base + '/laboratorio/lento', intentos=1, timeout=0.05)
except requests.Timeout:
    print('Timeout: no llegó respuesta dentro del plazo')
resultado = obtener_json(base + '/laboratorio/inestable',
                         headers={'X-Ensayo': str(uuid.uuid4())})
print('Dos HTTP 503 y recuperación en el tercer intento ->', resultado)
