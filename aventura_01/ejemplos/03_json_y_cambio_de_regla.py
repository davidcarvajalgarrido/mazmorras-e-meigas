"""Leer JSON y reutilizar datos válidos con dos reglas, sin editar el original."""
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from procesar import cargar_configuracion, procesar


def main():
    config, entrada, salida = cargar_configuracion(BASE / 'config.json')
    archivos = sorted(p for p in entrada.glob('*.csv') if p.is_file())
    validos, rechazados, errores = procesar(archivos, config)
    comparacion = {}
    for umbral in [4, 5]:
        seleccion = [p['id'] for p in validos if p['nivel_riesgo'] >= umbral]
        comparacion[str(umbral)] = seleccion
        print(f'Umbral {umbral}: {len(seleccion)} prioridades: {seleccion}')
    # JSON también puede ser una salida que lea otro programa.
    destino = BASE / 'salida_ejemplos'
    destino.mkdir(parents=True, exist_ok=True)
    ruta = destino / 'comparacion_umbrales.json'
    ruta.write_text(json.dumps(comparacion, ensure_ascii=False, indent=2) + '\n',
                    encoding='utf-8')
    print('JSON generado:', ruta)
    print('La validez de los registros no cambia al cambiar el umbral.')


if __name__ == '__main__':
    main()
