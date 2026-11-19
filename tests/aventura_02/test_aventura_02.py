"""Pruebas sobre HTTP real local y un servidor efímero; sin red externa."""
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import uuid
from contextlib import redirect_stdout
from datetime import date, timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import requests
from aventura_02 import cliente
from aventura_02.servidor import Servidor, CLAVE_DEMO, prediccion_ejemplo


def prediccion_meteosix():
    manana = (date.today() + timedelta(days=1)).isoformat()
    return {'type': 'FeatureCollection', 'features': [{
        'type': 'Feature',
        'geometry': {'type': 'Point', 'coordinates': [-8.5448, 42.8782]},
        'properties': {'days': [{
            'timePeriod': {},
            'variables': [{
                'name': 'precipitation_amount',
                'units': 'lm2',
                'values': [
                    {'timeInstant': manana + 'T08:00:00+01', 'modelRun': None, 'value': 0},
                    {'timeInstant': manana + 'T09:00:00+01', 'modelRun': '2026-11-19T00:00:00+01',
                     'value': 0.4},
                    {'timeInstant': manana + 'T13:00:00+01', 'modelRun': '2026-11-19T00:00:00+01',
                     'value': 1.2},
                ],
            }],
        }]},
    }]}


class Aventura(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = Servidor(('127.0.0.1', 0), CLAVE_DEMO, demo=True)
        cls.hilo = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.hilo.start()
        cls.base = 'http://127.0.0.1:' + str(cls.servidor.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()
        cls.hilo.join()

    def token(self):
        return cliente.autenticar(self.base, CLAVE_DEMO)

    def ritual(self):
        return cliente.elegir_ritual(cliente.extraer_franjas(prediccion_ejemplo()))

    def test_recorrido_completo(self):
        datos = cliente.obtener_json(self.base + '/meteo/prediccion', params={'idConc': 15078})
        franjas = cliente.extraer_franjas(datos)
        self.assertEqual(len(franjas), 9)
        ritual = cliente.elegir_ritual(franjas)
        self.assertEqual(ritual['probabilidad_lluvia'], 70)
        self.assertEqual(ritual['fecha'], (date.today() + timedelta(days=1)).isoformat())
        token = self.token()
        nueva = cliente.invocar(self.base, token, ritual)
        resultado = cliente.obtener_json(self.base + '/invocaciones/' + nueva['id'],
                                          headers={'Authorization': 'Bearer ' + token})
        self.assertEqual(resultado, nueva)
        self.assertEqual(resultado['estado'], 'registrada')

    def test_script_desde_otra_carpeta(self):
        ruta = Path(cliente.__file__).resolve()
        with tempfile.TemporaryDirectory() as carpeta:
            salida = Path(carpeta) / 'resultado.json'
            proceso = subprocess.run([sys.executable, str(ruta), '--offline', '--demo',
                                      '--base', self.base, '--salida', str(salida)],
                                     cwd=carpeta, capture_output=True, text=True, timeout=10)
            self.assertEqual(proceso.returncode, 0, proceso.stdout + proceso.stderr)
            resultado = json.loads(salida.read_text(encoding='utf-8'))
            self.assertEqual(resultado['fuente'], 'sintética de ensayo')
            self.assertNotIn('access_token', resultado)
            self.assertNotIn(CLAVE_DEMO, proceso.stdout)

    def test_sin_condiciones(self):
        datos = prediccion_ejemplo()
        for dia in datos['predConcello']['listaPredDiaConcello']:
            dia['pchoiva'] = dict.fromkeys(('manha', 'tarde', 'noite'), 20)
        self.assertIsNone(cliente.elegir_ritual(cliente.extraer_franjas(datos)))

    def test_datos_ausentes_y_fechas_pasadas(self):
        datos = prediccion_ejemplo()
        dias = datos['predConcello']['listaPredDiaConcello']
        dias[0]['dataPredicion'] = (date.today() - timedelta(days=1)).isoformat()
        dias[1]['pchoiva']['manha'] = -9999
        dias[1]['pchoiva']['tarde'] = None
        self.assertEqual(len(cliente.extraer_franjas(datos)), 4)

    def test_contrato_y_valores_invalidos(self):
        for datos in [{}, {'predConcello': None}]:
            with self.assertRaises(ValueError):
                cliente.extraer_franjas(datos)
        for valor in [101, '70', True]:
            datos = prediccion_ejemplo()
            datos['predConcello']['listaPredDiaConcello'][0]['pchoiva']['manha'] = valor
            with self.assertRaises(ValueError):
                cliente.extraer_franjas(datos)

    def test_adaptacion_meteosix_y_regla_sin_porcentaje(self):
        franjas = cliente.extraer_franjas_meteosix(
            prediccion_meteosix(), 'Santiago de Compostela', -8.5448, 42.8782,
            hoy=date.today()
        )
        self.assertEqual([(f['franja'], f['hora'], f['precipitacion_lm2'])
                          for f in franjas], [('manha', '08:00', 0),
                                              ('manha', '09:00', 0.4),
                                              ('tarde', '13:00', 1.2)])
        ritual = cliente.elegir_ritual(franjas)
        self.assertEqual(ritual['precipitacion_lm2'], 0.4)
        self.assertEqual(ritual['variable_meteorologica'], 'precipitation_amount')
        self.assertEqual(ritual['unidad_meteorologica'], 'lm2')
        self.assertEqual(ritual['criterio_ritual'], 'precipitation_amount > 0 lm2')
        self.assertNotIn('probabilidad_lluvia', ritual)

    def test_meteosix_consulta_usa_api_key_en_params_sin_clave_real(self):
        with patch.object(cliente, 'obtener_json', return_value={}) as obtener:
            cliente.consultar_meteosix('clave-de-prueba', -8.5448, 42.8782)
        args, kwargs = obtener.call_args
        self.assertEqual(args, (cliente.METEOSIX_URL,))
        self.assertEqual(kwargs['params']['API_KEY'], 'clave-de-prueba')
        self.assertEqual(kwargs['params']['coords'], '-8.5448,42.8782')
        self.assertEqual(kwargs['params']['variables'], 'precipitation_amount')
        self.assertEqual(kwargs['params']['units'], 'lm2')
        self.assertEqual(kwargs['params']['tz'], 'Europe/Madrid')

    def test_meteosix_sin_clave_y_error_de_api_sin_filtrar_mensaje(self):
        with self.assertRaisesRegex(ValueError, 'METEOSIX_API_KEY'):
            cliente.consultar_meteosix('', -8.5448, 42.8782)
        with self.assertRaises(ValueError) as error:
            cliente.extraer_franjas_meteosix(
                {'exception': {'code': '005', 'message': 'texto que no se debe mostrar'}},
                'Santiago de Compostela', -8.5448, 42.8782
            )
        self.assertIn('005', str(error.exception))
        self.assertNotIn('texto que no se debe mostrar', str(error.exception))

    def test_cliente_exige_clave_meteosix_sin_usar_la_de_conjuro(self):
        with patch.object(sys, 'argv', ['cliente.py', '--fuente', 'meteosix', '--demo']), \
                patch.dict(os.environ, {'METEOSIX_API_KEY': ''}):
            with self.assertRaisesRegex(SystemExit, 'METEOSIX_API_KEY'):
                cliente.main()

    def test_error_http_meteosix_no_imprime_la_clave(self):
        response = requests.Response()
        response.status_code = 403
        response.url = cliente.METEOSIX_URL + '?API_KEY=clave-solo-prueba'
        error = requests.HTTPError(
            '403 Client Error: Forbidden for url: ' + response.url,
            response=response
        )
        salida = StringIO()
        with patch.object(sys, 'argv', ['cliente.py', '--fuente', 'meteosix', '--demo']), \
                patch.dict(os.environ, {'METEOSIX_API_KEY': 'clave-solo-prueba'}), \
                patch.object(cliente, 'consultar_meteosix', side_effect=error), \
                redirect_stdout(salida):
            self.assertEqual(cliente.main(), 1)
        self.assertIn('403', salida.getvalue())
        self.assertNotIn('clave-solo-prueba', salida.getvalue())

    def test_meteosix_datos_incompletos_y_valores_ausentes(self):
        with self.assertRaises(ValueError):
            cliente.extraer_franjas_meteosix(
                {'features': [{'properties': {}}]},
                'Santiago de Compostela', -8.5448, 42.8782
            )
        datos = prediccion_meteosix()
        datos['features'][0]['properties']['days'][0]['variables'][0]['values'] = [
            {'timeInstant': (date.today() + timedelta(days=1)).isoformat()
                            + 'T09:00:00+01', 'modelRun': None, 'value': None}
        ]
        franjas = cliente.extraer_franjas_meteosix(
            datos, 'Santiago de Compostela', -8.5448, 42.8782
        )
        self.assertEqual(franjas, [])
        self.assertIsNone(cliente.elegir_ritual(franjas))
        for value in [True, -1, '0.5']:
            datos = prediccion_meteosix()
            datos['features'][0]['properties']['days'][0]['variables'][0]['values'][0]['value'] = value
            with self.assertRaises(ValueError):
                cliente.extraer_franjas_meteosix(
                    datos, 'Santiago de Compostela', -8.5448, 42.8782
                )

    def test_credenciales_y_caducidad(self):
        with self.assertRaises(requests.HTTPError) as error:
            cliente.autenticar(self.base, 'incorrecta')
        self.assertEqual(error.exception.response.status_code, 401)
        token = self.token()
        with self.servidor.cerrojo:
            self.servidor.tokens[token] = 0
        respuesta = requests.get(self.base + '/invocaciones/INV-001',
                                 headers={'Authorization': 'Bearer ' + token}, timeout=3)
        self.assertEqual(respuesta.status_code, 401)

    def test_validacion_y_cuerpo_http(self):
        headers = {'Authorization': 'Bearer ' + self.token()}
        for cuerpo in [{}, {'criatura': 'patata_cosmica'}, {**self.ritual(), 'probabilidad_lluvia': 59},
                       {**self.ritual(), 'fecha': None}]:
            respuesta = requests.post(self.base + '/invocaciones', json=cuerpo, headers=headers, timeout=3)
            self.assertEqual(respuesta.status_code, 422)
        respuesta = requests.post(self.base + '/invocaciones', data='{}', headers=headers, timeout=3)
        self.assertEqual(respuesta.status_code, 415)
        respuesta = requests.post(self.base + '/invocaciones', data='{roto',
                                 headers={**headers, 'Content-Type': 'application/json'}, timeout=3)
        self.assertEqual(respuesta.status_code, 400)

    def test_invocacion_meteosix_validada_sin_probabilidad(self):
        franjas = cliente.extraer_franjas_meteosix(
            prediccion_meteosix(), 'Santiago de Compostela', -8.5448, 42.8782
        )
        ritual = cliente.elegir_ritual(franjas)
        token = self.token()
        respuesta = requests.post(
            self.base + '/invocaciones', json=ritual,
            headers={'Authorization': 'Bearer ' + token}, timeout=3
        )
        self.assertEqual(respuesta.status_code, 201, respuesta.text)
        self.assertNotIn('probabilidad_lluvia', respuesta.json())
        self.assertEqual(respuesta.json()['fuente_meteorologica'], 'MeteoSIX v5.1')
        ritual_invalido = {**ritual, 'precipitacion_lm2': 0, 'probabilidad_lluvia': 70}
        respuesta = requests.post(
            self.base + '/invocaciones', json=ritual_invalido,
            headers={'Authorization': 'Bearer ' + token}, timeout=3
        )
        self.assertEqual(respuesta.status_code, 422)

    def test_no_encontrado(self):
        respuesta = requests.get(self.base + '/invocaciones/INV-99999',
                                 headers={'Authorization': 'Bearer ' + self.token()}, timeout=3)
        self.assertEqual(respuesta.status_code, 404)

    def test_reintentos_get(self):
        resultado = cliente.obtener_json(self.base + '/laboratorio/inestable',
                                         headers={'X-Ensayo': str(uuid.uuid4())})
        self.assertEqual(resultado['intento'], 3)
        with self.assertRaises(requests.HTTPError) as error:
            cliente.obtener_json(self.base + '/laboratorio/inestable', intentos=1,
                                 headers={'X-Ensayo': str(uuid.uuid4())})
        self.assertEqual(error.exception.response.status_code, 503)

    def test_200_no_garantiza_datos_utilizables(self):
        with self.assertRaises(requests.exceptions.JSONDecodeError):
            cliente.obtener_json(self.base + '/laboratorio/json-roto')
        with self.assertRaises(ValueError):
            cliente.extraer_franjas(cliente.obtener_json(self.base + '/laboratorio/datos-incompletos'))

    def test_timeout(self):
        with self.assertRaises(requests.Timeout):
            cliente.obtener_json(self.base + '/laboratorio/lento', intentos=1, timeout=0.03)

    def test_post_no_se_reintenta(self):
        with patch.object(cliente.requests, 'post', side_effect=requests.Timeout) as post:
            with self.assertRaises(requests.Timeout):
                cliente.invocar(self.base, 'token', self.ritual())
            self.assertEqual(post.call_count, 1)


if __name__ == '__main__':
    unittest.main()
