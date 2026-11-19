# Mazmorras e Meigas · Aventura 02

## O pacto da brétema

Ayer los archivistas investigaban los sucesos. Hoy los conjuradores quieren
provocarlos: consultan las condiciones meteorológicas, eligen un ritual y
solicitan una invocación a otra esfera.

Material para el seminario **APIs con Python: cómo consumir servicios web y
trabajar con datos externos**, CNTG, 19 de noviembre de 2026.

La criatura `espiritu_da_bretema`, el ritual y sus reglas son ficción propia;
no se presentan como tradición mitológica documentada. La probabilidad de
lluvia es un dato real cuando procede del servicio público. No equivale a
humedad, niebla ni lluvia garantizada. El script no altera el tiempo real.

## Preparación

Python **3.10 o posterior**. Dependencias externas: **requests** y
**python-dotenv**.
Se recomienda un entorno virtual seleccionado también en el editor.
Desde la raíz del repositorio instala las dependencias con el intérprete elegido:

```sh
python -m pip install -r aventura_02/requirements.txt
```

Usa `python3` o `py -3` si así se llama tu intérprete. El resto del servidor
usa biblioteca estándar. Para el servicio JSON municipal y el ensayo offline
no necesitas una clave de MeteoSIX. El modo MeteoSIX usa una clave gratuita
solicitada a MeteoGalicia.

## Preparar las claves

Copia `aventura_02/.env.example` a `aventura_02/.env` y sustituye los valores:

```sh
cp -n aventura_02/.env.example aventura_02/.env
```

Si ya existe `aventura_02/.env`, añade o actualiza allí las variables; no lo
sobrescribas con la plantilla.

`CONJURO_API_KEY` es solo para nuestra API ficticia. `METEOSIX_API_KEY` es
solo para MeteoSIX; la clave oficial es gratuita y se solicita a MeteoGalicia.
El cliente y el servidor cargan explícitamente ese `.env` desde la carpeta
`aventura_02/`, incluso si ejecutas el script desde otra ubicación. Las
variables ya definidas en el entorno tienen prioridad. El `.env` real está
ignorado por Git; no compartas ni publiques sus valores.

## Primero: ensayo en una terminal

```sh
python aventura_02/ensayar.py
```

Arranca un servidor temporal sobre loopback y un puerto libre, ejecuta el
cliente completo, recorre los errores y cierra el servidor. La meteorología
es **sintética y está identificada como ensayo**. Se hacen peticiones HTTP
reales entre procesos locales. Después de instalar requests, no requiere red.

Resultado esperado: 9 franjas disponibles, primera elegible mañana por la
mañana con 70 % de probabilidad; autenticación correcta; `INV-001` registrada;
resultado en `aventura_02/salida/resultado.json`. El laboratorio muestra
401, 404, 422, JSON roto, estructura inesperada, timeout y recuperación tras
dos 503. No deben aparecer tokens ni claves en la salida.

Las fechas sintéticas se generan respecto al día de ejecución. Este ejemplo
elige por fecha y franja, sin calcular la hora exacta de comienzo de cada franja.

## Durante la charla: dos terminales

Terminal 1, que permanece abierto:

```sh
python aventura_02/servidor.py --demo
```

Terminal 2, ensayo completo con datos sintéticos:

```sh
python aventura_02/cliente.py --offline --demo
```

Consulta al JSON público de MeteoGalicia y creación en nuestra API local:

```sh
python aventura_02/cliente.py --demo
```

La selección explícita equivalente es:

```sh
python aventura_02/cliente.py --fuente meteogalicia --demo
```

Consulta autenticada a MeteoSIX v5.1 y creación en nuestra API local:

```sh
python aventura_02/cliente.py --fuente meteosix --demo
```

`--demo` selecciona la clave pública de ejemplo **solo para la API ficticia**;
no sustituye la clave MeteoSIX. La fuente meteorológica predeterminada sigue
siendo el JSON público por municipio. `--fuente meteogalicia` la selecciona
explícitamente y `--offline` conserva la predicción sintética local. `--offline`
y `--fuente` son alternativas mutuamente excluyentes. MeteoSIX pide
`METEOSIX_API_KEY`; la API key se envía en el parámetro `API_KEY` de la
petición HTTPS y nunca se imprime.

Puedes seleccionar otro municipio del JSON con `--municipio 15037` (Fisterra)
o `--municipio 15030` (A Coruña). Para MeteoSIX, usa coordenadas
`--lon -8.5448 --lat 42.8782` y cambia el nombre mostrado con
`--ubicacion "Santiago de Compostela"`. Coordenadas de ejemplo para otra
ubicación:

```sh
python aventura_02/cliente.py --fuente meteosix --demo \
  --ubicacion "A Coruña" --lon -8.4115 --lat 43.3623
```

La respuesta del servicio público o de MeteoSIX puede no contener datos
vigentes o ninguna franja elegible. En ese caso no se solicita una invocación.
El modo live no cambia automáticamente a datos sintéticos.

## Seis pasos cortos para live coding

Con el servidor local --demo abierto:

```sh
python aventura_02/etapas/01_consultar_oraculo.py --offline
python aventura_02/etapas/02_descifrar_json.py --offline
python aventura_02/etapas/03_presentar_credenciales.py --demo
python aventura_02/etapas/04_solicitar_invocacion.py
python aventura_02/etapas/05_cuando_falla_el_portal.py
python aventura_02/etapas/06_consultar_meteosix.py
```

Los pasos 01 y 02 consultan MeteoGalicia si omites `--offline`. Los pasos 03 y
04 son independientes: cada uno obtiene un token nuevo. El paso 04 siempre
usa la clave pública y datos sintéticos. El paso 06 muestra la consulta
autenticada MeteoSIX, sin imprimir la clave. Para continuar desde esa consulta
hasta la invocación completa, ejecuta en el otro terminal:

```sh
python aventura_02/cliente.py --fuente meteosix --demo
```

Los ejemplos cortos dejan visibles las excepciones para explicarlas; el cliente
completo ofrece mensajes finales.

## Qué aprendemos y dónde

| Contenido del contrato | Código y evidencia |
|---|---|
| REST, HTTP, recursos, endpoints y métodos | [Contrato de la API](../docs/aventura_02/contrato_api.md): recursos `/invocaciones/{id}`, GET y POST; comparación conceptual con PUT, PATCH y DELETE |
| GET, POST, parámetros, cabeceras y librerías | [Etapas](etapas/), `requests.get`, `params`, `headers`, `requests.post(..., json=...)`; la etapa 06 muestra `API_KEY` en los parámetros de MeteoSIX |
| JSON, conversión y extracción | `respuesta.json()`, `extraer_franjas()` y etapa 02: diccionario → objeto anidado → lista → campos |
| API keys, tokens y credenciales | Etapas 03–04: X-API-Key → token opaco temporal → Authorization: Bearer; variables de entorno, sin imprimir secretos |
| HTTP, excepciones, reintentos y validación | Etapa 05 y `obtener_json()`: 401/404/422/503, timeout, JSON inválido, datos no válidos y GET con reintentos acotados |
| Caso práctico completo | [cliente.py](cliente.py): predicción → criterio → autenticación → creación → consulta → resultado JSON |

HTTP es el protocolo; REST es un estilo de arquitectura. Un servicio HTTP que
intercambia JSON no es automáticamente REST. GET consulta; POST procesa o crea
según el contrato, no significa universalmente «crear». PUT sustituye una
representación, PATCH aplica cambios parciales y DELETE solicita eliminar un
recurso. Nuestra demo implementa GET y POST; no construye un CRUD completo.

## Credenciales y límites de la API didáctica

En modo normal cliente y servidor leen `CONJURO_API_KEY` del entorno; se usa
solo en el intercambio con nuestra API ficticia. La petición MeteoSIX usa
`METEOSIX_API_KEY`, separada, y la requiere únicamente al seleccionar esa
fuente. `aventura_02/.env` se carga explícitamente con ruta anclada al archivo
y sin sobrescribir variables de entorno. No subas `.env`, claves reales,
tokens ni capturas de cabeceras al repositorio.

La API actual de MeteoSIX es la v5.1 (`/apiv5/getNumericForecastInfo`).
Consulta por coordenadas `longitud,latitud`. El modelo de respuesta GeoJSON
contiene `features[].properties.days[].variables[]`; cada variable tiene
`name`, `units` y `values[]`, con `timeInstant` y `value`. Para
`precipitation_amount`, la unidad oficial es `lm2` (litros por metro cuadrado,
equivalente a mm) y el valor es precipitación acumulada durante la hora
anterior. No se convierte a porcentaje ni se envía `probabilidad_lluvia`.
El ritual MeteoSIX usa una regla separada: una franja es elegible si al menos
una hora en esa franja tiene `precipitation_amount > 0 lm2`. La regla original
`pchoiva >= 60 %` sigue intacta para el JSON municipal y el ensayo offline.

El token es opaco, caduca a los 900 segundos y solo vale mientras vive el
servidor. No es un JWT ni un flujo OAuth; el intercambio API key → token es
el contrato particular de esta demo, no una regla universal de las APIs.
Reiniciar el servidor elimina tokens, invocaciones y contadores del laboratorio.
Cada POST válido crea una invocación nueva: repetirlo puede duplicarla.

El servidor escucha exclusivamente en 127.0.0.1. El HTTP sin TLS se limita a
este ensayo local. En un servicio remoto se debe usar HTTPS. Nuestra API no
comprueba MeteoGalicia ni MeteoSIX por su cuenta: valida los campos, la fuente,
la variable, la unidad y el criterio del ritual declarados por el cliente. No
garantiza que las condiciones meteorológicas sean verdaderas. No es un servicio
preparado para publicación en producción.

## Estructura y pruebas

- `aventura_02/servidor.py`: API local ya preparada para la clase.
- `aventura_02/cliente.py`: solución completa para consumir los servicios.
- `aventura_02/etapas/`: etapas para el live coding.
- `aventura_02/etapas/06_consultar_meteosix.py`: consulta autenticada a MeteoSIX.
- `aventura_02/ensayar.py`: comprobación completa en una terminal.
- `docs/aventura_02/recorrido.md`: secuencia, tiempos, preguntas y recuperación.
- `docs/aventura_02/contrato_api.md`: ejemplos de peticiones, respuestas y códigos.
- `tests/aventura_02/`: pruebas sobre HTTP local; no consultan Internet.

```sh
python -m unittest discover -s tests/aventura_02 -t . -v
```

Esta aventura forma parte del mismo repositorio que la primera. Los comandos
se ejecutan desde la raíz de la campaña. La documentación está en
`docs/aventura_02/` y las pruebas en `tests/aventura_02/`.
Volver al [índice de la campaña](../README.md).

## Fuentes

- [Servicio JSON por municipio y estructura](https://www.meteogalicia.gal/datosred/infoweb/meteo/docs/rss/JSON_Pred_Concello_es.pdf)
- [Petición pública de Santiago](https://servizos.meteogalicia.gal/mgrss/predicion/jsonPredConcellos.action?idConc=15078)
- [Información oficial de MeteoSIX y obtención de clave](https://www.meteogalicia.gal/web/modelos-numericos/meteosix)
- [Manual oficial de MeteoSIX v5.1, actualizado en octubre de 2026](https://meteo-estaticos.xunta.gal/datosred/infoweb/meteo/proxectos/meteosix/API_MeteoSIX_v5.1_gl.pdf)
- [Documentación oficial de Requests](https://requests.readthedocs.io/en/latest/user/quickstart/)
- [Biblioteca estándar urllib.request](https://docs.python.org/3/library/urllib.request.html)
- [Documentación oficial de HTTPX](https://www.python-httpx.org/)

El parámetro usado en el ejemplo oficial del JSON municipal es `idConc`. El documento contiene
una referencia textual a `idConcello`; seguimos la URL de ejemplo y el endpoint
comprobado. El JSON incluye una envoltura `predConcello`. Valores `-9999` y
`null` no se tratan como predicciones válidas. Se descartan fechas pasadas.
Los datos de MeteoGalicia se atribuyen a MeteoGalicia; los de ensayo son propios.
