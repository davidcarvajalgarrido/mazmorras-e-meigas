# Recorrido de la segunda aventura

## Preparación del ponente

1. Instalar requirements con el intérprete seleccionado en el editor.
2. Ejecutar `python aventura_02/ensayar.py`: final feliz y errores.
3. Abrir etapas y cliente.py; aumentar fuente y dejar visibles ambos terminales.
4. Durante la charla: servidor --demo en un terminal; cliente en otro.
5. Ensayar una petición real. Si falla la red, seleccionar --offline explícitamente.
6. Reiniciar el servidor antes de una nueva pasada para recuperar INV-001.
   Los tokens anteriores dejan de valer. El archivo de resultado se sobrescribe.

ensayar.py elige un puerto libre y cierra su servidor al terminar. Sus sesiones
son independientes del servidor manual. Las etapas usan 8765. Si está ocupado,
usar ensayar.py o --puerto/--base en el servidor/cliente completo. Para las etapas,
ajustar sus constantes antes de la clase.

## Tiempos orientativos

| Hora | Bloque | Resultado |
|---|---|---|
| 16:30–16:45 | Llegada y apertura | Entender el encargo |
| 16:45–17:20 | Contactar con otras esferas | Petición, respuesta, HTTP y recursos |
| 17:20–18:15 | Consultar el oráculo | GET, JSON y elección de franja |
| 18:15–18:40 | Descanso | Primer logro cerrado |
| 18:40–19:25 | Solicitar la invocación | Credenciales, POST, ID y GET |
| 19:25–20:10 | Cuando falla el portal | Errores y cliente completo |
| 20:10–20:30 | Cierre y preguntas | Aplicación a una tarea del público |

180 minutos de contenido, 15 de apertura, 25 de descanso y 20 de cierre.
Si las preguntas se alargan, pasar escenarios de error secundarios a reserva.

## Apertura y problema

«Ayer registramos los sucesos paranormales. Hoy estamos al otro lado del
mostrador: vamos a conocer a los responsables».

No presuponer asistencia previa: presentar en una diapositiva la Galicia
fantástica, los archivistas investigadores y los conjuradores responsables.
Encargo: elegir condiciones lluviosas y registrar una invocación.
La metáfora acompaña; los términos técnicos se explican por su nombre.

Qué: consumir servicios externos. Por qué: información y capacidades están
en otros sistemas. Para qué: tomar decisiones y encadenar acciones desde Python.
Cómo: consultar → interpretar → validar → autenticarse → crear → comprobar.

## 1. Contactar con otras esferas

Mostrar una petición/respuesta con etiquetas: base, ruta, parámetro, método,
cabeceras, cuerpo y estado. Separar HTTP de REST y JSON de HTTP.
Contrastar GET/POST; nombrar PUT/PATCH/DELETE sin construir un CRUD.
Cada API define su contrato y autenticación. Requests no interpreta por nosotros
el significado de los campos.

Pregunta: «¿Conocer la dirección de un portal significa tener permiso para entrar?»

## 2. Consultar el oráculo

Etapa 01: GET de Santiago; imprimir URL, estado y Content-Type. Explicar params,
headers, timeout y raise_for_status(). Diferenciar cuerpo como texto y json().

Etapa 02: dict → predConcello → listaPredDiaConcello → pchoiva. Mostrar tipos,
listas, campos y extracción. Validar ausencias, -9999/null, valores fuera de
rango y fechas pasadas. No confundir probabilidad de lluvia con niebla/humedad.

Regla ficticia: primera franja cronológica con probabilidad >=60. El dato lo
proporciona el servicio; la regla la decide nuestro script. Si no hay candidata,
no enviamos POST. Para completar la demo, cambiar a offline anunciándolo.
Offline: nueve franjas; mañana por la mañana, 70 %, es la primera elegible.

Antes del descanso: ya sabemos pedir información externa y utilizarla.

## 3. Solicitar la invocación

Etapa 03: clave → token. Mostrar nombres de cabecera y variables, no secretos.
--demo usa una clave pública de ejemplo. No todas las APIs intercambian keys por
tokens. Esta sesión no es OAuth ni JWT. El token caduca y vive en memoria.

Etapa 04: construir ritual y enviarlo con json=ritual. Requests serializa y
añade Content-Type. Diferenciar cuerpo de params. Mostrar 201, Location e ID.
Usar el ID para GET autenticado. Una respuesta es entrada del siguiente paso.
El POST crea en nuestra API ficticia, no altera la predicción de MeteoGalicia.

Pregunta: «Si no recibimos respuesta, ¿significa que el otro lado no hizo nada?»

## 4. Cuando falla el portal

Etapa 05: anticipar cada resultado. 401/404/422 requieren corregir algo; 503
puede ser temporal. Timeout no es un código HTTP. 200 no garantiza JSON válido
ni un contrato correcto. Usar el GET inestable con X-Ensayo nuevo: 503,503,200.

Comprobar máximo de tres intentos. No repetir POST a ciegas. Nombrar idempotencia
como ampliación sin implementarla durante la charla.

Recorrer cliente.py y ejecutar de principio a fin. Abrir resultado.json: fuente
identificada y recurso consultado, sin tokens. Repetir el POST crea otro recurso;
contrastar con regenerar archivos en la primera aventura.

## Recuperación y cierre

- Se pierde el hilo: volver al recorrido de seis pasos y señalar el actual.
- Error al escribir: abrir la etapa ya terminada y continuar.
- Falla Internet: --offline explícito, manteniendo HTTP real local.
- La clave de MeteoSIX no llega: no afecta al JSON público que usamos.
- No hay franja elegible: resultado correcto; usar ensayo sintético para continuar.
- Token inválido tras reinicio: obtener uno nuevo.
- Falta tiempo: conservar GET → JSON → autenticación → POST → GET; demostrar 401
  y 503, dejar los otros errores como material posterior.

Cerrar con: «¿Qué servicio consultaríais en vuestro trabajo? ¿Qué haríais con sus
datos? ¿Cómo comprobaríais que la operación terminó bien?».

Compartir el código y distinguir el servidor preparado del cliente que hemos
aprendido a construir. No hace falta haber asistido a la primera aventura.
