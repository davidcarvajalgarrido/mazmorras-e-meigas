# Mazmorras e Meigas

Una campaña de pequeñas aventuras de automatización con Python.

**Aventura 01: Expediente Meiga, el turno de noche.** Los archivistas de A
Irmandade do Dobre Sierpe reúnen los partes enviados por los vigías, comprueban sus
datos y preparan las prioridades de los guardianes. El código convierte ese
trabajo repetitivo en un proceso que podemos ejecutar y comprobar.

Material de David Carvajal Garrido para el seminario del CNTG del
**18 de noviembre de 2026**, «Python para automatizar tareas del día a día:
ficheros, datos y pequeños procesos».

La institución, los personajes y todos los sucesos son ficticios. La magia
es la ambientación; el proceso usa reglas explícitas y biblioteca estándar.

## Empezar

Python **3.10 o posterior**. No requiere paquetes externos ni conexión para
ejecutar el caso. Los comandos de esta guía se ejecutan desde la raíz del repositorio:

```sh
python aventura_01/procesar.py
```

Si tu intérprete se llama `python3` o utilizas `py -3`, sustituye `python`
en los ejemplos. La aplicación localiza su configuración y los datos a
partir de su propia ubicación, aunque el terminal esté en otra carpeta.

Resultado inicial: **18 registros leídos, 12 válidos, 6 rechazados y
4 prioritarios**. Se generan CSV, un resumen JSON y un log en
`aventura_01/salida/`. Los prioritarios son parte de los registros válidos.

## Qué aprenderás y dónde verlo

| Bloque del seminario | Ejemplos y código | Resultado comprobable |
|---|---|---|
| Identificar automatizaciones, estructura de scripts y reutilización | [Estructura](ejemplos/01_estructura_script.py), [reutilización](ejemplos/04_reutilizar_una_funcion.py), [reglas](reglas.py) | Una función procesa entradas distintas sin copiar su lógica |
| Ficheros, carpetas, rutas, lectura, escritura y múltiples archivos | [Rutas](etapas/etapa_01_rutas.py), [lectura CSV](etapas/etapa_02_lectura.py), `escribir_csv()` en [el proceso](procesar.py) | Tres archivos de entrada y salidas generadas en otra carpeta |
| CSV, JSON, extracción, transformación y validación | [Antes/después](ejemplos/02_extraer_transformar_validar.py), [validación](etapas/etapa_03_validacion.py), [JSON](ejemplos/03_json_y_cambio_de_regla.py) | Texto convertido a entero, datos rechazados y prioridad configurable |
| Tareas encadenadas, errores y logs | [Encadenar funciones](etapas/etapa_05_prioridades.py), `main()` y `procesar()` en [el proceso](procesar.py) | Entradas y salidas entre funciones, errores con distinta consecuencia y diario de ejecución |
| Proceso completo de principio a fin | [Solución completa](procesar.py), [último aviso](reserva/04_ultimo_aviso.csv) | Incorporar otro archivo y repetir sin modificar el programa |

El desarrollo de cada requisito y las comprobaciones están en
[Temario y evidencias](../docs/aventura_01/temario.md). El [recorrido de la aventura](../docs/aventura_01/recorrido.md)
propone el orden de ejecución y preguntas para anticipar resultados.

## Estructura

- `aventura_01/entrada/`: tres CSV ficticios del lote inicial.
- `aventura_01/etapas/`: cinco pasos ejecutables para seguir el desarrollo.
- `aventura_01/ejemplos/`: ejemplos pequeños de conceptos específicos.
- `aventura_01/reglas.py`: función de validación compartida.
- `aventura_01/procesar.py`: solución completa del caso.
- `aventura_01/config.json`: configuración inicial, umbral 4.
- `aventura_01/config_riesgo_5.json`: configuración alternativa, con salida separada.
- `aventura_01/reserva/`: un nuevo aviso para el cierre.
- `aventura_01/escenarios/`: errores preparados para experimentar.
- `tests/`: pruebas con copias temporales; no alteran la entrada original.

## Ejecutar por etapas

```sh
python aventura_01/etapas/etapa_01_rutas.py
python aventura_01/etapas/etapa_02_lectura.py
python aventura_01/etapas/etapa_03_validacion.py
python aventura_01/etapas/etapa_04_configuracion.py
python aventura_01/etapas/etapa_05_prioridades.py
python aventura_01/procesar.py
```

Las etapas muestran **avances parciales**. La 03 obtiene 13 válidos y
5 rechazos porque todavía admite un reenvío. La 04 imprime 5 prioridades,
incluyendo ese duplicado. La 05 y el proceso final añaden la deduplicación:
**12 válidos, 6 rechazos y 4 prioridades**. No son resultados contradictorios:
en cada paso incorporamos una regla que antes no existía.

## Ejemplos breves

```sh
python aventura_01/ejemplos/01_estructura_script.py
python aventura_01/ejemplos/02_extraer_transformar_validar.py
python aventura_01/ejemplos/03_json_y_cambio_de_regla.py
python aventura_01/ejemplos/04_reutilizar_una_funcion.py
```

El segundo distingue extracción, transformación y validación. El tercero
compara umbrales 4 y 5 y escribe `salida_ejemplos/comparacion_umbrales.json`.
El cuarto utiliza la misma función `validar()` con un diccionario que no
procede de un CSV.

## Cambiar una regla mediante JSON

```sh
python aventura_01/procesar.py --config aventura_01/config_riesgo_5.json
```

Con los datos iniciales, el umbral 5 deja **2 prioridades**. Los válidos y
rechazados siguen siendo 12 y 6: prioridad y validez son decisiones distintas.
Los resultados alternativos van a `salida_riesgo_5/`, separada de la salida inicial.
Las rutas que contiene un JSON son relativas al propio archivo JSON.

## El último mensajero

Copia `aventura_01/reserva/04_ultimo_aviso.csv` a `aventura_01/entrada/`
y vuelve a ejecutar el proceso. Resultado: **19 leídos, 13 válidos,
6 rechazados y 5 prioritarios**. Repite: los recuentos se mantienen.
Para restaurar la situación inicial, retira solo esa copia de `entrada/`.

## Pruebas

```sh
python -m unittest discover -s tests/aventura_01 -t . -v
```

Las pruebas ejecutan el caso en copias temporales, incluyendo otra carpeta
de trabajo, un archivo defectuoso, JSON incorrecto, salidas vacías y el aviso final.

## Reglas y límites del ejemplo

Todos los campos del caso son obligatorios. El CSV usa coma, cabecera fija
y UTF-8 con o sin BOM. Fecha válida AAAA-MM-DD, riesgo entero 1–5 y fenómeno
del catálogo. Identificador repetido: se conserva el primer registro válido
por orden de archivo. No se deduplican sucesos parecidos con IDs distintos.

Una fila inválida se aparta y queda explicada. Un archivo ilegible o con
cabecera incorrecta se omite entero y el lote queda parcial. Configuración
inválida o carpeta sin CSV: se detiene sin generar resultados nuevos.

Códigos de salida: **0 completo**, aunque haya filas rechazadas; **2 parcial**
por archivos omitidos; **1 fallo global**. Si falla una ejecución, las salidas
de una ejecución anterior no deben interpretarse como resultados actuales.

Los CSV y el resumen se regeneran; el log conserva el historial. La escritura
sustituye cada archivo mediante un temporal, pero no hace una transacción
de todo el lote. El ejemplo está pensado para archivos pequeños y ejecución
individual, no para procesos simultáneos ni grandes volúmenes. Los originales
no se modifican. Las salidas y logs habituales quedan excluidos del control de versiones.

## Referencias

- [pathlib](https://docs.python.org/3/library/pathlib.html)
- [csv](https://docs.python.org/3/library/csv.html)
- [json](https://docs.python.org/3/library/json.html)
- [datetime](https://docs.python.org/3/library/datetime.html)
- [logging](https://docs.python.org/3/library/logging.html)
- [argparse](https://docs.python.org/3/library/argparse.html)

La [segunda aventura](../aventura_02/README.md) continúa la campaña con APIs.
