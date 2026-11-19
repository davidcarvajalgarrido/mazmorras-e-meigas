"""Consulta autenticada a MeteoSIX; requiere METEOSIX_API_KEY en aventura_02/.env."""
import argparse
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cliente import (
    METEOSIX_URL,
    SANTIAGO_LATITUD,
    SANTIAGO_LONGITUD,
    consultar_meteosix,
    extraer_franjas_meteosix,
    elegir_ritual,
)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--ubicacion', default='Santiago de Compostela')
parser.add_argument('--lon', type=float, default=SANTIAGO_LONGITUD)
parser.add_argument('--lat', type=float, default=SANTIAGO_LATITUD)
args = parser.parse_args()
clave = os.getenv('METEOSIX_API_KEY')
if not clave:
    raise SystemExit('Define METEOSIX_API_KEY en aventura_02/.env o en el entorno')

print('GET', METEOSIX_URL)
print('Autenticación: parámetro API_KEY (valor oculto)')
try:
    datos = consultar_meteosix(clave, args.lon, args.lat)
    franjas = extraer_franjas_meteosix(
        datos, args.ubicacion, args.lon, args.lat
    )
except requests.HTTPError as error:
    raise SystemExit(f'Error HTTP {error.response.status_code}') from None
except (requests.RequestException, ValueError):
    raise SystemExit('No se pudo consultar o validar la respuesta de MeteoSIX') from None

for franja in franjas[:5]:
    print(f"{franja['fecha']} {franja['hora']} · "
          f"{franja['precipitacion_lm2']} lm2 en la hora anterior")
print('Criterio MeteoSIX: precipitation_amount > 0 lm2')
print('Ritual elegido:', elegir_ritual(franjas))
