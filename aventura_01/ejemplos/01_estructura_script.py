"""Estructura mínima: importaciones, función reutilizable y entrada principal."""
from pathlib import Path


def listar_partes(carpeta):
    """Recibe una ruta y devuelve los CSV ordenados de esa carpeta."""
    return sorted(carpeta.glob('*.csv'))


def main():
    base = Path(__file__).resolve().parents[1]
    partes = listar_partes(base / 'entrada')
    print(f'Archivos encontrados: {len(partes)}')
    for parte in partes:
        print(parte.name)


# Importar esta función desde otro módulo no ejecuta main().
if __name__ == '__main__':
    main()
