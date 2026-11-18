"""Tercera misión: reglas explícitas y una función reutilizable."""
import csv
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from reglas import validar, FENOMENOS


def main():
    validos, rechazados = 0, 0
    for archivo in sorted((BASE / 'entrada').glob('*.csv')):
        with archivo.open(encoding='utf-8-sig', newline='') as fichero:
            for numero, fila in enumerate(csv.DictReader(fichero), start=2):
                try:
                    parte = validar(fila, FENOMENOS)
                    validos += 1
                    print('VÁLIDO', parte['id'])
                except ValueError as error:
                    rechazados += 1
                    print('REVISAR', archivo.name, numero, str(error))
    print(f'Válidos: {validos}; rechazados: {rechazados}')
    print('En esta etapa aún no detectamos identificadores repetidos.')


if __name__ == '__main__':
    main()
