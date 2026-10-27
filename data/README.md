# Datos

Los archivos de la Superintendencia de Banca, Seguros y AFP (SBS) no se versionan: se descargan con `uv run python scripts/descargar_sbs.py`, que también los lleva a formato largo en `data/interim/`. Solo se versiona `data/raw/manifest.csv`, que registra la URL, la fecha de descarga, la fecha `Last-Modified` del servidor, el tamaño y el SHA-256 de cada archivo.

El manifiesto funciona como referencia: en un clon limpio, cada archivo descargado debe coincidir con su SHA-256. Si la SBS reemplazó un archivo (riesgo R3 del acta), el script se detiene sin modificar `data/raw/` y el cambio se revisa antes de actualizar el manifiesto.

## Archivos de origen

| Archivo | Fuente | URL | Documento o serie | Fecha de corte | Fecha de descarga | Condiciones de uso |
|---|---|---|---|---|---|---|
| `S-367-di2019.ZIP` | SBS | [enlace](https://intranet2.sbs.gob.pe/estadistica/financiera/2019/Diciembre/S-367-di2019.ZIP) | S-367 · Boletín Mensual (libro `Avance 2019 12.xls`, en realidad `.xlsx`) | 2019-12-31 | 2026-10-11 | No declaradas (ver nota) |
| `S-367-di2020.ZIP` | SBS | [enlace](https://intranet2.sbs.gob.pe/estadistica/financiera/2020/Diciembre/S-367-di2020.ZIP) | S-367 · Boletín Mensual (`.xls`) | 2020-12-31 | 2026-10-11 | No declaradas |
| `S-367-di2021.ZIP` | SBS | [enlace](https://intranet2.sbs.gob.pe/estadistica/financiera/2021/Diciembre/S-367-di2021.ZIP) | S-367 · Boletín Mensual (`.xlsx`, actualizado al 20.09.23) | 2021-12-31 | 2026-10-11 | No declaradas |
| `S-367-di2022.ZIP` | SBS | [enlace](https://intranet2.sbs.gob.pe/estadistica/financiera/2022/Diciembre/S-367-di2022.ZIP) | S-367 · Boletín Mensual (`.xlsx`, actualizado al 20.09.23) | 2022-12-31 | 2026-10-11 | No declaradas |
| `S-367-di2023.ZIP` | SBS | [enlace](https://intranet2.sbs.gob.pe/estadistica/financiera/2023/Diciembre/S-367-di2023.ZIP) | S-367 · Boletín Mensual (`.xlsm`) | 2023-12-31 | 2026-10-11 | No declaradas |
| `S-367-di2024.ZIP` | SBS | [enlace](https://intranet2.sbs.gob.pe/estadistica/financiera/2024/Diciembre/S-367-di2024.ZIP) | S-367 · Boletín Mensual (`.xlsx`, actualizado al 26.05.2026) | 2024-12-31 | 2026-10-11 | No declaradas |
| `S-367-ag2025.ZIP` | SBS | [enlace](https://intranet2.sbs.gob.pe/estadistica/financiera/2025/Agosto/S-367-ag2025.ZIP) | S-367 · Boletín Mensual (`.xlsx`) | 2025-08-31 | 2026-10-11 | No declaradas |
| `S-367-di2025.ZIP` | SBS | [enlace](https://intranet2.sbs.gob.pe/estadistica/financiera/2025/Diciembre/S-367-di2025.ZIP) | S-367 · Boletín Mensual (`.xls`, actualizado al 06.05.2026) | 2025-12-31 | 2026-10-11 | No declaradas |
| `S-367-ag2026.ZIP` | SBS | [enlace](https://intranet2.sbs.gob.pe/estadistica/financiera/2026/Agosto/S-367-ag2026.ZIP) | S-367 · Boletín Mensual (`.xlsx`) | 2026-08-31 | 2026-10-11 | No declaradas |
| `S-401-ag2026.XLS` | SBS | [enlace](https://intranet2.sbs.gob.pe/estadistica/financiera/2026/Agosto/S-401-ag2026.XLS) | S-401 · Primas de seguros netas, cedidas y retenidas según riesgos | 2026-08-31 | 2026-10-11 | No declaradas |
| `S-402-ag2026.XLS` | SBS | [enlace](https://intranet2.sbs.gob.pe/estadistica/financiera/2026/Agosto/S-402-ag2026.XLS) | S-402 · Siniestros de primas de seguros netas, cedidas y retenidas según riesgos | 2026-08-31 | 2026-10-11 | No declaradas |
| `S-403-ag2026.XLS` | SBS | [enlace](https://intranet2.sbs.gob.pe/estadistica/financiera/2026/Agosto/S-403-ag2026.XLS) | S-403 · Índice de siniestralidad directa y retenida según riesgos | 2026-08-31 | 2026-10-11 | No declaradas |

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-d, s. f.-e, s. f.-f). La fecha de descarga es la del registro de referencia en el manifiesto. Sobre las condiciones de uso: el portal indica «Todos los derechos reservados» y la página de datos abiertos no declara una licencia (SBS, s. f.-c); el proyecto publica solo agregados propios con su cita y no redistribuye los archivos originales.

## Tablas en formato largo (`data/interim/`)

| Archivo | Hojas | Filas (descarga del 2026-10-11) |
|---|---|---|
| `estados_financieros.csv` | P001 (estado de situación financiera) y P002 (estado de resultados), con moneda MN, ME y TOTAL | 50 790 |
| `indicadores.csv` | P003 (cifras para indicadores) y P004 (indicadores, con su sección) | 15 086 |
| `riesgos.csv` | P009 a P016 del Boletín Mensual y de los cuadros S-401, S-402 y S-403 | 86 842 |

Las columnas se describen en `docs/03_diccionario_datos.md`, sección 1.

## Salidas del análisis (`data/processed/`)

`uv run python scripts/exportar_indicadores.py` escribe las vistas del análisis de 3.2 (`sql/oracle/04_vistas_analisis.sql`, decisiones D-PF01-11 a D-PF01-16) como CSV en UTF-8 con finales de línea LF. Las columnas se describen en `docs/03_diccionario_datos.md`, secciones 3.6 a 3.12.

| Archivo | Vista de origen | Una fila por | Filas |
|---|---|---|---|
| `parametros_analisis.csv` | `vw_parametros_analisis` | parámetros del análisis (fila única) | 1 |
| `cortes_analisis.csv` | `vw_cortes_analisis` | cortes del análisis (fila única) | 1 |
| `indicadores_riesgo.csv` | `vw_indicadores_riesgo` | riesgo comparable en cada corte | 432 |
| `crecimiento_riesgos.csv` | `vw_crecimiento_riesgo` | riesgo comparable | 48 |
| `matriz_riesgos.csv` | `vw_matriz_riesgo` | riesgo comparable en el corte actual | 48 |
| `participacion_empresa_riesgo.csv` | `vw_participacion_empresa_riesgo` | empresa y riesgo en cada corte | 7 756 |

Se versionan `matriz_riesgos.csv`, `indicadores_riesgo.csv` y `crecimiento_riesgos.csv`, que lee el tablero Power BI (D-PF01-23): son agregados propios por riesgo comparable (48 filas en la matriz y en el crecimiento; 432 en la serie de 9 cortes) que se publican con su cita, según la regla de datos del portafolio. Los otros tres se regeneran con el script y quedan fuera de Git.

*Nota.* Elaboración propia con datos de SBS (s. f.-b).

## Verificación de datos personales

Los datos publicados por la SBS y los agregados del proyecto corresponden a personas jurídicas (empresas de seguros supervisadas) y a totales del sistema: las tablas de `data/interim/` y `data/processed/` y el modelo Oracle solo contienen nombres de empresas, conceptos contables, riesgos y cifras (estructura en `docs/03_diccionario_datos.md`, sección 1, y catálogos versionados en `src/pf_01_siniestralidad_sbs/catalogos/`). Las notas al pie de la fuente se excluyen en la extracción y solo se conservan sus llamadas («1/», «(3)»), salvo la nota «*Actualizado al 01/09/2022» de P001 de diciembre de 2021, que entró como cuenta (limitación conocida, issue #34); los textos libres de los catálogos describen eventos societarios, resoluciones de la SBS y excepciones de la fuente. Verificado el 2026-10-26 sobre la estructura y los catálogos, conforme a la Ley N.º 29733 y su reglamento (D.S. N.º 016-2024-JUS).

## Referencias

Superintendencia de Banca, Seguros y AFP. (s. f.-a). *Boletín estadístico de seguros*. Recuperado el 10 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaBoletinEstadistico.aspx?p=25

Superintendencia de Banca, Seguros y AFP. (s. f.-b). *Boletín mensual* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-367

Superintendencia de Banca, Seguros y AFP. (s. f.-c). *Datos abiertos*. Recuperado el 10 de octubre de 2026, de https://www.sbs.gob.pe/estadisticas-y-publicaciones/estadisticas-/datos-abiertos_

Superintendencia de Banca, Seguros y AFP. (s. f.-d). *Índice de siniestralidad directa y retenida según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-403

Superintendencia de Banca, Seguros y AFP. (s. f.-e). *Primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-401

Superintendencia de Banca, Seguros y AFP. (s. f.-f). *Siniestros de primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-402
