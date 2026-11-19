# Verificación de aventura_02

- Documentación oficial consultada: MeteoSIX v5.1 (5.1.0), publicada en
  octubre de 2026. La API vigente conserva la base `/apiv5/`; la operación es
  `getNumericForecastInfo`, con `API_KEY` y coordenadas `longitud,latitud`.
- El manual define `precipitation_amount` como acumulación de la hora anterior
  en `lm2`; no documenta una variable de probabilidad de lluvia.
- La respuesta sin clave devolvió la excepción documentada `005`; no se hizo
  ninguna consulta autenticada con la clave real.
- 29 pruebas aprobadas en las dos aventuras. Incluyen la adaptación de MeteoSIX,
  clave ausente, errores, datos incompletos, validación de la invocación,
  reintentos GET y ausencia de reintentos POST. Ninguna prueba consulta Internet.
- `python aventura_02/ensayar.py` completó la invocación local y los escenarios
  de error con meteorología sintética.
- `aventura_02/.env` está ignorado por Git. No se inspeccionó su contenido ni se
  utilizó en las pruebas.

Pendiente: ejecutar `python aventura_02/etapas/06_consultar_meteosix.py` y
`python aventura_02/cliente.py --fuente meteosix --demo` desde el equipo y la
red de la charla con `METEOSIX_API_KEY` configurada. La consulta real puede no
tener precipitación positiva en los días/franjas disponibles; en tal caso el
cliente no crea una invocación, por diseño. El JSON municipal y `--offline`
siguen siendo alternativas.
