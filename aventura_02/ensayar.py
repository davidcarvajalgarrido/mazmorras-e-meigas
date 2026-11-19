"""Ensayo completo en una terminal, con HTTP local y sin datos externos."""
import subprocess
import sys
import threading
from pathlib import Path
from servidor import Servidor, CLAVE_DEMO


def main():
    servidor = Servidor(('127.0.0.1', 0), CLAVE_DEMO, demo=True)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    base = f'http://127.0.0.1:{servidor.server_port}'
    carpeta = Path(__file__).resolve().parent
    print('ENSAYO: meteorología sintética + API local temporal', flush=True)
    try:
        resultado = subprocess.run([sys.executable, str(carpeta / 'cliente.py'),
                                    '--offline', '--demo', '--base', base], check=False)
        if resultado.returncode:
            return resultado.returncode
        print('\nLABORATORIO DE ERRORES', flush=True)
        return subprocess.run([sys.executable, str(carpeta / 'etapas' / '05_cuando_falla_el_portal.py'),
                               '--base', base], check=False).returncode
    finally:
        servidor.shutdown()
        servidor.server_close()
        hilo.join()


if __name__ == '__main__':
    raise SystemExit(main())
