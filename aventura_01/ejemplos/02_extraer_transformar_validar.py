"""Un registro antes y después: leer, transformar y validar son pasos distintos."""
import csv
from io import StringIO


def main():
    texto = 'id,nivel_riesgo\n  MEI-007  ,  5  \n'
    # Extracción: seleccionamos campos de la fila leída del CSV.
    fila = next(csv.DictReader(StringIO(texto)))
    print('EXTRAÍDO:', repr(fila['id']), repr(fila['nivel_riesgo']))
    print('Tipo original:', type(fila['nivel_riesgo']).__name__)

    # Transformación: limpiamos espacios y convertimos texto en entero.
    parte = {'id': fila['id'].strip(), 'nivel_riesgo': int(fila['nivel_riesgo'].strip())}
    print('TRANSFORMADO:', repr(parte['id']), parte['nivel_riesgo'])
    print('Tipo nuevo:', type(parte['nivel_riesgo']).__name__)

    # Validación: convertir a entero no garantiza un valor permitido.
    for valor in ['5', '9', 'muchísimo']:
        try:
            riesgo = int(valor)
            if not 1 <= riesgo <= 5:
                raise ValueError('Fuera del intervalo 1–5')
            print(repr(valor), 'ACEPTADO')
        except ValueError as error:
            print(repr(valor), 'PARA REVISIÓN:', error)


if __name__ == '__main__':
    main()
