"""Primera misión: localizar los partes. Ejecutable desde cualquier carpeta."""
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
entrada = BASE / 'entrada'

print('Carpeta del terminal:', Path.cwd())
print('Carpeta de entrada:', entrada)
for archivo in sorted(entrada.glob('*.csv')):
    print('Parte recibido:', archivo.name)
