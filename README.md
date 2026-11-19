# Mazmorras e Meigas

Una campaña de dos aventuras prácticas con Python, ambientadas en una Galicia
fantástica. Material de David Carvajal Garrido para los seminarios del CNTG
los días 18 y 19 de noviembre de 2026.

## Elige tu aventura

| Aventura | Seminario | Material |
|---|---|---|
| **01 · Expediente Meiga: el turno de noche** | Automatización, ficheros, CSV/JSON, validación, errores y logs | [Instrucciones y ejemplos](aventura_01/README.md) · [Recorrido](docs/aventura_01/recorrido.md) · [Temario](docs/aventura_01/temario.md) |
| **02 · O pacto da brétema** | Consumo de APIs, HTTP, JSON, autenticación, errores y reintentos | [Instrucciones y ejemplos](aventura_02/README.md) · [Recorrido](docs/aventura_02/recorrido.md) · [Contrato de la API](docs/aventura_02/contrato_api.md) |

Los archivistas reúnen y verifican los avisos. Los conjuradores consultan otras
esferas y solicitan invocaciones. Las dos aventuras se pueden seguir de forma
independiente; la institución, los personajes y los rituales son ficticios.

## Empezar

Python **3.10 o posterior**. Todos los comandos se ejecutan desde la raíz del
repositorio. Si tu intérprete se llama python3 o py -3, adapta el ejecutable.

**Primera aventura:** sin dependencias externas ni conexión.

```sh
python aventura_01/procesar.py
```

Resultado inicial esperado: 18 registros leídos, 12 válidos, 6 rechazados y
4 prioritarios. Los originales de entrada no se modifican.

**Segunda aventura:** instalar Requests y python-dotenv y ejecutar el ensayo completo.

```sh
python -m pip install -r aventura_02/requirements.txt
python aventura_02/ensayar.py
```

El ensayo utiliza HTTP local, datos meteorológicos sintéticos identificados y
una credencial pública de ejemplo. Arranca y cierra su servidor automáticamente.
Después de instalar las dependencias, no requiere Internet. Para el JSON
municipal público, MeteoSIX autenticado o la demo por etapas, consulta las
instrucciones de la aventura 02.

## Organización

- `aventura_01/` y `aventura_02/`: código e instrucciones de cada aventura.
- `docs/aventura_01/` y `docs/aventura_02/`: guías separadas.
- `tests/aventura_01/` y `tests/aventura_02/`: pruebas separadas.
- Las dependencias de APIs están en `aventura_02/requirements.txt`.

Se conservan las salidas de la primera aventura incluidas en el material original;
son ejemplos ya generados. Al ejecutar el proceso, los CSV y el resumen se
regeneran y el log conserva historial. Las salidas de la segunda no se distribuyen.

## Pruebas

Todas (con las dependencias de aventura_02 instaladas):

```sh
python -m unittest discover -s tests -t . -v
```

Solo la primera, sin instalar dependencias:

```sh
python -m unittest discover -s tests/aventura_01 -t . -v
```

Solo la segunda (requiere Requests y python-dotenv):

```sh
python -m unittest discover -s tests/aventura_02 -t . -v
```

Mantén `-t .` para descubrir los paquetes de pruebas desde la raíz y evitar
confundir sus nombres con las carpetas de código. Las pruebas de la primera
trabajan sobre copias temporales; las de la segunda usan un servidor HTTP local
en un puerto libre. Ninguna suite consulta MeteoGalicia.

## Credenciales y datos

La clave de demostración es deliberadamente pública y solo se usa con el
servidor local preparado. No subas credenciales reales ni tokens. La plantilla
está en `aventura_02/.env.example`; cliente y servidor cargan
`aventura_02/.env` explícitamente.

La probabilidad de lluvia de MeteoGalicia no garantiza niebla ni lluvia. El
ritual utiliza una regla ficticia. Los fallos preparados se ejecutan únicamente
contra nuestra API local, no contra servicios públicos.
