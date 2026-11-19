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

Python **3.10 o posterior**. Una dependencia externa: **requests**.
Se recomienda un entorno virtual seleccionado también en el editor.
Desde la raíz del repositorio instala las dependencias con el intérprete elegido:

```sh
python -m pip install -r aventura_02/requirements.txt
```

Usa `python3` o `py -3` si así se llama tu intérprete. El resto del servidor
usa biblioteca estándar. No necesitas una clave de MeteoSIX, una cuenta,
Docker ni desplegar nada en Internet.

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

Consulta real a MeteoGalicia y creación en nuestra API local:

```sh
python aventura_02/cliente.py --demo
```

`--demo` elige una **clave pública de ejemplo**; `--offline` cambia la fuente
meteorológica al servicio sintético local. Son opciones independientes.
El servidor necesita `--demo` para ofrecer meteorología sintética y escenarios
de error. La respuesta de MeteoGalicia puede variar, no contener condiciones
adecuadas o no contener días vigentes. Eso no es un fallo del script: si no
hay franja adecuada, no solicita una invocación. Nunca sustituye silenciosamente
los datos reales por datos inventados.

Puedes seleccionar otro municipio con `--municipio 15037` (Fisterra) o
`--municipio 15030` (A Coruña). En el modo real solo se consultan endpoints GET
de MeteoGalicia; las peticiones POST se envían exclusivamente a nuestra API.

## Cinco pasos cortos para live coding

Con el servidor local --demo abierto:

```sh
python aventura_02/etapas/01_consultar_oraculo.py --offline
python aventura_02/etapas/02_descifrar_json.py --offline
python aventura_02/etapas/03_presentar_credenciales.py --demo
python aventura_02/etapas/04_solicitar_invocacion.py
python aventura_02/etapas/05_cuando_falla_el_portal.py
```

Los pasos 01 y 02 consultan MeteoGalicia si omites `--offline`. Los pasos 03 y
04 son independientes: cada uno obtiene un token nuevo. El paso 04 siempre
usa la clave pública y datos sintéticos. Los ejemplos cortos dejan visibles
las excepciones para explicarlas; el cliente completo ofrece mensajes finales.

## Qué aprendemos y dónde

| Contenido del contrato | Código y evidencia |
|---|---|
| REST, HTTP, recursos, endpoints y métodos | [Contrato de la API](../docs/aventura_02/contrato_api.md): recursos `/invocaciones/{id}`, GET y POST; comparación conceptual con PUT, PATCH y DELETE |
| GET, POST, parámetros, cabeceras y librerías | [Etapas](etapas/), `requests.get`, `params`, `headers`, `requests.post(..., json=...)`; urllib y HTTPX como alternativas explicadas en el guion |
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

En modo normal cliente y servidor leen `CONJURO_API_KEY` del entorno.
`.env.example` es una plantilla: **no se carga automáticamente**. Configura
la variable en el terminal o en el editor para ambos procesos. No subas `.env`,
claves reales, tokens ni capturas de cabeceras al repositorio.

El token es opaco, caduca a los 900 segundos y solo vale mientras vive el
servidor. No es un JWT ni un flujo OAuth; el intercambio API key → token es
el contrato particular de esta demo, no una regla universal de las APIs.
Reiniciar el servidor elimina tokens, invocaciones y contadores del laboratorio.
Cada POST válido crea una invocación nueva: repetirlo puede duplicarla.

El servidor escucha exclusivamente en 127.0.0.1. El HTTP sin TLS se limita a
este ensayo local. En un servicio remoto se debe usar HTTPS. Nuestra API no
comprueba MeteoGalicia por su cuenta: valida los campos y la regla del ritual
que declara el cliente. No garantiza que las condiciones meteorológicas sean
verdaderas. No es un servicio preparado para publicación en producción.

## Estructura y pruebas

- `aventura_02/servidor.py`: API local ya preparada para la clase.
- `aventura_02/cliente.py`: solución completa para consumir los servicios.
- `aventura_02/etapas/`: cinco puntos de partida o recuperación del live coding.
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
- [Documentación oficial de Requests](https://requests.readthedocs.io/en/latest/user/quickstart/)
- [Biblioteca estándar urllib.request](https://docs.python.org/3/library/urllib.request.html)
- [Documentación oficial de HTTPX](https://www.python-httpx.org/)

El parámetro usado en el ejemplo oficial es `idConc`. El documento contiene
una referencia textual a `idConcello`; seguimos la URL de ejemplo y el endpoint
comprobado. El JSON incluye una envoltura `predConcello`. Valores `-9999` y
`null` no se tratan como predicciones válidas. Se descartan fechas pasadas.
Los datos de MeteoGalicia se atribuyen a MeteoGalicia; los de ensayo son propios.
