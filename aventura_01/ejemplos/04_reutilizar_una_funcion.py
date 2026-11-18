"""Importar la misma regla usada por el proceso final para otro origen de datos."""
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from reglas import validar, FENOMENOS


def main():
    # Este registro no procede de un CSV: podría llegar de un formulario.
    recibido = {'id': 'MEI-EXTRA', 'fecha': '2026-11-18',
                'localidad': '  Betanzos  ', 'fenomeno': 'trasno',
                'nivel_riesgo': ' 4 ', 'descripcion': 'El registro cambia de sitio.'}
    print('Antes:', recibido)
    limpio = validar(recibido, FENOMENOS)
    print('Después:', limpio)
    print('La regla se importa; no se copia ni se vuelve a escribir.')


if __name__ == '__main__':
    main()
