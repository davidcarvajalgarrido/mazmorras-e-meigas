# Contrato del portal de invocaciones

Base local: `http://127.0.0.1:8765`. Intercambio JSON UTF-8.
Servidor preparado; el objetivo docente es consumir servicios desde Python.

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
`Content-Type: application/json`. Cuerpo (usar una fecha vigente):

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
la declaración recibida; no comprueba MeteoGalicia por su cuenta.

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
