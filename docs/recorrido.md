# Recorrido de la primera guardia

## Antes de la demostración

En `aventura_01/entrada/` deben estar solo los tres CSV iniciales. El último aviso
y el archivo con cabecera defectuosa esperan fuera, en reserva y escenarios.
Los ejemplos no requieren instalar paquetes. Abrir el proyecto en el editor
y comprobar el intérprete disponible en ese equipo.

## Primer bloque: el encargo

Presentar la hermandad, el papel de los archivistas y los pasos manuales.
Identificar entradas, reglas, salidas y cómo comprobarlas. Usar el ejemplo
`01_estructura_script.py` para reconocer función, parámetro y entrada principal.

## Segundo bloque: reunir los partes

Ejecutar etapas 01 y 02. Mostrar la diferencia entre ruta del terminal y ruta
del proyecto, la búsqueda de CSV y la lectura con cabeceras. Resultado: tres
archivos, 18 registros. El riesgo sigue siendo una cadena de texto.
Cerrar aquí el primer logro antes del descanso.

## Tercer bloque: interpretar y comprobar

Usar ejemplo 02 y etapa 03 para separar extracción, transformación y validación.
La etapa 03 deja 13 válidos y 5 rechazos: aún contiene el reenvío MEI-002.
Mostrar la regla del conjunto en el proceso final. La etapa 05 ya incorpora
esa regla y deja 12 válidos, 6 rechazos y 4 prioridades.

La etapa 04 muestra el paso intermedio de JSON y todavía imprime el reenvío.
Si se sigue el orden numérico, aclarar esta diferencia. Si se prefiere una
demo sin duplicados en ese momento, usar ejemplo 03 después de la etapa 05.

Predecir el efecto de pasar el umbral de 4 a 5. Ejecutar con la configuración
alternativa o comparar con ejemplo 03. Los válidos siguen siendo los mismos.
Ejemplo 04 demuestra la reutilización real de `reglas.validar()`.

## Cuarto bloque: completar el proceso

Recorrer las funciones de `procesar.py`, sus entradas y sus resultados.
Ejecutar el programa completo. Abrir los CSV, el resumen JSON y el log.
Diferenciar rechazo de fila, omisión de archivo y fallo global.
Repetir una ejecución para comprobar que las salidas no duplican registros.

## El último mensajero y la resolución

Copiar el CSV de reserva a entrada. Preguntar qué recuentos cambiarán antes
de ejecutar. Resultado: 19 leídos, 13 válidos, 6 rechazados, 5 prioritarios.
El código permanece igual. Conectar con una tarea real del público.

Para volver al inicio, retirar solo las copias añadidas a entrada. No tocar
los tres CSV iniciales ni las reservas. Una nueva ejecución regenera salidas.

## Si hay tiempo

Probar la cabecera incorrecta y el JSON inválido. Explicar que un programador
de tareas puede arrancar el script con un intérprete, unas rutas y un usuario
concretos. No hace falta instalar un programador para entender el proceso.
