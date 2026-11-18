"""Segunda misión: leer los CSV como diccionarios."""
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
total = 0
for archivo in sorted((BASE / 'entrada').glob('*.csv')):
    with archivo.open(encoding='utf-8-sig', newline='') as fichero:
        lector = csv.DictReader(fichero)
        for fila in lector:
            total += 1
            print(fila['id'], fila['localidad'], repr(fila['nivel_riesgo']))
print('Partes leídos:', total)
print('CSV devuelve texto: todavía no hemos convertido ni validado el riesgo.')
