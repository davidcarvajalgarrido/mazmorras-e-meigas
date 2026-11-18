"""Expediente Meiga. Biblioteca estándar. Python 3.10 o posterior.

Uso: python procesar.py [--config RUTA]
Salidas regeneradas en cada ejecución. El log conserva el historial.
Código 0: lote completo (puede contener filas rechazadas).
Código 1: fallo global. Código 2: resultado parcial por archivos defectuosos.
"""
import argparse
import csv
import json
import logging
import sys
from collections import Counter
from pathlib import Path

from reglas import CAMPOS, validar

BASE = Path(__file__).resolve().parent
LOG = logging.getLogger('expediente_meiga')


def cargar_configuracion(ruta):
    with ruta.open(encoding='utf-8') as fichero:
        config = json.load(fichero)
    if not isinstance(config, dict):
        raise ValueError('La configuración debe ser un objeto JSON')
    for clave in ['entrada', 'salida']:
        if not isinstance(config.get(clave), str) or not config[clave].strip():
            raise ValueError(f'Configuración inválida: {clave}')
    umbral = config.get('riesgo_prioritario')
    if type(umbral) is not int or not 1 <= umbral <= 5:
        raise ValueError('riesgo_prioritario debe ser un entero entre 1 y 5')
    catalogo = config.get('fenomenos')
    if (not isinstance(catalogo, list) or not catalogo or
            not all(isinstance(x, str) and x.strip() for x in catalogo)):
        raise ValueError('fenomenos debe ser una lista de nombres')
    # Las rutas del JSON son relativas a su propio archivo.
    entrada = (ruta.parent / config['entrada']).resolve()
    salida = (ruta.parent / config['salida']).resolve()
    if (entrada == salida or entrada in salida.parents or
            salida in entrada.parents):
        raise ValueError('Entrada y salida deben ser carpetas separadas')
    if not entrada.is_dir():
        raise ValueError(f'No existe la carpeta de entrada: {entrada}')
    return config, entrada, salida


def leer_archivo(archivo):
    # Leemos el archivo completo antes de aceptarlo. Un fallo estructural
    # descarta todo ese archivo, evitando incorporar una parte de sus filas.
    with archivo.open(encoding='utf-8-sig', newline='') as fichero:
        lector = csv.DictReader(fichero, strict=True)
        if lector.fieldnames != CAMPOS:
            raise ValueError('Cabecera incorrecta: se esperan ' + ','.join(CAMPOS))
        return list(lector)


def escribir_csv(destino, campos, filas):
    # Reemplazo por archivo: no añadimos filas a salidas de otra ejecución.
    temporal = destino.with_suffix('.tmp')
    with temporal.open('w', encoding='utf-8-sig', newline='') as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(filas)
    temporal.replace(destino)


def procesar(archivos, config):
    validos, rechazados, errores_archivo = [], [], []
    vistos = set()
    for archivo in archivos:
        try:
            filas = leer_archivo(archivo)
        except (OSError, UnicodeError, csv.Error, ValueError) as error:
            errores_archivo.append({'archivo': archivo.name, 'motivo': str(error)})
            LOG.error('Archivo omitido: %s. %s', archivo.name, error)
            continue
        LOG.info('Leyendo %s: %s registros', archivo.name, len(filas))
        for numero, fila in enumerate(filas, start=2):
            try:
                parte = validar(fila, config['fenomenos'])
                if parte['id'] in vistos:
                    raise ValueError('Identificador repetido en el lote')
                vistos.add(parte['id'])
                validos.append(parte)
            except ValueError as error:
                rechazados.append({'archivo': archivo.name, 'registro': numero,
                                   'id': fila.get('id', ''), 'motivo': str(error)})
                LOG.warning('%s, registro %s: %s', archivo.name, numero, error)
    # El número es el ordinal del registro contando la cabecera, no una
    # línea física: un campo CSV entrecomillado puede contener saltos.
    return validos, rechazados, errores_archivo


def guardar_resultados(salida, config, validos, rechazados, errores, encontrados):
    prioridades = sorted(
        [p for p in validos if p['nivel_riesgo'] >= config['riesgo_prioritario']],
        key=lambda p: (-p['nivel_riesgo'], p['id']))
    escribir_csv(salida / 'incidencias_validadas.csv', CAMPOS, validos)
    escribir_csv(salida / 'avisos_prioritarios.csv', CAMPOS, prioridades)
    escribir_csv(salida / 'partes_rechazados.csv',
                 ['archivo', 'registro', 'id', 'motivo'], rechazados)
    escribir_csv(salida / 'archivos_omitidos.csv', ['archivo', 'motivo'], errores)
    resumen = {
        'estado': 'parcial' if errores else 'completo',
        'archivos_encontrados': encontrados,
        'archivos_omitidos': len(errores),
        'registros_leidos': len(validos) + len(rechazados),
        'validos': len(validos), 'rechazados': len(rechazados),
        'prioritarios': len(prioridades),
        'por_fenomeno': dict(sorted(Counter(p['fenomeno'] for p in validos).items())),
    }
    temporal = salida / 'resumen.tmp'
    temporal.write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + '\n',
                        encoding='utf-8')
    temporal.replace(salida / 'resumen.json')
    return resumen


def main():
    parser = argparse.ArgumentParser(description='Procesa los partes del turno de noche')
    parser.add_argument('--config', type=Path, default=BASE / 'config.json')
    args = parser.parse_args()
    try:
        config, entrada, salida = cargar_configuracion(args.config.resolve())
        archivos = sorted(p for p in entrada.glob('*.csv') if p.is_file())
        if not archivos:
            raise ValueError('No hay archivos CSV. No se generan resultados nuevos.')
        salida.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
            handlers=[logging.FileHandler(salida / 'turno_de_noche.log', encoding='utf-8'),
                      logging.StreamHandler()], force=True)
        LOG.info('INICIO: %s archivos', len(archivos))
        validos, rechazados, errores = procesar(archivos, config)
        resumen = guardar_resultados(salida, config, validos, rechazados,
                                     errores, len(archivos))
        LOG.info('FIN (%s): %s válidos, %s rechazados, %s prioritarios',
                 resumen['estado'], resumen['validos'], resumen['rechazados'],
                 resumen['prioritarios'])
        print(json.dumps(resumen, ensure_ascii=False, indent=2))
        print('Resultados:', salida)
        return 2 if errores else 0
    except (OSError, ValueError, csv.Error) as error:
        LOG.error('EJECUCIÓN FALLIDA: %s. No dar por actuales las salidas previas.', error)
        return 1


if __name__ == '__main__':
    sys.exit(main())
