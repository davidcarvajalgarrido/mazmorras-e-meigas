"""Pruebas del comportamiento observable, sin modificar los datos originales."""
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ORIGINAL = Path(__file__).resolve().parents[2] / 'aventura_01'


class Aventura01Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.case = self.work / 'aventura_01'
        shutil.copytree(ORIGINAL, self.case,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc',
                                                     'salida', 'salida_ejemplos',
                                                     'salida_riesgo_5'))

    def run_script(self, script='procesar.py', *arguments):
        env = dict(os.environ, PYTHONIOENCODING='utf-8')
        # Se ejecuta deliberadamente fuera de la carpeta del proyecto.
        return subprocess.run([sys.executable, str(self.case / script), *arguments],
                              cwd=self.work, env=env, capture_output=True,
                              encoding='utf-8', timeout=20)

    def summary(self, folder='salida'):
        return json.loads((self.case / folder / 'resumen.json').read_text(encoding='utf-8'))

    def test_lote_inicial_y_procedencia_de_rechazos(self):
        run = self.run_script()
        self.assertEqual(run.returncode, 0, run.stderr)
        result = self.summary()
        self.assertEqual((result['registros_leidos'], result['validos'],
                          result['rechazados'], result['prioritarios']), (18, 12, 6, 4))
        with (self.case / 'salida/partes_rechazados.csv').open(encoding='utf-8-sig', newline='') as f:
            rejects = list(csv.DictReader(f))
        self.assertEqual(len(rejects), 6)
        self.assertTrue(all(row['archivo'] and row['registro'] and row['motivo'] for row in rejects))
        duplicate = next(row for row in rejects if row['id'] == 'MEI-002')
        self.assertIn('repetido', duplicate['motivo'])
        log = (self.case / 'salida/turno_de_noche.log').read_text(encoding='utf-8')
        self.assertIn('INICIO', log)
        self.assertIn('FIN (completo)', log)

    def test_reejecucion_no_acumula_csv(self):
        self.assertEqual(self.run_script().returncode, 0)
        paths = sorted((self.case / 'salida').glob('*.csv'))
        before = {path.name: path.read_bytes() for path in paths}
        summary = self.summary()
        self.assertEqual(self.run_script().returncode, 0)
        self.assertEqual(before, {path.name: path.read_bytes() for path in paths})
        self.assertEqual(self.summary(), summary)
        log = (self.case / 'salida/turno_de_noche.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('INICIO:'), 2)

    def test_ultimo_aviso_y_orden_de_prioridad(self):
        shutil.copy2(self.case / 'reserva/04_ultimo_aviso.csv', self.case / 'entrada')
        self.assertEqual(self.run_script().returncode, 0)
        result = self.summary()
        self.assertEqual((result['registros_leidos'], result['validos'],
                          result['rechazados'], result['prioritarios']), (19, 13, 6, 5))
        with (self.case / 'salida/avisos_prioritarios.csv').open(encoding='utf-8-sig', newline='') as f:
            priorities = list(csv.DictReader(f))
        self.assertIn('MEI-018', [p['id'] for p in priorities])
        self.assertEqual(priorities,
                         sorted(priorities, key=lambda p: (-int(p['nivel_riesgo']), p['id'])))

    def test_json_alternativo_cambia_prioridad_no_validez(self):
        run = self.run_script('procesar.py', '--config', str(self.case / 'config_riesgo_5.json'))
        self.assertEqual(run.returncode, 0, run.stderr)
        result = self.summary('salida_riesgo_5')
        self.assertEqual((result['validos'], result['rechazados'], result['prioritarios']), (12, 6, 2))

    def test_archivo_defectuoso_da_lote_parcial(self):
        shutil.copy2(self.case / 'escenarios/99_cabecera_incorrecta.csv', self.case / 'entrada')
        run = self.run_script()
        self.assertEqual(run.returncode, 2, run.stderr)
        result = self.summary()
        self.assertEqual(result['estado'], 'parcial')
        self.assertEqual(result['archivos_omitidos'], 1)
        self.assertEqual((result['validos'], result['rechazados']), (12, 6))
        with (self.case / 'salida/archivos_omitidos.csv').open(encoding='utf-8-sig', newline='') as f:
            omitted = list(csv.DictReader(f))
        self.assertEqual(omitted[0]['archivo'], '99_cabecera_incorrecta.csv')

    def test_json_invalido_detiene_sin_crear_salidas(self):
        run = self.run_script('procesar.py', '--config', str(self.case / 'escenarios/config_rota.json'))
        self.assertEqual(run.returncode, 1)
        self.assertFalse((self.case / 'salida/resumen.json').exists())

    def test_configuracion_semanticamente_invalida(self):
        config = json.loads((self.case / 'config.json').read_text(encoding='utf-8'))
        config['riesgo_prioritario'] = 'muchísimo'
        bad = self.case / 'config_invalida.json'
        bad.write_text(json.dumps(config), encoding='utf-8')
        self.assertEqual(self.run_script('procesar.py', '--config', str(bad)).returncode, 1)

    def test_todo_rechazado_limpia_salida_anterior(self):
        self.assertEqual(self.run_script().returncode, 0)
        for path in (self.case / 'entrada').glob('*.csv'):
            path.unlink()
        with (self.case / 'entrada/invalido.csv').open('w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'fecha', 'localidad', 'fenomeno', 'nivel_riesgo', 'descripcion'])
            writer.writerow(['MEI-X', '2026-11-18', '', 'trasno', '2', 'Falta la localidad'])
        self.assertEqual(self.run_script().returncode, 0)
        self.assertEqual((self.summary()['validos'], self.summary()['rechazados']), (0, 1))
        with (self.case / 'salida/incidencias_validadas.csv').open(encoding='utf-8-sig', newline='') as f:
            self.assertEqual(list(csv.DictReader(f)), [])

    def test_entrada_vacia_no_produce_resultado_nuevo(self):
        for path in (self.case / 'entrada').glob('*.csv'):
            path.unlink()
        self.assertEqual(self.run_script().returncode, 1)
        self.assertFalse((self.case / 'salida/resumen.json').exists())

    def test_etapas_y_ejemplos_ejecutables(self):
        for folder in ['etapas', 'ejemplos']:
            for script in sorted((self.case / folder).glob('*.py')):
                with self.subTest(script=script.name):
                    run = self.run_script(str(script.relative_to(self.case)))
                    self.assertEqual(run.returncode, 0, run.stderr)
                    if script.name == 'etapa_03_validacion.py':
                        self.assertIn('Válidos: 13; rechazados: 5', run.stdout)
                    if script.name == 'etapa_05_prioridades.py':
                        self.assertIn('Válidos: 12; rechazados: 6', run.stdout)
                        self.assertIn('Prioritarios: 4', run.stdout)
        comparison = json.loads((self.case / 'salida_ejemplos/comparacion_umbrales.json').read_text(encoding='utf-8'))
        self.assertEqual((len(comparison['4']), len(comparison['5'])), (4, 2))


if __name__ == '__main__':
    unittest.main()
