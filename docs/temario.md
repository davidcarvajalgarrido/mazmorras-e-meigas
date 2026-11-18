# Temario y evidencias de aprendizaje

Correspondencia entre los cinco bloques del seminario y los ejemplos de la aventura 01.
Ejecutar desde la raíz del repositorio. Solo se necesita Python 3.10 o posterior.

## 1. Automatización con Python

**Tareas susceptibles de automatización, estructura básica de un script y reutilización del código.**

La tarea manual consiste en abrir cada parte, copiar registros, revisar valores,
detectar reenvíos y ordenar prioridades. Se repite y tiene reglas comprobables.
El script conserva la revisión humana para los datos rechazados.

- Ejecutar `aventura_01/ejemplos/01_estructura_script.py`: importaciones,
  función con parámetro, `main()` y guardia `if __name__ == '__main__'`.
- Ejecutar `aventura_01/ejemplos/04_reutilizar_una_funcion.py`: importar y usar
  `validar()` con un registro creado en memoria. Las etapas 03/04, la etapa 05
  y la solución comparten la misma definición en `reglas.py`.
- Comprobar: la regla limpia Betanzos y convierte el riesgo a entero sin copiar la función.

**Pregunta:** ¿qué parte del proceso merece automatizarse y qué dato requiere revisión humana?

## 2. Ficheros y directorios

**Lectura, escritura, carpetas, rutas y procesamiento de múltiples archivos.**

- Etapa 01: rutas ancladas al script, carpeta actual, `glob('*.csv')` y bucle.
- Etapa 02: apertura con `with`, codificación, CSV con cabecera y 18 registros.
- Solución completa: `mkdir`, `DictWriter`, cabeceras y resultados en otra carpeta.
- Comprobar: ejecutar desde otra carpeta sigue encontrando los mismos datos.

**Pregunta:** ¿qué cambia si llega un cuarto CSV y qué parte del programa permanece igual?

## 3. Tratamiento básico de datos

**CSV, JSON, extracción, transformación y validación.**

- Ejemplo 02: extraer campos, quitar espacios y convertir `'  5  '` a `5`.
- Etapa 03: comprobar campos, fecha, catálogo y rango. El texto `muchísimo`
  no se puede convertir a entero; `9` sí se convierte, pero no es un riesgo permitido.
- Etapa 05: conjunto de IDs, selección por umbral y orden de prioridades.
- Ejemplo 03: leer JSON, comparar umbrales y generar una salida JSON.
- Configuración alternativa: ejecutar con `--config aventura_01/config_riesgo_5.json`.
  Los datos iniciales dejan 2 prioridades frente a 4. La validez no cambia.

**Pregunta:** ¿por qué leer un registro correctamente no demuestra que sea válido?

## 4. Automatización de procesos

**Tareas encadenadas, gestión básica de errores y logs.**

La etapa 05 encadena funciones del programa final sin escribir sus salidas.
En `procesar.py`, `main()` coordina el proceso completo:

| Operación | Recibe | Devuelve o produce |
|---|---|---|
| `cargar_configuracion()` | Ruta del JSON | Configuración y carpetas |
| Búsqueda de archivos | Carpeta de entrada | Lista ordenada de CSV |
| `leer_archivo()` | Una ruta CSV | Filas como diccionarios |
| `validar()` | Fila y catálogo | Registro limpio o excepción |
| `procesar()` | Archivos y configuración | Válidos, rechazos y errores de archivo |
| `guardar_resultados()` | Datos procesados y configuración | CSV y resumen JSON |
| `logging` | Mensajes durante el proceso | Consola y diario del turno |

Copiar `escenarios/99_cabecera_incorrecta.csv` a entrada permite observar
un lote parcial, un archivo omitido y código 2. El resto del lote se procesa.
Retirar esa copia después. Un JSON incorrecto produce código 1.

Abrir `salida/turno_de_noche.log`: localizar INICIO, registros rechazados y FIN.
Las excepciones tienen distinta consecuencia según lo que ha fallado.

**Pregunta:** ¿cuándo continuar con el resto y cuándo detener todo el proceso?

## 5. Caso práctico completo

**Construcción de un pequeño proceso de automatización de principio a fin.**

Ejecutar las etapas, después `procesar.py`, abrir los resultados y comprobar
los recuentos. Copiar el último aviso de reserva, ejecutar de nuevo y comprobar
19/13/6/5. Repetir sin añadir datos: los CSV no acumulan copias.

**Comprobación final:** poder explicar qué entra, qué reglas se aplican, qué
sale y cómo sabemos que ha funcionado. Adaptar una regla o un origen de datos
sin reconstruir el programa entero.
