"""O pacto da brétema: consumir dos servicios HTTP desde Python."""
import argparse
import json
import math
import os
import time
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit

import requests
from dotenv import load_dotenv

METEO_URL = 'https://servizos.meteogalicia.gal/mgrss/predicion/jsonPredConcellos.action'
METEOSIX_URL = 'https://servizos.meteogalicia.gal/apiv5/getNumericForecastInfo'
METEOSIX_VARIABLE = 'precipitation_amount'
METEOSIX_UNIT = 'lm2'
SANTIAGO_LONGITUD = -8.5448
SANTIAGO_LATITUD = 42.8782
BASE_LOCAL = 'http://127.0.0.1:8765'
CLAVE_DEMO = 'clave-publica-solo-para-la-demo'

load_dotenv(Path(__file__).resolve().parent / '.env', override=False)


def obtener_json(url, *, params=None, headers=None, intentos=3, timeout=(3.05, 8)):
    """Reintentos acotados SOLO para GET. No se reintentan errores de datos/JSON."""
    if not 1 <= intentos <= 3:
        raise ValueError('Se permiten de 1 a 3 intentos')
    for intento in range(intentos):
        try:
            respuesta = requests.get(url, params=params, headers=headers, timeout=timeout)
        except (requests.Timeout, requests.ConnectionError):
            if intento == intentos - 1:
                raise
            time.sleep(0.1 * 2 ** intento)
            continue
        if respuesta.status_code in (429, 502, 503, 504) and intento < intentos - 1:
            try:
                espera = min(2, max(0, float(respuesta.headers.get('Retry-After', '0.1'))))
            except ValueError:
                espera = 0.1 * 2 ** intento
            respuesta.close()
            time.sleep(espera)
            continue
        respuesta.raise_for_status()
        return respuesta.json()
    raise RuntimeError('No se obtuvo respuesta')


def extraer_franjas(datos, hoy=None, *, fuente='MeteoGalicia JSON municipal'):
    """Validar el contrato externo; no convertir -9999 en una predicción real."""
    hoy = hoy or date.today()
    try:
        prediccion = datos['predConcello']
        nombre = prediccion['nome']
        identificador = prediccion['idConcello']
        dias = prediccion['listaPredDiaConcello']
        if (not isinstance(nombre, str) or not nombre.strip()
                or type(identificador) is not int or not isinstance(dias, list)):
            raise ValueError('Tipos inesperados en la predicción')
        franjas = []
        for dia in dias:
            fecha = datetime.fromisoformat(dia['dataPredicion']).date()
            if fecha < hoy:
                continue
            probabilidades = dia['pchoiva']
            if not isinstance(probabilidades, dict):
                raise ValueError('pchoiva debe ser un objeto')
            for franja in ('manha', 'tarde', 'noite'):
                probabilidad = probabilidades.get(franja)
                if probabilidad is None or probabilidad == -9999:
                    continue
                if type(probabilidad) not in (int, float) or not 0 <= probabilidad <= 100:
                    raise ValueError('Probabilidad fuera de 0–100')
                franjas.append({'municipio_id': identificador, 'municipio': nombre,
                                'fecha': fecha.isoformat(), 'franja': franja,
                                'probabilidad_lluvia': probabilidad,
                                'fuente_meteorologica': fuente,
                                'variable_meteorologica': 'pchoiva',
                                'unidad_meteorologica': '%',
                                'criterio_ritual': 'probabilidad_lluvia >= 60 %'})
        return franjas
    except (KeyError, TypeError, AttributeError, ValueError) as error:
        raise ValueError('Respuesta meteorológica no válida: ' + str(error)) from error


def consultar_meteosix(api_key, longitud, latitud):
    """Consulta MeteoSIX v5.1; la clave es un parámetro obligatorio de la API."""
    if not api_key:
        raise ValueError('Define METEOSIX_API_KEY para consultar MeteoSIX')
    if (type(longitud) not in (int, float) or not -180 <= longitud <= 180
            or type(latitud) not in (int, float) or not -90 <= latitud <= 90
            or (type(longitud) is float and not math.isfinite(longitud))
            or (type(latitud) is float and not math.isfinite(latitud))):
        raise ValueError('Las coordenadas deben estar dentro de los rangos geográficos')
    return obtener_json(METEOSIX_URL, params={
        'API_KEY': api_key,
        'coords': f'{longitud},{latitud}',
        'variables': METEOSIX_VARIABLE,
        'units': METEOSIX_UNIT,
        'format': 'application/json',
        'lang': 'gl',
        'tz': 'Europe/Madrid',
    }, timeout=(3.05, 8))


def extraer_franjas_meteosix(datos, ubicacion, longitud, latitud, hoy=None):
    """Adaptar la respuesta GeoJSON horaria de MeteoSIX sin fabricar porcentajes."""
    hoy = hoy or date.today()
    try:
        if not isinstance(datos, dict):
            raise ValueError('La raíz debe ser un objeto')
        if not isinstance(ubicacion, str) or not ubicacion.strip():
            raise ValueError('La ubicación debe tener un nombre')
        excepcion = datos.get('exception')
        if excepcion is not None:
            codigo = excepcion.get('code') if isinstance(excepcion, dict) else None
            codigo = codigo if isinstance(codigo, str) and codigo.isdigit() else 'desconocido'
            raise ValueError('MeteoSIX devolvió la excepción ' + codigo)

        features = datos['features']
        if not isinstance(features, list) or len(features) != 1:
            raise ValueError('Se esperaba un único punto en features')
        feature = features[0]
        propiedades = feature['properties']
        dias = propiedades['days']
        if not isinstance(dias, list):
            raise ValueError('properties.days debe ser una lista')

        franjas = []
        coordenadas = {'longitud': longitud, 'latitud': latitud}
        for dia in dias:
            variables = dia.get('variables')
            if variables is None:
                continue
            if not isinstance(variables, list):
                raise ValueError('day.variables debe ser una lista o null')
            for variable in variables:
                if variable.get('name') != METEOSIX_VARIABLE:
                    continue
                if variable.get('units') != METEOSIX_UNIT:
                    raise ValueError('La unidad de precipitation_amount debe ser lm2')
                valores = variable['values']
                if valores is None:
                    continue
                if not isinstance(valores, list):
                    raise ValueError('variable.values debe ser una lista o null')
                for valor in valores:
                    instante = valor['timeInstant']
                    if (isinstance(instante, str) and len(instante) >= 3
                            and instante[-3] in '+-' and instante[-2:].isdigit()):
                        instante += ':00'
                    momento = datetime.fromisoformat(instante)
                    if momento.date() < hoy:
                        continue
                    cantidad = valor.get('value')
                    if cantidad is None or cantidad == '':
                        continue
                    if (type(cantidad) not in (int, float) or cantidad < 0
                            or (type(cantidad) is float and not math.isfinite(cantidad))):
                        raise ValueError('precipitation_amount debe ser un número no negativo')
                    if 6 <= momento.hour < 12:
                        franja = 'manha'
                    elif 12 <= momento.hour < 18:
                        franja = 'tarde'
                    elif 18 <= momento.hour < 24:
                        franja = 'noite'
                    else:
                        continue
                    franjas.append({
                        'municipio': ubicacion,
                        'coordenadas': coordenadas,
                        'fecha': momento.date().isoformat(),
                        'franja': franja,
                        'hora': momento.strftime('%H:%M'),
                        'precipitacion_lm2': cantidad,
                        'fuente_meteorologica': 'MeteoSIX v5.1',
                        'variable_meteorologica': METEOSIX_VARIABLE,
                        'unidad_meteorologica': METEOSIX_UNIT,
                        'criterio_ritual': 'precipitation_amount > 0 lm2',
                    })
        return franjas
    except (KeyError, TypeError, AttributeError, ValueError) as error:
        raise ValueError('Respuesta MeteoSIX no válida: ' + str(error)) from error


def elegir_ritual(franjas):
    # Primera franja elegible en orden cronológico. Cada fuente conserva su criterio.
    orden_franjas = ('manha', 'tarde', 'noite')
    franjas_ordenadas = sorted(
        franjas,
        key=lambda f: (f['fecha'], orden_franjas.index(f['franja']), f.get('hora', ''))
    )
    for franja in franjas_ordenadas:
        if (franja['variable_meteorologica'] == 'pchoiva'
                and franja['probabilidad_lluvia'] >= 60):
            return {**franja, 'criatura': 'espiritu_da_bretema'}
        if (franja['variable_meteorologica'] == METEOSIX_VARIABLE
                and franja['precipitacion_lm2'] > 0):
            return {**franja, 'criatura': 'espiritu_da_bretema'}
    return None


def autenticar(base, clave):
    respuesta = requests.post(base + '/sesiones', headers={'X-API-Key': clave}, timeout=(3.05, 8))
    respuesta.raise_for_status()
    datos = respuesta.json()
    if (not isinstance(datos, dict) or not isinstance(datos.get('access_token'), str)
            or not datos['access_token'] or datos.get('token_type') != 'Bearer'):
        raise ValueError('La respuesta de autenticación no contiene un token válido')
    return datos['access_token']


def invocar(base, token, ritual):
    respuesta = requests.post(base + '/invocaciones', json=ritual,
                             headers={'Authorization': 'Bearer ' + token}, timeout=(3.05, 8))
    # No repetir POST automáticamente: podría haberse creado aunque se pierda la respuesta.
    respuesta.raise_for_status()
    datos = respuesta.json()
    if (not isinstance(datos, dict) or not isinstance(datos.get('id'), str)
            or not datos['id'].startswith('INV-') or not datos['id'][4:].isdigit()):
        raise ValueError('La respuesta no contiene un identificador de invocación válido')
    return datos


def argumentos():
    parser = argparse.ArgumentParser(description=__doc__)
    fuente = parser.add_mutually_exclusive_group()
    fuente.add_argument('--offline', action='store_true', help='Meteo sintética por HTTP local; requiere servidor --demo')
    fuente.add_argument('--fuente', choices=('meteogalicia', 'meteosix'),
                        default='meteogalicia', help='Servicio meteorológico (por defecto: meteogalicia)')
    parser.add_argument('--demo', action='store_true', help='Usar la credencial pública de demostración')
    parser.add_argument('--municipio', type=int, default=15078)
    parser.add_argument('--ubicacion', default='Santiago de Compostela',
                        help='Nombre mostrado para la consulta MeteoSIX')
    parser.add_argument('--lon', type=float, default=SANTIAGO_LONGITUD,
                        help='Longitud para MeteoSIX (por defecto, Santiago)')
    parser.add_argument('--lat', type=float, default=SANTIAGO_LATITUD,
                        help='Latitud para MeteoSIX (por defecto, Santiago)')
    parser.add_argument('--base', default=BASE_LOCAL)
    parser.add_argument('--salida', type=Path, default=Path(__file__).resolve().parent / 'salida' / 'resultado.json')
    return parser.parse_args()


def main():
    args = argumentos()
    base = args.base.rstrip('/')
    # Evitar enviar credenciales por HTTP remoto por un cambio accidental de --base.
    url = urlsplit(base)
    if url.scheme != 'https' and not (url.scheme == 'http' and url.hostname in ('127.0.0.1', 'localhost', '::1')):
        raise SystemExit('La API debe usar HTTPS o HTTP sobre loopback local')
    fuente_meteorologica = (
        'ensayo sintético local' if args.offline else
        'MeteoSIX v5.1' if args.fuente == 'meteosix' else
        'MeteoGalicia JSON municipal'
    )
    fuente_resultado = (
        'sintética de ensayo' if args.offline else
        'MeteoSIX v5.1' if args.fuente == 'meteosix' else
        'MeteoGalicia'
    )
    meteo_key = os.getenv('METEOSIX_API_KEY') if args.fuente == 'meteosix' else None
    if args.fuente == 'meteosix' and not meteo_key:
        raise SystemExit('Define METEOSIX_API_KEY en aventura_02/.env o en el entorno')
    clave = CLAVE_DEMO if args.demo else os.getenv('CONJURO_API_KEY')
    if not clave:
        raise SystemExit('Define CONJURO_API_KEY o utiliza --demo')
    etiquetas = {
        'ensayo sintético local': 'METEO: DATOS SINTÉTICOS DE ENSAYO',
        'MeteoSIX v5.1': 'METEO: consulta autenticada a MeteoSIX v5.1',
        'MeteoGalicia JSON municipal': 'METEO: consulta al servicio público de MeteoGalicia',
    }
    print(etiquetas[fuente_meteorologica])
    try:
        if args.offline:
            datos = obtener_json(base + '/meteo/prediccion', params={'idConc': args.municipio})
            franjas = extraer_franjas(
                datos, fuente='ensayo sintético local'
            )
        elif args.fuente == 'meteosix':
            datos = consultar_meteosix(meteo_key, args.lon, args.lat)
            franjas = extraer_franjas_meteosix(
                datos, args.ubicacion, args.lon, args.lat
            )
        else:
            datos = obtener_json(METEO_URL, params={'idConc': args.municipio})
            franjas = extraer_franjas(datos)
        print(f'Franjas disponibles desde hoy: {len(franjas)}')
        ritual = elegir_ritual(franjas)
        if ritual is None:
            print('No hay condiciones adecuadas. No se solicita ninguna invocación.')
            args.salida.parent.mkdir(parents=True, exist_ok=True)
            args.salida.write_text(json.dumps({
                'fuente': fuente_resultado,
                'estado': 'sin condiciones', 'invocacion': None
            }, ensure_ascii=False, indent=2), encoding='utf-8')
            return 0
        print('Ritual elegido:', json.dumps(ritual, ensure_ascii=False))
        token = autenticar(base, clave)
        print('Autenticación correcta. Token recibido (no se muestra ni se guarda).')
        creada = invocar(base, token, ritual)
        resultado = obtener_json(base + '/invocaciones/' + creada['id'],
                                  headers={'Authorization': 'Bearer ' + token})
        if not isinstance(resultado, dict) or resultado.get('id') != creada['id'] or resultado.get('estado') != 'registrada':
            raise ValueError('El resultado consultado no coincide con la invocación')
        salida = {'fuente': fuente_resultado,
                  'invocacion': resultado}
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"Invocación {resultado['id']}: {resultado['estado']}. Resultado: {args.salida}")
        return 0
    except requests.HTTPError as error:
        print(f'ERROR HTTP {error.response.status_code}. Revisa la petición y el contrato del servicio.')
    except requests.Timeout:
        print('ERROR: tiempo de espera agotado. Si era un POST, el resultado puede ser incierto; no lo repitas a ciegas.')
    except requests.ConnectionError:
        print('ERROR: no se pudo conectar. Comprueba el servidor o la red.')
    except (requests.RequestException, ValueError, OSError):
        print('ERROR: respuesta inesperada o no se pudo guardar el resultado. Consulta el paso que estaba en ejecución.')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
