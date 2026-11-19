# Contrato del portal de invocaciones

Base local: `http://127.0.0.1:8765`. Intercambio JSON UTF-8.
Servidor preparado; el objetivo docente es consumir servicios desde Python.

## Fuentes meteorológicas

Ejecuta estos comandos desde la raíz del repositorio con el servidor local
`python aventura_02/servidor.py --demo` abierto en la primera terminal:

```sh
python aventura_02/cliente.py --demo
python aventura_02/cliente.py --fuente meteogalicia --demo
python aventura_02/cliente.py --fuente meteosix --demo
python aventura_02/cliente.py --offline --demo
```

Sin `--fuente`, se conserva el JSON público municipal de MeteoGalicia.
`--offline` consulta la predicción sintética del servidor local y no se combina
con `--fuente`.

### MeteoSIX v5.1

Según el [manual oficial v5.1](https://meteo-estaticos.xunta.gal/datosred/infoweb/meteo/proxectos/meteosix/API_MeteoSIX_v5.1_gl.pdf),
publicado en octubre de 2026, la consulta es un GET HTTPS a
`https://servizos.meteogalicia.gal/apiv5/getNumericForecastInfo`.
`API_KEY` es obligatorio y se envía como parámetro; `coords` es
`longitud,latitud`. Se solicitan `variables=precipitation_amount`,
`units=lm2`, `format=application/json`, `lang=gl` y `tz=Europe/Madrid`.
Las coordenadas predeterminadas son las de Santiago de Compostela; `--lon`,
`--lat` y `--ubicacion` permiten cambiarlas.

El JSON es GeoJSON: `features[].properties.days[]` contiene periodos y una
lista `variables[]`; la variable tiene `name`, `units` y `values[]`, cuyos
elementos incluyen `timeInstant`, `modelRun` y `value`. Para
`precipitation_amount`, el manual define precipitación acumulada durante la
hora anterior y unidad `lm2` (l/m2, equivalente a mm). El manual no ofrece una
variable de probabilidad de lluvia. Los valores ausentes (`null`) se omiten;
un cuerpo de error de MeteoSIX puede ser HTTP 200 con `exception`, por lo que
también se valida el JSON y no solo el estado HTTP.

La regla original de MeteoGalicia municipal y offline permanece:
`pchoiva >= 60 %`. Para MeteoSIX se agrupan los valores horarios en mañana
(06:00–11:59), tarde (12:00–17:59) y noche (18:00–23:59), hora local de
Europe/Madrid; la primera franja cronológica con `precipitation_amount > 0 lm2`
es elegible. No se inventan porcentajes ni se llena `probabilidad_lluvia`.

La invocación declara `fuente_meteorologica`, `variable_meteorologica`,
`unidad_meteorologica` y `criterio_ritual`; el campo numérico depende de la
fuente (`probabilidad_lluvia` o `precipitacion_lm2`). Para MeteoSIX se incluyen
también `coordenadas` en el ritual. La API local valida los metadatos y el
criterio correspondiente.

## Presentar credenciales

`POST /sesiones`, cabecera `X-API-Key: <clave>`; sin cuerpo.
Respuesta **201**:

```json
{"access_token": "<token-opaco>", "token_type": "Bearer", "expires_in": 900}
```

Clave incorrecta o ausente: **401**. Nunca se imprime el token ni se guarda.
Es un contrato didáctico particular; no es JWT ni un flujo OAuth.

## Solicitar la invocación

`POST /invocaciones` con `Authorization: Bearer <token>` y
`Content-Type: application/json`. Cuerpo con datos del JSON municipal u
offline (usar una fecha vigente):

```json
{
  "criatura": "espiritu_da_bretema",
  "municipio_id": 15078,
  "municipio": "Santiago de Compostela",
  "fecha": "2026-11-20",
  "franja": "manha",
  "probabilidad_lluvia": 70
}
```

Fecha de hoy o posterior, franja manha/tarde/noite, probabilidad numérica
60–100, identificador entero positivo y nombre no vacío. El servidor valida
la declaración recibida; no comprueba MeteoGalicia por su cuenta. En MeteoSIX
no se envía `municipio_id` ni `probabilidad_lluvia`; el campo
`precipitacion_lm2` debe ser positivo, con variable `precipitation_amount`,
unidad `lm2` y el criterio documentado arriba.

Respuesta **201**: campos recibidos más `id: "INV-001"` y
`estado: "registrada"`. Cabecera `Location: /invocaciones/INV-001`.
Registrada significa recurso creado, no invocación real ni trabajo asíncrono.

## Consultar la invocación

`GET /invocaciones/INV-001`, con `Authorization: Bearer <token>`.
Respuesta **200** con el recurso; ID desconocido: **404**.

| Estado | Significado en la demo | Decisión |
|---|---|---|
| 200 | Consulta correcta | Interpretar y validar el cuerpo |
| 201 | Sesión o invocación creada | Recuperar token o ID |
| 400 | Cuerpo JSON incorrecto | Corregir serialización/cuerpo |
| 401 | Credencial incorrecta o caducada | Revisar autenticación |
| 404 | Recurso inexistente | Revisar ruta o ID |
| 415 | Content-Type incorrecto | Usar json=... en Requests |
| 422 | Campos incumplen reglas | Corregir los datos |
| 503 | Servicio temporalmente indisponible | GET: reintento limitado |

HTTPError, Timeout, ConnectionError y JSONDecodeError son problemas distintos.
Un 200 puede contener JSON roto o datos que no sirven. raise_for_status()
comprueba estados 4xx/5xx; json() interpreta; la validación comprueba el contrato.

## Escenarios exclusivos de --demo

| GET | Respuesta |
|---|---|
| /salud | Estado del servidor |
| /meteo/prediccion?idConc=15078 | Datos sintéticos con fechas relativas a hoy |
| /laboratorio/inestable | Dos 503 y después 200 por cada cabecera X-Ensayo distinta |
| /laboratorio/lento | Espera 0,3 s; usar timeout 0,05 para provocar Timeout |
| /laboratorio/json-roto | 200 con JSON inválido |
| /laboratorio/datos-incompletos | 200 con JSON válido de estructura inesperada |

No se provocan fallos ni cargas de prueba contra MeteoGalicia.

## Reintentos y límites

obtener_json() hace como máximo tres intentos, SOLO GET. Reintenta conexión,
timeout y estados 429/502/503/504. Retry-After numérico se limita a dos segundos;
no implementa Retry-After en forma de fecha HTTP. No reintenta los demás 4xx,
JSON roto ni errores de validación. Los timeouts de Requests limitan conexión
/esperas de lectura, no son un límite total del proceso.

POST nunca se repite automáticamente. Tras un timeout puede haberse creado el
recurso. Una API real puede ofrecer claves de idempotencia para resolverlo;
esta no las implementa: dos POST válidos crean dos invocaciones.

Servidor local en memoria, sin despliegue de producción. Reiniciarlo elimina
sesiones, recursos y contadores. Escucha únicamente en loopback; usar HTTPS
para servicios remotos con credenciales.

## Bibliotecas y métodos que se presentan

Requests sostiene los ejemplos síncronos. urllib.request es la alternativa de
biblioteca estándar; HTTPX ofrece interfaces síncronas y asíncronas. No se
instalan más dependencias ni se introduce asincronía en el caso.

HTTP es el protocolo; REST es un estilo arquitectónico. Intercambiar JSON por
HTTP no convierte automáticamente un servicio en REST. GET consulta; POST
procesa o crea según el contrato; PUT sustituye una representación; PATCH
aplica cambios parciales; DELETE solicita eliminar un recurso. La demo solo
implementa GET y POST.
