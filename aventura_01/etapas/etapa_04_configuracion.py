"""Cuarta misión: separar opciones del código."""
import csv
import json
from pathlib import Path

from etapa_03_validacion import validar
BASE = Path(__file__).resolve().parents[1]

def main():
    with (BASE / 'config.json').open(encoding='utf-8') as fichero:
        config = json.load(fichero)
    print('Umbral de prioridad:', config['riesgo_prioritario'])
    for archivo in sorted((BASE / config['entrada']).glob('*.csv')):
        with archivo.open(encoding='utf-8-sig', newline='') as fichero:
            for fila in csv.DictReader(fichero):
                try:
                    parte = validar(fila, config['fenomenos'])
                except ValueError:
                    continue  # Las explicaciones se vieron en la etapa 03.
                if parte['nivel_riesgo'] >= config['riesgo_prioritario']:
                    print('PRIORITARIO', parte['id'], parte['localidad'])

if __name__ == '__main__':
    main()
