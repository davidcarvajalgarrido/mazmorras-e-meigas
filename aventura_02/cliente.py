"""O pacto da brétema: consumir dos servicios HTTP desde Python."""
import argparse
import json
import os
import time
from datetime import date, datetime
from pathlib import Path

import requests

METEO_URL = 'https://servizos.meteogalicia.gal/mgrss/predicion/jsonPredConcellos.action'
BASE_LOCAL = 'http://127.0.0.1:8765'
CLAVE_DEMO = 'clave-publica-solo-para-la-demo'


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


def extraer_franjas(datos, hoy=None):
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
                                'probabilidad_lluvia': probabilidad})
        return franjas
    except (KeyError, TypeError, AttributeError, ValueError) as error:
        raise ValueError('Respuesta meteorológica no válida: ' + str(error)) from error


def elegir_ritual(franjas):
    # Primera franja elegible en orden cronológico. Es una regla ficticia.
    for franja in sorted(franjas, key=lambda f: (f['fecha'], ('manha', 'tarde', 'noite').index(f['franja']))):
        if franja['probabilidad_lluvia'] >= 60:
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
    parser.add_argument('--offline', action='store_true', help='Meteo sintética por HTTP local; requiere servidor --demo')
    parser.add_argument('--demo', action='store_true', help='Usar la credencial pública de demostración')
    parser.add_argument('--municipio', type=int, default=15078)
    parser.add_argument('--base', default=BASE_LOCAL)
    parser.add_argument('--salida', type=Path, default=Path(__file__).resolve().parent / 'salida' / 'resultado.json')
    return parser.parse_args()


def main():
    args = argumentos()
    base = args.base.rstrip('/')
    # Evitar enviar credenciales por HTTP remoto por un cambio accidental de --base.
    from urllib.parse import urlsplit
    url = urlsplit(base)
    if url.scheme != 'https' and not (url.scheme == 'http' and url.hostname in ('127.0.0.1', 'localhost', '::1')):
        raise SystemExit('La API debe usar HTTPS o HTTP sobre loopback local')
    clave = CLAVE_DEMO if args.demo else os.getenv('CONJURO_API_KEY')
    if not clave:
        raise SystemExit('Define CONJURO_API_KEY o utiliza --demo')
    print('METEO: DATOS SINTÉTICOS DE ENSAYO' if args.offline else 'METEO: consulta al servicio público de MeteoGalicia')
    try:
        meteo = base + '/meteo/prediccion' if args.offline else METEO_URL
        datos = obtener_json(meteo, params={'idConc': args.municipio})
        franjas = extraer_franjas(datos)
        print(f'Franjas disponibles desde hoy: {len(franjas)}')
        ritual = elegir_ritual(franjas)
        if ritual is None:
            print('No hay condiciones adecuadas. No se solicita ninguna invocación.')
            args.salida.parent.mkdir(parents=True, exist_ok=True)
            args.salida.write_text(json.dumps({
                'fuente': 'sintética de ensayo' if args.offline else 'MeteoGalicia',
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
        salida = {'fuente': 'sintética de ensayo' if args.offline else 'MeteoGalicia',
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
