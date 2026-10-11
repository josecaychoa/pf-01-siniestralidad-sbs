# Diccionario de datos · PF-01

`Portafolio · PF-01` · Versión 0.1 · 2026-10-11 · Paquete 2.1 (tablas intermedias). Las tablas del modelo Oracle se agregan en el paquete 2.3.

## 1. Tablas intermedias en formato largo (`data/interim/`)

Las tres tablas tienen las mismas columnas: una fila por celda numérica publicada por la Superintendencia de Banca, Seguros y AFP (SBS, s. f.-a, s. f.-b, s. f.-c, s. f.-d). Se generan con `uv run python scripts/descargar_sbs.py` y se leen con las columnas de texto como texto, por ejemplo `pd.read_csv(ruta, dtype={"llamadas_concepto": str, "llamadas_empresa": str})`.

| Columna | Tipo | Descripción |
|---|---|---|
| `serie` | texto | Serie de la SBS: `S-367` (Boletín Mensual) o `S-401`, `S-402` y `S-403` (cuadros de consistencia) |
| `corte` | fecha ISO | Fecha de corte; se valida contra el rótulo «Al … de … del …» de cada hoja |
| `hoja` | texto | Hoja del libro (`P001` … `P016`), sin espacios |
| `cuadro` | texto | Título de la hoja, sin llamadas a nota |
| `unidad` | texto | Unidad declarada bajo el título («En Miles de Soles», «En Porcentaje»); vacía en P004, donde la unidad está en la sección |
| `seccion` | texto | Solo P004: grupo del indicador (p. ej., «DE SOLVENCIA (N° de veces)») |
| `fila`, `columna` | entero | Posición de la celda en la hoja, en numeración de Excel (1 = primera) |
| `concepto_original` | texto | Etiqueta de la fila tal como se publica (cuenta, riesgo o indicador) |
| `concepto` | texto | Etiqueta sin llamadas a nota y sin espacios repetidos |
| `sangria` | entero | Espacios iniciales de la etiqueta; indica el nivel en P001 y P002 |
| `llamadas_concepto` | texto | Llamadas a nota de la etiqueta («7/ 8/») |
| `empresa_original` | texto | Encabezado de la columna tal como se publica |
| `empresa` | texto | Encabezado sin llamadas a nota; la equivalencia entre razones sociales se resuelve en 2.2 |
| `llamadas_empresa` | texto | Llamadas a nota del encabezado («1/», «(3)») |
| `es_total` | booleano | Verdadero si el encabezado empieza por «Total» (incluye «Total + Mapfre Perú (abs)») |
| `moneda` | texto | Solo P001 y P002: `MN`, `ME` o `TOTAL` |
| `valor` | número | Cifra publicada (miles de soles, porcentaje o veces, según la hoja) |
| `sha256_archivo` | texto | SHA-256 del archivo de origen en `data/raw/manifest.csv` |

Llave única: `serie`, `corte`, `hoja`, `fila` y `columna` (probada en `tests/test_datos_sbs.py`).

Celdas excluidas: vacías y textos como «n.a.», «n.d.» o «-», además de las notas al pie y los rótulos de sección.

## 2. Observaciones de estructura (verificadas el 2026-10-11)

| Tema | Observación | Tratamiento |
|---|---|---|
| Formato de los libros | `.xlsx` (2021, 2022, 2024, ago-2025, ago-2026), `.xlsm` (2023) y `.xls` BIFF (2020 y dic-2025); el libro de 2019 tiene extensión `.xls`, pero es `.xlsx` | El motor de lectura se elige por la firma del archivo |
| Nombres de hoja | Diciembre de 2020 publica «P003 » y «P004 » con espacio final | Se normalizan |
| Encabezados | La fila de encabezado está entre la 4 y la 7 según la hoja y el corte; P003 repite el encabezado a mitad de hoja con llamadas propias | Se detecta en cada hoja y se usa el encabezado vigente para cada tramo |
| Empresas absorbidas o en liquidación | En P009 a P014, diciembre de 2020 agrega `Rigel (1)`, `Coface Seguros (2)` y `Total + Rigel + Coface Seguros (3)`; diciembre de 2022 agrega `Mapfre Perú (abs) (2)` y `Total + Mapfre Perú (abs) (3)` | Se conservan con `es_total`; qué total usar para los cuadres se decide en 2.2 |
| Indicadores de solvencia | En diciembre de 2019, 2021 y 2023, P004 no publica los seis primeros indicadores de solvencia (de «Patrimonio Efectivo / Requerimientos Patrimoniales» a «Reservas Técnicas / Patrimonio Efectivo») | No generan filas |
| Consistencia | P009 a P016 de agosto de 2026 coinciden celda por celda con S-401, S-402 y S-403 (8 778 celdas, diferencia máxima 0) | Prueba en `tests/test_datos_sbs.py` |

## Referencias

Superintendencia de Banca, Seguros y AFP. (s. f.-a). *Boletín mensual* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-367

Superintendencia de Banca, Seguros y AFP. (s. f.-b). *Índice de siniestralidad directa y retenida según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-403

Superintendencia de Banca, Seguros y AFP. (s. f.-c). *Primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-401

Superintendencia de Banca, Seguros y AFP. (s. f.-d). *Siniestros de primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-402
