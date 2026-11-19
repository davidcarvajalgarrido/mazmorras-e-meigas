"""API didáctica local. Arrancar con --demo; no es un servidor de producción."""
import argparse
import hmac
import json
import math
import os
import secrets
import threading
import time
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from dotenv import load_dotenv

CLAVE_DEMO = 'clave-publica-solo-para-la-demo'

load_dotenv(Path(__file__).resolve().parent / '.env', override=False)


def prediccion_ejemplo(municipio=15078):
    """Datos sintéticos con la estructura de MeteoGalicia, nunca datos en directo."""
    nombres = {15078: 'Santiago de Compostela', 15030: 'A Coruña', 15037: 'Fisterra'}
    return {'predConcello': {
        'idConcello': municipio, 'nome': nombres.get(municipio, 'Municipio de ejemplo'),
        'listaPredDiaConcello': [
            {'dataPredicion': (date.today() + timedelta(days=i)).isoformat() + 'T00:00:00',
             'tMin': 9 + i, 'tMax': 15 + i,
             'pchoiva': {'manha': p, 'tarde': p + 5, 'noite': p + 10}}
            for i, p in enumerate([20, 70, 40])
        ]}}


class Servidor(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, direccion, clave, demo=False, ttl=900):
        super().__init__(direccion, Manejador)
        self.clave = clave
        self.demo = demo
        self.ttl = ttl
        self.tokens = {}
        self.invocaciones = {}
        self.intentos = {}
        self.cerrojo = threading.Lock()


class Manejador(BaseHTTPRequestHandler):
    # HTTP local sobre loopback. Un servicio remoto con credenciales debe usar HTTPS.
    def log_message(self, formato, *args):
        pass  # No registrar URLs, cabeceras ni cuerpos con credenciales.

    def responder(self, estado, datos, cabeceras=None):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode('utf-8')
        self.enviar(estado, cuerpo, 'application/json; charset=utf-8', cabeceras)

    def enviar(self, estado, cuerpo, tipo, cabeceras=None):
        self.send_response(estado)
        self.send_header('Content-Type', tipo)
        self.send_header('Content-Length', str(len(cuerpo)))
        for nombre, valor in (cabeceras or {}).items():
            self.send_header(nombre, valor)
        self.end_headers()
        try:
            self.wfile.write(cuerpo)
        except (BrokenPipeError, ConnectionResetError):
            pass  # El cliente puede haber agotado su timeout de demostración.

    def autorizado(self):
        esquema, _, token = self.headers.get('Authorization', '').partition(' ')
        with self.server.cerrojo:
            valido = (esquema.lower() == 'bearer' and bool(token)
                      and self.server.tokens.get(token, 0) > time.monotonic())
        if not valido:
            self.responder(401, {'error': 'Token ausente, incorrecto o caducado'},
                           {'WWW-Authenticate': 'Bearer'})
        return valido

    def leer_json(self):
        if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
            self.responder(415, {'error': 'Se requiere Content-Type: application/json'})
            return None
        try:
            longitud = int(self.headers.get('Content-Length', '0'))
            if not 0 < longitud <= 16384:
                raise ValueError('Tamaño del cuerpo no válido')
            datos = json.loads(self.rfile.read(longitud))
            if not isinstance(datos, dict):
                raise ValueError('El cuerpo debe ser un objeto JSON')
            return datos
        except (ValueError, UnicodeError):
            self.responder(400, {'error': 'Cuerpo JSON incorrecto'})
            return None

    def do_GET(self):
        url = urlsplit(self.path)
        ruta = url.path
        if ruta == '/salud':
            self.responder(200, {'estado': 'listo', 'modo_demo': self.server.demo})
        elif self.server.demo and ruta == '/meteo/prediccion':
            try:
                municipio = int(parse_qs(url.query).get('idConc', ['15078'])[0])
            except ValueError:
                self.responder(400, {'error': 'idConc debe ser entero'})
                return
            self.responder(200, prediccion_ejemplo(municipio))
        elif self.server.demo and ruta.startswith('/laboratorio/'):
            caso = ruta.rsplit('/', 1)[-1]
            if caso == 'inestable':
                etiqueta = self.headers.get('X-Ensayo', 'compartido')
                with self.server.cerrojo:
                    intento = self.server.intentos.get(etiqueta, 0) + 1
                    self.server.intentos[etiqueta] = intento
                if intento <= 2:
                    self.responder(503, {'error': 'Portal ocupado', 'intento': intento},
                                   {'Retry-After': '0'})
                else:
                    self.responder(200, {'estado': 'portal disponible', 'intento': intento})
            elif caso == 'lento':
                time.sleep(0.3)
                self.responder(200, {'estado': 'respuesta tardía'})
            elif caso == 'json-roto':
                self.enviar(200, b'{esto no es JSON', 'application/json')
            elif caso == 'datos-incompletos':
                self.responder(200, {'mensaje': 'JSON válido, estructura inesperada'})
            else:
                self.responder(404, {'error': 'Escenario inexistente'})
        elif ruta.startswith('/invocaciones/'):
            if not self.autorizado():
                return
            identificador = ruta.rsplit('/', 1)[-1]
            with self.server.cerrojo:
                resultado = self.server.invocaciones.get(identificador)
            self.responder(200 if resultado else 404,
                           resultado or {'error': 'Invocación inexistente'})
        else:
            self.responder(404, {'error': 'Recurso inexistente'})

    def do_POST(self):
        ruta = urlsplit(self.path).path
        if ruta == '/sesiones':
            clave = self.headers.get('X-API-Key', '')
            if not hmac.compare_digest(clave.encode(), self.server.clave.encode()):
                self.responder(401, {'error': 'API key ausente o incorrecta'})
                return
            token = secrets.token_urlsafe(32)
            with self.server.cerrojo:
                self.server.tokens[token] = time.monotonic() + self.server.ttl
            self.responder(201, {'access_token': token, 'token_type': 'Bearer',
                                 'expires_in': self.server.ttl})
        elif ruta == '/invocaciones':
            if not self.autorizado():
                return
            datos = self.leer_json()
            if datos is None:
                return
            try:
                if datos.get('criatura') != 'espiritu_da_bretema':
                    raise ValueError('Criatura desconocida')
                if not isinstance(datos.get('municipio'), str) or not datos['municipio'].strip():
                    raise ValueError('Falta el nombre del municipio')
                if date.fromisoformat(datos.get('fecha', '')) < date.today():
                    raise ValueError('La fecha ya ha pasado')
                if datos.get('franja') not in ('manha', 'tarde', 'noite'):
                    raise ValueError('Franja desconocida')
                fuente = datos.get('fuente_meteorologica')
                variable = datos.get('variable_meteorologica')
                unidad = datos.get('unidad_meteorologica')
                criterio = datos.get('criterio_ritual')
                if fuente == 'MeteoSIX v5.1':
                    cantidad = datos.get('precipitacion_lm2')
                    coordenadas = datos.get('coordenadas')
                    if variable != 'precipitation_amount' or unidad != 'lm2':
                        raise ValueError('MeteoSIX requiere precipitation_amount en lm2')
                    if criterio != 'precipitation_amount > 0 lm2':
                        raise ValueError('El criterio declarado para MeteoSIX no es válido')
                    if ('probabilidad_lluvia' in datos
                            or type(cantidad) not in (int, float)
                            or cantidad <= 0
                            or (type(cantidad) is float and not math.isfinite(cantidad))):
                        raise ValueError('MeteoSIX requiere una cantidad horaria positiva')
                    if (not isinstance(coordenadas, dict)
                            or type(coordenadas.get('longitud')) not in (int, float)
                            or type(coordenadas.get('latitud')) not in (int, float)
                            or not -180 <= coordenadas['longitud'] <= 180
                            or not -90 <= coordenadas['latitud'] <= 90):
                        raise ValueError('MeteoSIX requiere coordenadas válidas')
                else:
                    if fuente not in ('MeteoGalicia JSON municipal', 'ensayo sintético local'):
                        raise ValueError('Fuente meteorológica desconocida')
                    if variable != 'pchoiva' or unidad != '%':
                        raise ValueError('MeteoGalicia requiere pchoiva en porcentaje')
                    if criterio != 'probabilidad_lluvia >= 60 %':
                        raise ValueError('El criterio declarado para MeteoGalicia no es válido')
                    if type(datos.get('municipio_id')) is not int or datos['municipio_id'] <= 0:
                        raise ValueError('municipio_id debe ser un entero positivo')
                    probabilidad = datos.get('probabilidad_lluvia')
                    if (type(probabilidad) not in (int, float)
                            or not 60 <= probabilidad <= 100
                            or 'precipitacion_lm2' in datos):
                        raise ValueError('El ritual requiere una probabilidad de lluvia entre 60 y 100')
            except (ValueError, TypeError) as error:
                self.responder(422, {'error': str(error)})
                return
            with self.server.cerrojo:
                identificador = f'INV-{len(self.server.invocaciones) + 1:03}'
                resultado = {**datos, 'id': identificador, 'estado': 'registrada'}
                self.server.invocaciones[identificador] = resultado
            self.responder(201, resultado, {'Location': f'/invocaciones/{identificador}'})
        else:
            self.responder(404, {'error': 'Recurso inexistente'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='Clave pública y escenarios de ensayo')
    parser.add_argument('--puerto', type=int, default=8765)
    args = parser.parse_args()
    clave = CLAVE_DEMO if args.demo else os.getenv('CONJURO_API_KEY')
    if not clave:
        parser.error('Define CONJURO_API_KEY o utiliza --demo')
    servidor = Servidor(('127.0.0.1', args.puerto), clave, demo=args.demo)
    print(f'Portal local: http://127.0.0.1:{args.puerto} | demo={args.demo}', flush=True)
    print('Estado en memoria: se reinicia al cerrar. Ctrl+C para terminar.', flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()


if __name__ == '__main__':
    main()
