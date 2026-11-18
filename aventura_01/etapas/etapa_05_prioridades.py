"""Quinta misión: encadenar configuración, lectura, validación y prioridad.

Reutiliza el proceso final sin generar todavía sus archivos de salida.
Los avisos WARNING son registros rechazados, no fallos de ejecución.
"""
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from procesar import cargar_configuracion, procesar


def main():
    config, entrada, salida = cargar_configuracion(BASE / 'config.json')
    archivos = sorted(p for p in entrada.glob('*.csv') if p.is_file())
    validos, rechazados, errores = procesar(archivos, config)
    prioritarios = [p for p in validos
                   if p['nivel_riesgo'] >= config['riesgo_prioritario']]
    print(f'Válidos: {len(validos)}; rechazados: {len(rechazados)}')
    print(f'Prioritarios: {len(prioritarios)}; archivos omitidos: {len(errores)}')
    for parte in sorted(prioritarios, key=lambda p: (-p['nivel_riesgo'], p['id'])):
        print(parte['id'], parte['localidad'], parte['nivel_riesgo'])


if __name__ == '__main__':
    main()
