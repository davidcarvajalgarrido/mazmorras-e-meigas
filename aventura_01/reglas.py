"""Reglas de validación compartidas por el proceso final."""
from datetime import datetime

CAMPOS = ['id', 'fecha', 'localidad', 'fenomeno', 'nivel_riesgo', 'descripcion']
FENOMENOS = ['trasno', 'meiga', 'aparicion', 'santa_compana']


def validar(fila, fenomenos):
    # DictReader usa None cuando faltan o sobran columnas en una fila.
    if None in fila or any(fila.get(campo) is None for campo in CAMPOS):
        raise ValueError('La fila tiene un número de columnas incorrecto')
    limpia = {campo: fila[campo].strip() for campo in CAMPOS}
    for campo, valor in limpia.items():
        if not valor:
            raise ValueError(f'Campo obligatorio vacío: {campo}')
    fecha = datetime.strptime(limpia['fecha'], '%Y-%m-%d').date()
    if fecha.isoformat() != limpia['fecha']:
        raise ValueError('La fecha debe usar el formato AAAA-MM-DD')
    riesgo = int(limpia['nivel_riesgo'])
    if not 1 <= riesgo <= 5:
        raise ValueError('El riesgo debe estar entre 1 y 5')
    if limpia['fenomeno'] not in fenomenos:
        raise ValueError('Fenómeno fuera del catálogo')
    limpia['nivel_riesgo'] = riesgo
    return limpia

