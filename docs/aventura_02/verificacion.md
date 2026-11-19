# Verificación de esta entrega

- Python 3.12 y Requests 2.34.2.
- 12 pruebas aprobadas: flujo HTTP completo, ejecución desde otra carpeta,
  ausencia de condiciones, datos ausentes/incorrectos y fechas pasadas,
  autenticación/caducidad, cuerpos inválidos, 404, reintentos 503, JSON roto,
  contrato inesperado, timeout y ausencia de reintentos POST.
- Cinco etapas ejecutadas en modo demo, sin errores.
- ensayar.py completó INV-001 y todos los escenarios de error.
- La consulta directa a MeteoGalicia desde el entorno de preparación agotó
  el timeout de lectura. No se afirma haber verificado el flujo real completo.
  Se consultaron previamente la documentación oficial y el endpoint público.
- Los datos sintéticos están identificados en consola y resultado.

Antes de la charla, ejecutar ensayar.py en el ordenador del ponente y comprobar
una consulta real desde su red. La instalación inicial de dependencias requiere
Internet; el ensayo posterior no.
