"""Pruebas sobre HTTP real local y un servidor efímero; sin red externa."""
import json
import subprocess
import sys
import tempfile
import threading
import unittest
import uuid
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import requests
from aventura_02 import cliente
from aventura_02.servidor import Servidor, CLAVE_DEMO, prediccion_ejemplo


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
