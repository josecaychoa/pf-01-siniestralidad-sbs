# Diccionario de datos · PF-01

`Portafolio · PF-01` · Versión 0.3 · 2026-10-14 · Paquetes 2.1 (tablas intermedias), 2.2 (catálogos y validación) y 2.3 (modelo de datos Oracle).

## 1. Tablas intermedias en formato largo (`data/interim/`)

Las tres tablas tienen las mismas columnas: una fila por celda numérica publicada por la Superintendencia de Banca, Seguros y AFP (SBS, s. f.-a, s. f.-b, s. f.-c, s. f.-d). Se generan con `uv run python scripts/descargar_sbs.py` y se leen con las columnas de texto como texto, por ejemplo `pd.read_csv(ruta, dtype={"llamadas_concepto": str, "llamadas_empresa": str})`.

| Columna | Tipo | Descripción |
|---|---|---|
| `serie` | texto | Serie de la SBS: `S-367` (Boletín Mensual) o `S-401`, `S-402` y `S-403` (cuadros de consistencia) |
| `corte` | fecha ISO | Fecha de corte; se valida contra el rótulo «Al … de … del …» de cada hoja |
| `hoja` | texto | Hoja del libro (`P001` … `P016`), sin espacios |
| `cuadro` | texto | Título de la hoja, sin llamadas a nota |
| `unidad` | texto | Unidad declarada bajo el título («En Miles de Soles», «En Porcentaje»); vacía en P004, donde la unidad está en la sección |
| `seccion` | texto | Solo P004: grupo del indicador (p. ej., «DE GESTIÓN») |
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

## 2. Tablas del modelo Oracle (`sql/oracle/01_ddl_tablas.sql`)

El esquema del proyecto tiene 13 tablas: 3 de staging (`stg_`), copia de `data/interim/`, y las 7 dimensiones (`dim_`) y 3 tablas de hechos (`fct_`) del modelo relacional de `docs/modelo/`. Los tipos salen de `USER_TAB_COLUMNS` de la base nativa (Oracle 23.6) el 2026-10-14 y son idénticos en el contenedor (23.26.3). «Nulo» indica si la columna admite nulos; «PK/FK», si forma parte de la llave primaria o de una llave foránea, con la tabla a la que apunta. La descripción de cada columna de `dim_` y `fct_` es el texto de su comentario en la base (`COMMENT ON COLUMN`). Los valores observados corresponden a la carga del 2026-10-14 (SBS, s. f.-a, s. f.-b, s. f.-c, s. f.-d).

| Tabla | Clase | Una fila por | Filas | Origen |
|---|---|---|---|---|
| `stg_estados_financieros` | staging | celda de P001 o P002 | 50 790 | `data/interim/estados_financieros.csv` |
| `stg_indicadores` | staging | celda de P003 o P004 | 15 086 | `data/interim/indicadores.csv` |
| `stg_riesgos` | staging | celda de P009 a P016 (S-367) o de los cuadros S-401 a S-403 | 86 842 | `data/interim/riesgos.csv` |
| `dim_columna_empresa` | dimensión | rótulo de columna de la fuente y rango de cortes | 38 | `empresas.csv` y columnas Total de `stg_` |
| `dim_corte` | dimensión | corte | 9 | `cortes.csv` |
| `dim_cuadro` | dimensión | hoja | 12 | tablas `stg_` (serie S-367) |
| `dim_cuenta` | dimensión | fila de P001 o P002 | 127 | `stg_estados_financieros` |
| `dim_empresa` | dimensión | empresa | 20 | `empresas.csv` |
| `dim_indicador` | dimensión | fila de P003 o P004 | 126 | `stg_indicadores` |
| `dim_riesgo` | dimensión | riesgo | 60 | `riesgos.csv` |
| `fct_estado_financiero` | hechos | corte, cuenta, columna y moneda | 50 790 | `stg_estados_financieros` |
| `fct_indicador` | hechos | corte, indicador y columna | 15 086 | `stg_indicadores` |
| `fct_riesgo` | hechos | corte, riesgo, columna y hoja | 78 064 | `stg_riesgos` (solo S-367) |

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d). Filas tras la carga del 2026-10-14, iguales en la base nativa y en el contenedor.

### 2.1 `stg_estados_financieros`

Copia de `data/interim/estados_financieros.csv`: celdas de P001 (estado de situación financiera) y P002 (estado de resultados). Las tres tablas `stg_` tienen las mismas 19 columnas, en el orden del CSV; la tabla de esta subsección vale para las tres. Llave primaria: `serie`, `corte`, `hoja`, `fila` y `columna`, la llave única de la sección 1. Los textos se declaran en caracteres (`CHAR`) porque la base mide `VARCHAR2` en bytes. En esta tabla, `seccion` siempre es nula y `moneda` siempre tiene valor.

| Columna | Tipo | Nulo | PK/FK | Descripción | Valores o dominio |
|---|---|---|---|---|---|
| `serie` | `VARCHAR2(10 CHAR)` | No | PK | Serie de la SBS: S-367 (Boletín Mensual) o S-401, S-402 y S-403 (cuadros de consistencia) | `S-367` en las tres tablas; `S-401`, `S-402` y `S-403` solo en `stg_riesgos` |
| `corte` | `DATE` | No | PK | Fecha de corte; se valida contra el rótulo «Al … de … del …» de cada hoja | 9 cortes de 2019-12-31 a 2026-08-31 |
| `hoja` | `VARCHAR2(4 CHAR)` | No | PK | Hoja del libro (P001 … P016), sin espacios | `P001` y `P002`; `P003` y `P004`; `P009` a `P016` |
| `cuadro` | `VARCHAR2(150 CHAR)` | No |  | Título de la hoja, sin llamadas a nota | Título publicado |
| `unidad` | `VARCHAR2(30 CHAR)` | Sí |  | Unidad declarada bajo el título («En Miles de Soles», «En Porcentaje»); vacía en P004, donde la unidad está en la sección | `En Miles de Soles`, `En Porcentaje` o nulo (P004) |
| `seccion` | `VARCHAR2(100 CHAR)` | Sí |  | Solo P004: grupo del indicador (p. ej., «DE GESTIÓN») | Solo en `stg_indicadores` (P004) |
| `fila` | `NUMBER(7)` | No | PK | Fila de la celda en la hoja, en numeración de Excel (1 = primera) | 7 a 102 |
| `columna` | `NUMBER(5)` | No | PK | Columna de la celda en la hoja, en numeración de Excel (1 = primera) | 2 a 90 |
| `concepto_original` | `VARCHAR2(200 CHAR)` | No |  | Etiqueta de la fila tal como se publica (cuenta, riesgo o indicador) | Texto publicado |
| `concepto` | `VARCHAR2(200 CHAR)` | No |  | Etiqueta sin llamadas a nota y sin espacios repetidos | Texto sin llamadas |
| `sangria` | `NUMBER(3)` | No |  | Espacios iniciales de la etiqueta; indica el nivel en P001 y P002 | `0` a `12` |
| `llamadas_concepto` | `VARCHAR2(30 CHAR)` | Sí |  | Llamadas a nota de la etiqueta («7/ 8/») | p. ej., `1/`, `(1)`; nula si no hay llamada |
| `empresa_original` | `VARCHAR2(150 CHAR)` | No |  | Encabezado de la columna tal como se publica | Texto publicado |
| `empresa` | `VARCHAR2(150 CHAR)` | No |  | Encabezado sin llamadas a nota; la equivalencia entre razones sociales se resuelve en dim_columna_empresa | Texto sin llamadas |
| `llamadas_empresa` | `VARCHAR2(30 CHAR)` | Sí |  | Llamadas a nota del encabezado («1/», «(3)») | p. ej., `1/`, `(3)`; nula si no hay llamada |
| `es_total` | `BOOLEAN` | No |  | Verdadero si el encabezado empieza por «Total» (incluye «Total + Mapfre Perú (abs)») | `TRUE` o `FALSE` |
| `moneda` | `VARCHAR2(5 CHAR)` | Sí |  | Solo P001 y P002: MN, ME o TOTAL | `MN`, `ME` o `TOTAL`; solo en `stg_estados_financieros` |
| `valor` | `NUMBER` | No |  | Cifra publicada (miles de soles, porcentaje o veces, según la hoja); NUMBER sin precisión (D-PF01-06) | Sin redondear |
| `sha256_archivo` | `VARCHAR2(64 CHAR)` | No |  | SHA-256 del archivo de origen en data/raw/manifest.csv | 64 caracteres hexadecimales |

### 2.2 `stg_indicadores`

Copia de `data/interim/indicadores.csv`: celdas de P003 (cifras consideradas en la elaboración de los indicadores) y P004 (indicadores). Mismas columnas, tipos y llave primaria que `stg_estados_financieros` (sección 2.1). `moneda` siempre es nula y `seccion` solo tiene valor en P004; en P003 la carga deriva el tramo de la hoja (sección 4.4).

### 2.3 `stg_riesgos`

Copia de `data/interim/riesgos.csv`: celdas de P009 a P016 del Boletín Mensual (S-367) en los 9 cortes y de los cuadros S-401, S-402 y S-403 de agosto de 2026 (SBS, s. f.-b, s. f.-c, s. f.-d). Mismas columnas, tipos y llave primaria que `stg_estados_financieros` (sección 2.1); `seccion` y `moneda` siempre son nulas. Solo las filas de la serie S-367 pasan a `fct_riesgo` (D-PF01-08); las de S-401 a S-403 sirven para `vw_cuadre_cuadros_sbs`.

### 2.4 `dim_columna_empresa`

Una fila por rótulo de columna de la fuente y rango de cortes: las 32 equivalencias de `empresas.csv` (sección 7.1), con `columna_id` 1 a 32, y las 6 columnas Total publicadas (33 a 38). Una celda de `stg_` se asigna con su rótulo normalizado y su corte, que debe caer entre `corte_desde` y `corte_hasta`. Las restricciones CHECK de `tipo_columna` y `en_total_simple` siguen la decisión D-PF01-07.

| Columna | Tipo | Nulo | PK/FK | Descripción | Valores o dominio |
|---|---|---|---|---|---|
| `columna_id` | `NUMBER(6)` | No | PK | Identificador de la columna: 1 a 32 para las empresas, en el orden de empresas.csv, y los siguientes para las columnas Total | 1 a 38 (32 de empresa y 6 Total) |
| `clave_fuente` | `VARCHAR2(120)` | No |  | Rótulo de la columna en la fuente, normalizado (mayúsculas, sin tildes y sin espacios repetidos) | 35 rótulos, p. ej., `SECREX`, `MAPFRE PERU (ABS)`, `TOTAL` |
| `corte_desde` | `DATE` | No |  | Primer corte en que el rótulo tiene esta equivalencia | 2019-12-31 a 2026-01-01 |
| `corte_hasta` | `DATE` | No |  | Último corte en que el rótulo tiene esta equivalencia | 2019-12-31 a 2099-12-31 (2099-12-31 = vigente) |
| `tipo_columna` | `VARCHAR2(15)` | No |  | empresa, total_simple (columna «Total» o «Total empresas de seguros») o total_ampliado (columna «Total + …») (D-PF01-07) | `empresa`, `total_simple` o `total_ampliado` (CHECK `ck_dim_columna_empresa_tipo_columna`) |
| `entidad` | `VARCHAR2(150)` | Sí |  | Denominación en ese período según las notas al pie de la SBS; en las columnas Total, el rótulo publicado | 31 denominaciones |
| `estado` | `VARCHAR2(10)` | Sí |  | Situación de la empresa en ese rango de cortes; nulo en las columnas Total | `vigente`, `liquidada` o `absorbida` |
| `en_total_simple` | `VARCHAR2(1)` | No |  | S si la columna entra en el total simple; N en los flujos de empresas que dejaron de operar en el año (D-PF01-01 y D-PF01-07) | `S` o `N` (CHECK `ck_dim_columna_empresa_en_total_simple`); `N` en las columnas Total |
| `evento` | `VARCHAR2(200)` | Sí |  | Cambio de denominación, fusión o liquidación que explica la equivalencia | Texto del catálogo |
| `fuente_evento` | `VARCHAR2(200)` | Sí |  | Resolución SBS que autoriza el evento | p. ej., Resolución SBS N.º 1724-2022 (25/05/2022) |
| `empresa_id` | `VARCHAR2(30)` | Sí | FK a `dim_empresa` | Empresa para el análisis en el tiempo; nulo en las columnas Total | 20 empresas |

Columnas Total (2026-10-14):

| `columna_id` | Rótulo normalizado | `tipo_columna` | Cortes |
|---|---|---|---|
| 33 | `TOTAL` | `total_simple` | 2019-12-31 a 2026-08-31 (P003 y P009 a P016) |
| 34 | `TOTAL EMPRESAS DE SEGUROS` | `total_simple` | 2019-12-31 a 2026-08-31 (P001 y P002) |
| 35 | `TOTAL + COFACE SEGUROS + RIGEL` | `total_ampliado` | 2020-12-31 |
| 36 | `TOTAL + MAPFRE PERU (ABS)` | `total_ampliado` | 2022-12-31 |
| 37 | `TOTAL + RIGEL + COFACE SEGUROS` | `total_ampliado` | 2020-12-31 |
| 38 | `TOTAL +RIGEL + COFACE SEGUROS` | `total_ampliado` | 2020-12-31 |

*Nota.* Elaboración propia con datos de SBS (s. f.-a). Los cuatro rótulos ampliados son las variantes que la SBS publica en distintas hojas del mismo corte.

### 2.5 `dim_corte`

Una fila por corte del catálogo `cortes.csv` (sección 7.3). Todas las tablas de hechos apuntan a ella.

| Columna | Tipo | Nulo | PK/FK | Descripción | Valores o dominio |
|---|---|---|---|---|---|
| `fecha_corte` | `DATE` | No | PK | Fecha de corte del Boletín Mensual (último día del mes) | 9 cortes: 31 de diciembre de 2019 a 2025 y 31 de agosto de 2025 y de 2026 |
| `meses_acumulados` | `NUMBER(2)` | No |  | Meses que acumulan las cifras de flujo en el año: 12 en diciembre y 8 en agosto | `12` u `8` |
| `plan_de_cuentas` | `VARCHAR2(100)` | No |  | Versión del plan de cuentas vigente en el corte | 3 versiones (sección 7.3) |
| `resolucion_plan` | `VARCHAR2(20)` | Sí |  | Número de la resolución SBS del plan de cuentas; nulo antes de 2021 | `976-2021`, `085-2026` o nulo (sección 4.5) |

### 2.6 `dim_cuadro`

Una fila por hoja del Boletín Mensual que usa el proyecto. Título y unidad son los del corte más reciente; `grupo` y `medida` los define la carga (sección 4.5).

| Columna | Tipo | Nulo | PK/FK | Descripción | Valores o dominio |
|---|---|---|---|---|---|
| `hoja` | `VARCHAR2(4)` | No | PK | Código de la hoja del Boletín Mensual | `P001` a `P004` y `P009` a `P016` |
| `cuadro` | `VARCHAR2(150)` | No |  | Título de la hoja en el corte más reciente del Boletín Mensual | 12 títulos |
| `unidad` | `VARCHAR2(30)` | Sí |  | Unidad declarada bajo el título en el corte más reciente; nula en P004, donde la unidad va en cada sección | `En Miles de Soles`, `En Porcentaje` o nulo |
| `grupo` | `VARCHAR2(20)` | No |  | Tabla de data/interim de la que sale la hoja | `estados_financieros`, `indicadores` o `riesgos` |
| `medida` | `VARCHAR2(40)` | No |  | Lo que publica la hoja, con el nombre de la columna de las vistas | 12 valores (sección 4.5) |

### 2.7 `dim_cuenta`

Una fila por cuenta, es decir, por fila de P001 o P002. La identifica su rótulo normalizado en la hoja; los rótulos que se repiten en la misma hoja y corte llevan « (2)» en su segunda aparición (sección 4.3). Incluye una fila espuria: la nota al pie «*Actualizado al 01/09/2022» de P001 de diciembre de 2021, que la extracción tomó como cuenta porque trae un 0 en la columna de Chubb Seguros; no afecta los cuadres.

| Columna | Tipo | Nulo | PK/FK | Descripción | Valores o dominio |
|---|---|---|---|---|---|
| `cuenta_id` | `NUMBER(6)` | No | PK | Identificador de la cuenta, en el orden de la hoja del corte más reciente en que aparece | 1 a 127 |
| `clave` | `VARCHAR2(150)` | No |  | Rótulo normalizado de la fila; si el rótulo se repite en la misma hoja y corte, la segunda aparición lleva el sufijo (2) | 127 valores, p. ej., `TOTAL ACTIVO`, `OBLIGACIONES FINANCIERAS (2)` |
| `cuenta` | `VARCHAR2(150)` | No |  | Rótulo publicado de la cuenta en el corte más reciente en que aparece | 122 rótulos |
| `nivel` | `NUMBER(2)` | Sí |  | Nivel de sangría del rótulo en la hoja (0 = sin sangría), en el corte más reciente en que aparece | `0` a `3` (sección 4.5) |
| `hoja` | `VARCHAR2(4)` | No | FK a `dim_cuadro` | Hoja del estado financiero | `P001` (situación financiera) o `P002` (resultados) |

### 2.8 `dim_empresa`

Una fila por empresa para el análisis en el tiempo, desde `empresas.csv`. Agrupa los rótulos que la SBS publica para una misma compañía (sección 7.1).

| Columna | Tipo | Nulo | PK/FK | Descripción | Valores o dominio |
|---|---|---|---|---|---|
| `empresa_id` | `VARCHAR2(30)` | No | PK | Código de la empresa para el análisis en el tiempo (catálogo empresas.csv) | 20 códigos, p. ej., `RIMAC`, `MAPFRE`, `CESCE` |
| `empresa` | `VARCHAR2(100)` | No |  | Denominación vigente de la empresa | p. ej., Rímac, Mapfre Perú, Cesce Perú |

### 2.9 `dim_indicador`

Una fila por indicador o cifra para indicadores, es decir, por fila de P003 o P004 dentro de su sección. En P003, la sección es el tramo de la hoja (sección 4.4).

| Columna | Tipo | Nulo | PK/FK | Descripción | Valores o dominio |
|---|---|---|---|---|---|
| `indicador_id` | `NUMBER(6)` | No | PK | Identificador del indicador, en el orden de la hoja del corte más reciente en que aparece | 1 a 126 |
| `seccion` | `VARCHAR2(100)` | No |  | En P004, la sección publicada; en P003, el tramo de la hoja | P003: `CIFRAS AL CORTE` o `SALDOS PROMEDIO ULTIMOS 12 MESES`; P004: 5 secciones publicadas (de gestión, liquidez, rentabilidad, siniestralidad y solvencia) |
| `clave` | `VARCHAR2(150)` | No |  | Rótulo normalizado del indicador (mayúsculas, sin tildes y sin espacios repetidos) | 106 valores |
| `indicador` | `VARCHAR2(150)` | No |  | Rótulo publicado del indicador en el corte más reciente en que aparece | 106 rótulos |
| `hoja` | `VARCHAR2(4)` | No | FK a `dim_cuadro` | Hoja de origen del indicador | `P003` (cifras para indicadores) o `P004` (indicadores) |

### 2.10 `dim_riesgo`

Una fila por riesgo del catálogo `riesgos.csv` (sección 7.2), con su jerarquía.

| Columna | Tipo | Nulo | PK/FK | Descripción | Valores o dominio |
|---|---|---|---|---|---|
| `riesgo_id` | `NUMBER(3)` | No | PK | Identificador y orden del riesgo en el catálogo riesgos.csv | 1 a 60 |
| `clave` | `VARCHAR2(80)` | No |  | Rótulo normalizado del riesgo (mayúsculas, sin tildes y sin espacios repetidos) | 60 valores, p. ej., `INCENDIO`, `SOAT` |
| `riesgo` | `VARCHAR2(100)` | No |  | Rótulo vigente del riesgo (agosto de 2026) | 60 rótulos |
| `nivel` | `NUMBER(1)` | No |  | Profundidad en la jerarquía del catálogo (0 = TOTAL) | `0` a `5` |
| `tipo` | `VARCHAR2(10)` | No |  | Papel del riesgo en la jerarquía; solo los de tipo riesgo suman el total | `total`, `agregado`, `riesgo` (50 filas que suman el total) o `detalle` (no suma) |
| `ramo` | `VARCHAR2(50)` | Sí |  | Ramo al que pertenece el riesgo; nulo en el TOTAL | Ramos generales, Ramos de accidentes y enfermedades, Ramos de vida o nulo |
| `riesgo_comparable` | `VARCHAR2(100)` | No |  | Agrupación para comparar en el tiempo (p. ej., Cauciones y fianzas) | 58 agrupaciones |
| `corte_desde` | `DATE` | No |  | Primer corte en que se publica el riesgo | 2019-12-31, o 2023-12-31 en las dos filas de Fianzas |
| `nota` | `VARCHAR2(400)` | Sí |  | Observaciones del catálogo | Texto; 5 riesgos con nota |
| `riesgo_padre_id` | `NUMBER(3)` | Sí | FK a `dim_riesgo` | Riesgo o agregado que lo contiene; nulo en el TOTAL | `riesgo_id` de otro riesgo o nulo |

### 2.11 `fct_estado_financiero`

Cifras de P001 y P002. Llave primaria: `moneda`, `columna_id`, `cuenta_id` y `fecha_corte`.

| Columna | Tipo | Nulo | PK/FK | Descripción | Valores o dominio |
|---|---|---|---|---|---|
| `moneda` | `VARCHAR2(5)` | No | PK | Moneda de la columna publicada | `MN`, `ME` o `TOTAL` |
| `valor` | `NUMBER` | No |  | Cifra publicada sin redondear (D-PF01-06), en miles de soles; la utilidad por acción va en soles | `NUMBER` sin precisión |
| `columna_id` | `NUMBER(6)` | No | PK, FK a `dim_columna_empresa` | Columna de empresa o Total de la fuente | 30 columnas |
| `cuenta_id` | `NUMBER(6)` | No | PK, FK a `dim_cuenta` | Cuenta de P001 o P002 | 127 cuentas |
| `fecha_corte` | `DATE` | No | PK, FK a `dim_corte` | Fecha de corte | 9 cortes |

### 2.12 `fct_indicador`

Cifras de P003 y P004. Llave primaria: `fecha_corte`, `columna_id` e `indicador_id`.

| Columna | Tipo | Nulo | PK/FK | Descripción | Valores o dominio |
|---|---|---|---|---|---|
| `valor` | `NUMBER` | No |  | Cifra publicada sin redondear (D-PF01-06): miles de soles en P003; porcentaje o número de veces en P004, según la sección | `NUMBER` sin precisión |
| `fecha_corte` | `DATE` | No | PK, FK a `dim_corte` | Fecha de corte | 9 cortes |
| `columna_id` | `NUMBER(6)` | No | PK, FK a `dim_columna_empresa` | Columna de empresa o Total de la fuente | 34 columnas |
| `indicador_id` | `NUMBER(6)` | No | PK, FK a `dim_indicador` | Indicador o cifra para indicadores | 126 indicadores |

### 2.13 `fct_riesgo`

Primas, siniestros e índices de siniestralidad de P009 a P016, solo de la serie S-367 (D-PF01-08). Llave primaria: `fecha_corte`, `columna_id`, `riesgo_id` y `hoja`.

| Columna | Tipo | Nulo | PK/FK | Descripción | Valores o dominio |
|---|---|---|---|---|---|
| `valor` | `NUMBER` | No |  | Cifra publicada sin redondear (D-PF01-06): miles de soles en P009 a P014; porcentaje en P015 y P016 | `NUMBER` sin precisión |
| `fecha_corte` | `DATE` | No | PK, FK a `dim_corte` | Fecha de corte | 9 cortes |
| `columna_id` | `NUMBER(6)` | No | PK, FK a `dim_columna_empresa` | Columna de empresa o Total de la fuente | 36 columnas |
| `riesgo_id` | `NUMBER(3)` | No | PK, FK a `dim_riesgo` | Riesgo del catálogo | 60 riesgos |
| `hoja` | `VARCHAR2(4)` | No | PK, FK a `dim_cuadro` | Hoja de la cifra; dim_cuadro.medida indica qué publica | `P009` a `P016` |

## 3. Vistas (`sql/oracle/02_vistas.sql`)

Cinco vistas `vw_`: dos analíticas y tres de cuadre para el objetivo O1. Todas se crean con `CREATE OR REPLACE VIEW` y tienen `COMMENT ON TABLE`.

Reglas comunes:
- Redondeo solo en las vistas (D-PF01-06), con la escala del estándar 6.1: montos en miles de soles a 2 decimales e índices en porcentaje a 6 decimales. Las tablas guardan la cifra publicada.
- En los cuadres, la marca `cumple` (tipo `BOOLEAN`) se calcula con la diferencia sin redondear, como en `src/pf_01_siniestralidad_sbs/validacion.py`. Tolerancia de 1 mil soles, salvo en `vw_cuadre_cuadros_sbs`, que exige igualdad exacta.
- Las columnas Total publicadas también son filas, con `empresa_id` nulo. Para seguir a una empresa en el tiempo se suma por `empresa_id`; los índices de P015 y P016 no se suman.
- En las vistas de riesgo, `tipo_riesgo` distingue total, agregado, riesgo y detalle: sumar varios tipos duplica cifras.

| Vista | Propósito | Una fila por | Filas |
|---|---|---|---|
| `vw_produccion_riesgo` | Primas netas, cedidas y retenidas (P009 a P011) | riesgo en cada corte y columna publicada | 9 752 |
| `vw_siniestralidad_riesgo` | Siniestros e índices de siniestralidad (P012 a P016) | riesgo en cada corte y columna publicada | 10 211 |
| `vw_cuadre_balance` | Activo = Pasivo + Patrimonio (P001, moneda TOTAL) | corte y columna publicada | 168 |
| `vw_cuadre_totales` | Suma de las empresas frente a la columna Total | corte, hoja, concepto, moneda y tipo de total | 7 196 |
| `vw_cuadre_cuadros_sbs` | Boletín Mensual frente a S-401, S-402 y S-403 | celda de los cuadros de agosto de 2026 | 8 778 |

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d). Filas tras la carga del 2026-10-14.

### 3.1 `vw_produccion_riesgo`

Primas netas (P009), cedidas (P010) y retenidas (P011) en miles de soles, a 2 decimales. Tablas: `fct_riesgo`, `dim_columna_empresa`, `dim_empresa`, `dim_riesgo` y `dim_corte`.

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha_corte` | `DATE` | Fecha de corte |
| `meses_acumulados` | `NUMBER(2)` | Meses acumulados en el año (12 u 8) |
| `columna_id` | `NUMBER(6)` | Columna de empresa o Total (dim_columna_empresa) |
| `clave_fuente` | `VARCHAR2(120)` | Rótulo normalizado de la columna |
| `tipo_columna` | `VARCHAR2(15)` | `empresa`, `total_simple` o `total_ampliado` |
| `empresa_id` | `VARCHAR2(30)` | Empresa para el análisis en el tiempo; nulo en las columnas Total publicadas |
| `empresa` | `VARCHAR2(100)` | Denominación vigente de la empresa; nula en las columnas Total |
| `entidad` | `VARCHAR2(150)` | Denominación en ese período |
| `estado` | `VARCHAR2(10)` | `vigente`, `liquidada` o `absorbida`; nulo en las columnas Total |
| `riesgo_id` | `NUMBER(3)` | Riesgo del catálogo |
| `riesgo` | `VARCHAR2(100)` | Rótulo vigente del riesgo |
| `nivel_riesgo` | `NUMBER(1)` | Profundidad en la jerarquía (0 = TOTAL) |
| `tipo_riesgo` | `VARCHAR2(10)` | total, agregado, riesgo o detalle (catálogo de riesgos); sumar varios tipos duplica cifras |
| `ramo` | `VARCHAR2(50)` | Ramo del riesgo |
| `riesgo_comparable` | `VARCHAR2(100)` | Agrupación para comparar en el tiempo |
| `primas_netas` | `NUMBER` | Primas de seguros netas (P009), en miles de soles, acumuladas en el año; 2 decimales |
| `primas_cedidas` | `NUMBER` | Primas cedidas netas (P010), en miles de soles, acumuladas en el año; 2 decimales |
| `primas_retenidas` | `NUMBER` | Primas retenidas (P011), en miles de soles, acumuladas en el año; 2 decimales |

### 3.2 `vw_siniestralidad_riesgo`

Siniestros netos (P012), cedidos (P013) y retenidos (P014) en miles de soles, a 2 decimales, e índices de siniestralidad directa (P015) y retenida (P016) publicados, en porcentaje, a 6 decimales. Tiene las mismas 15 columnas de corte, empresa y riesgo que `vw_produccion_riesgo` (sección 3.1), de `fecha_corte` a `riesgo_comparable`, y estas cinco medidas. Tablas: las mismas que la sección 3.1.

| Columna | Tipo | Descripción |
|---|---|---|
| `siniestros_netos` | `NUMBER` | Siniestros de primas de seguros netos (P012), en miles de soles, acumulados en el año; 2 decimales |
| `siniestros_cedidos` | `NUMBER` | Siniestros de primas cedidas netos (P013), en miles de soles, acumulados en el año; 2 decimales |
| `siniestros_retenidos` | `NUMBER` | Siniestros retenidos (P014), en miles de soles, acumulados en el año; 2 decimales |
| `indice_siniestralidad_directa` | `NUMBER` | Índice de siniestralidad directa publicado por la SBS (P015), en porcentaje; 6 decimales; no se suma entre columnas |
| `indice_siniestralidad_retenida` | `NUMBER` | Índice de siniestralidad retenida publicado por la SBS (P016), en porcentaje; 6 decimales; no se suma entre columnas |

La vista trae los índices que publica la SBS; la siniestralidad calculada como siniestros entre primas es parte del objetivo O2.

### 3.3 `vw_cuadre_balance`

Control de O1: Activo = Pasivo + Patrimonio por corte y columna publicada, en P001 y moneda TOTAL (el patrimonio se presenta en moneda nacional, así que la igualdad no se exige por moneda). Tablas: `fct_estado_financiero`, `dim_cuenta`, `dim_columna_empresa` y `dim_empresa`. Montos en miles de soles a 2 decimales.

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha_corte` | `DATE` | Fecha de corte |
| `columna_id` | `NUMBER(6)` | Columna de empresa o Total (dim_columna_empresa) |
| `clave_fuente` | `VARCHAR2(120)` | Rótulo normalizado de la columna |
| `tipo_columna` | `VARCHAR2(15)` | `empresa`, `total_simple` o `total_ampliado` |
| `empresa_id` | `VARCHAR2(30)` | Empresa para el análisis en el tiempo; nulo en las columnas Total |
| `empresa` | `VARCHAR2(100)` | Denominación vigente de la empresa; nula en las columnas Total |
| `total_activo` | `NUMBER` | Total activo, en miles de soles; 2 decimales |
| `total_pasivo` | `NUMBER` | Total pasivo, en miles de soles; 2 decimales |
| `patrimonio` | `NUMBER` | Patrimonio, en miles de soles; 2 decimales |
| `pasivo_mas_patrimonio` | `NUMBER` | Total pasivo + patrimonio, calculado |
| `total_pasivo_y_patrimonio` | `NUMBER` | Total pasivo y patrimonio publicado en P001 |
| `diferencia_activo` | `NUMBER` | Total activo - (total pasivo + patrimonio) |
| `diferencia_total_publicado` | `NUMBER` | (Total pasivo + patrimonio) - total pasivo y patrimonio publicado |
| `cumple` | `BOOLEAN` | Verdadero si las dos diferencias, sin redondear, son de 1 mil soles o menos y no falta ningún rubro |

### 3.4 `vw_cuadre_totales`

Control de O1: suma de las columnas de empresa frente a la columna Total publicada, en P001 a P003 y P009 a P014 (D-PF01-01 y D-PF01-07). El total simple suma las empresas con `en_total_simple = 'S'` y se compara con «Total» o «Total empresas de seguros»; el total ampliado suma todas las columnas de empresa y se compara con «Total + …», que solo existe en diciembre de 2020 y de 2022. En el modelo, la fila de la hoja es su concepto (cuenta, indicador o riesgo). Tablas: las tres `fct_`, `dim_cuenta`, `dim_indicador`, `dim_riesgo` y `dim_columna_empresa`.

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha_corte` | `DATE` | Fecha de corte |
| `hoja` | `VARCHAR2(4)` | Hoja (P001 a P003 y P009 a P014) |
| `concepto_id` | `NUMBER` | Fila de la hoja en el modelo: cuenta_id (P001 y P002), indicador_id (P003) o riesgo_id (P009 a P014) |
| `concepto` | `VARCHAR2(150)` | Rótulo de la cuenta, indicador o riesgo |
| `moneda` | `VARCHAR2(5)` | MN, ME o TOTAL en P001 y P002; nula en las demás hojas |
| `tipo_total` | `VARCHAR2(14)` | total_simple: empresas con en_total_simple = S frente a «Total»; total_ampliado: todas las columnas de empresa frente a «Total + …» |
| `suma_empresas` | `NUMBER` | Suma de las columnas de empresa que integran el total, en miles de soles; 2 decimales |
| `total_publicado` | `NUMBER` | Columna Total publicada, en miles de soles; 2 decimales |
| `diferencia` | `NUMBER` | suma_empresas - total_publicado, en miles de soles; 2 decimales |
| `cumple` | `BOOLEAN` | Verdadero si la diferencia, sin redondear, es de 1 mil soles o menos |

### 3.5 `vw_cuadre_cuadros_sbs`

Control de O1: cada celda de los cuadros S-401, S-402 y S-403 de agosto de 2026 frente a la celda del Boletín Mensual (S-367) con el mismo corte, hoja, fila y columna (SBS, s. f.-a, s. f.-b, s. f.-c, s. f.-d). Es la única vista sobre una tabla `stg_` (`stg_riesgos`), porque `fct_riesgo` solo guarda la serie S-367 (D-PF01-08); replica `consistencia_cuadros` de `validacion.py`. Exige igualdad exacta, y una celda del cuadro sin par en el Boletín no cumple. Los valores se muestran a 2 decimales (miles de soles) o a 6 (porcentaje en P015 y P016); la diferencia, sin redondear.

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha_corte` | `DATE` | Fecha de corte |
| `hoja` | `VARCHAR2(4 CHAR)` | Hoja del Boletín y del cuadro (P009 a P016) |
| `serie_cuadro` | `VARCHAR2(10 CHAR)` | Cuadro publicado por separado: S-401 (primas), S-402 (siniestros) o S-403 (índices de siniestralidad) |
| `fila` | `NUMBER(7)` | Fila de la celda (numeración de Excel) |
| `columna` | `NUMBER(5)` | Columna de la celda (numeración de Excel) |
| `concepto` | `VARCHAR2(200 CHAR)` | Rótulo de la fila en el cuadro |
| `empresa` | `VARCHAR2(150 CHAR)` | Encabezado de la columna en el cuadro |
| `unidad` | `VARCHAR2(30 CHAR)` | Unidad de la hoja |
| `valor_boletin` | `NUMBER` | Cifra del Boletín Mensual (S-367); miles de soles a 2 decimales o porcentaje a 6 decimales (P015 y P016); nula si la celda no está en el Boletín |
| `valor_cuadro` | `NUMBER` | Cifra del cuadro S-401, S-402 o S-403; miles de soles a 2 decimales o porcentaje a 6 decimales (P015 y P016) |
| `diferencia` | `NUMBER` | valor del Boletín - valor del cuadro, sin redondear, para que una diferencia mínima no quede oculta |
| `cumple` | `BOOLEAN` | Verdadero si las dos cifras son iguales; falso si difieren o si la celda no está en el Boletín |

## 4. Reglas de carga

### 4.1 Orden de ejecución

`scripts/cargar_oracle.py` ejecuta los cinco pasos en este orden; `src/pf_01_siniestralidad_sbs/carga.py` contiene la lógica.

| Paso | Archivo o función | Qué hace | Transacción |
|---|---|---|---|
| 1 | `sql/oracle/01_ddl_tablas.sql` | Crea las tablas, llaves, restricciones CHECK, índices y comentarios | DDL; cada sentencia confirma |
| 2 | `sql/oracle/02_vistas.sql` | Crea o reemplaza las 5 vistas | DDL |
| 3 | `carga.cargar_stg` | Vacía las tablas `stg_` (TRUNCATE) y las llena desde `data/interim/` con `executemany` por lotes de 20 000 filas; después reúne sus estadísticas del optimizador | Una por tabla |
| 4 | `carga.cargar_catalogos` | Borra los hechos y reemplaza `dim_empresa`, `dim_corte`, `dim_riesgo` y las columnas de empresa de `dim_columna_empresa` desde los catálogos | Abierta, sin confirmar |
| 5 | `sql/oracle/03_carga_modelo.sql` | Llena `dim_cuadro`, `dim_cuenta`, `dim_indicador`, las columnas Total y las tres tablas de hechos; controla los conteos y confirma; luego reúne las estadísticas de `dim_` y `fct_` | Confirma los pasos 4 y 5 juntos |

Los catálogos se cargan desde Python directo a `dim_` porque son pocos (60 filas o menos) y su traducción (true y false a S y N, padre de cada riesgo) son funciones puras con pruebas en `tests/test_carga.py`; una tabla `stg_` de catálogo no aportaba control adicional. Al final, el programa informa las filas por tabla, el estado de las vistas y los cuadres de O1, y devuelve 1 si un paso falla o si alguna vista queda no válida.

### 4.2 Idempotencia y control de conteos

- `01_ddl_tablas.sql` usa `CREATE TABLE IF NOT EXISTS` y crea cada llave, restricción CHECK e índice en un bloque PL/SQL que consulta `USER_CONSTRAINTS` o `USER_INDEXES`. Los comentarios se reescriben en cada ejecución.
- `02_vistas.sql` usa `CREATE OR REPLACE VIEW` (Oracle no admite `IF NOT EXISTS` junto con `OR REPLACE`: ORA-11541).
- Los pasos 4 y 5 reemplazan los datos en una sola transacción: borran y vuelven a insertar con `INSERT ... SELECT`. Con los mismos datos, la segunda ejecución deja las mismas filas y los mismos identificadores; la huella por fila de `dim_` y `fct_` se comprobó idéntica entre dos ejecuciones y entre la base nativa y el contenedor.
- Antes del `COMMIT`, `03_carga_modelo.sql` comprueba que cada tabla de hechos tenga tantas filas como su tabla `stg_` en la serie S-367. Si no, lanza `ORA-20001` («una celda no tiene equivalencia única en alguna dimensión») y la transacción se deshace, incluidos los catálogos del paso 4.

### 4.3 Rótulos normalizados y cuentas repetidas

- Rótulo normalizado: mayúsculas, sin tildes y sin espacios repetidos, el mismo criterio que `validacion.normalizar()` y los catálogos. En SQL: `TRIM(REGEXP_REPLACE(UPPER(TRANSLATE(texto, con tilde, sin tilde)), '[[:space:]]+', ' '))`; `tests/test_carga.py` comprueba que da el mismo resultado que la función de Python.
- Una cuenta por fila de P001 y P002. Si los bloques de empresas publican rótulos distintos en la misma fila, vale el del bloque de la columna Total, que es el que suma esa fila: en P001 de diciembre de 2021, 2022 y 2023, el primer bloque (3 empresas) ya usa los rótulos del plan nuevo en 2 filas.
- En P001, 5 o 6 rótulos aparecen dos veces por corte, en la parte corriente y en la no corriente (p. ej., «Disponibles para la Venta», «Obligaciones Financieras»). La segunda aparición del rótulo en la hoja y el corte lleva el sufijo « (2)» (decisión del director, 2026-10-14). En los 9 cortes, la primera aparición es la corriente.

### 4.4 Tramos de P003

P003 publica dos tramos con las mismas empresas y casi los mismos conceptos: el primero, sin título (cifras al corte), y el segundo, titulado «Saldos Promedio Últimos 12 Meses». La carga los separa por el mayor salto de filas de la hoja, que corresponde a las notas al pie y al encabezado repetido entre los dos tramos, y asigna `dim_indicador.seccion` = `CIFRAS AL CORTE` o `SALDOS PROMEDIO ULTIMOS 12 MESES` (decisión del director, 2026-10-14). La regla se verificó en los 9 cortes: los dos tramos empiezan en «Caja y Bancos» y dentro de cada uno los rótulos no se repiten.

### 4.5 Valores que define la carga

El modelo de Data Modeler no fija estos valores; los define `03_carga_modelo.sql`:

| Hoja | `dim_cuadro.grupo` | `dim_cuadro.medida` |
|---|---|---|
| P001 | `estados_financieros` | `estado_situacion_financiera` |
| P002 | `estados_financieros` | `estado_resultados` |
| P003 | `indicadores` | `cifras_indicadores` |
| P004 | `indicadores` | `indicadores` |
| P009 | `riesgos` | `primas_netas` |
| P010 | `riesgos` | `primas_cedidas` |
| P011 | `riesgos` | `primas_retenidas` |
| P012 | `riesgos` | `siniestros_netos` |
| P013 | `riesgos` | `siniestros_cedidos` |
| P014 | `riesgos` | `siniestros_retenidos` |
| P015 | `riesgos` | `indice_siniestralidad_directa` |
| P016 | `riesgos` | `indice_siniestralidad_retenida` |

- `grupo` es la tabla de `data/interim/` de la hoja, y `medida`, el nombre de la columna de las vistas (sección 3). Una hoja nueva sin `medida` hace fallar la carga por la restricción NOT NULL.
- `dim_corte.resolucion_plan` es el número de la resolución del plan de cuentas que cita la nota al pie de P001 (`texto_de_la_nota` de `cortes.csv`): `976-2021` de diciembre de 2021 a diciembre de 2025, `085-2026` en agosto de 2026 y nulo en 2019 y 2020, cuando regía el plan anterior.
- `dim_cuenta.nivel` es el orden de la sangría dentro de la hoja (0 = sin sangría), en el corte más reciente en que aparece la cuenta.
- El título y la unidad de `dim_cuadro`, y los rótulos de `dim_cuenta` y `dim_indicador`, son los del corte más reciente.

### 4.6 Columnas de empresa y columnas Total (D-PF01-07)

- `en_total_simple` se codifica `S` o `N` (restricción CHECK); la carga traduce `true` y `false` de `empresas.csv`. Las columnas Total llevan `N`.
- `tipo_columna` toma tres valores, con restricción CHECK. `empresa` corresponde a las 32 filas de `empresas.csv`. `total_simple` corresponde a «Total» y «Total empresas de seguros». `total_ampliado` corresponde a los rótulos que empiezan por «Total +». Es la misma clasificación de `validacion.tipo_total()`.
- Las vistas reconocen las columnas Total por `tipo_columna`, no por el rótulo.

### 4.7 Solo la serie S-367 en `fct_riesgo` (D-PF01-08)

La llave primaria de `fct_riesgo` no incluye la serie, así que la tabla guarda solo el Boletín Mensual (S-367): 78 064 de las 86 842 filas de `stg_riesgos`. Las 8 778 celdas de S-401, S-402 y S-403 se quedan en `stg_riesgos` y se comparan con el Boletín en `vw_cuadre_cuadros_sbs`.

### 4.8 Conexión y bases

- Base nativa por defecto (D-PF01-03): `localhost:1521/FREEPDB1`, Oracle 23.6.
- Contenedor: `--base contenedor` usa `ORACLE_DSN` de `.env` (`localhost:1522/FREEPDB1`, imagen `gvenzl/oracle-free:23.26.3`); `--dsn` indica otra base.
- Usuario y contraseña: `ORACLE_USER` y `ORACLE_PASSWORD` del entorno o de `.env`; nunca se imprimen. Conexión con python-oracledb en modo Thin.
- `scripts/ejecutar_sql.py <archivo.sql> [--base contenedor]` ejecuta un solo script con la misma separación de sentencias que SQL*Plus y SQLcl.
- Notebook: `PF01_BASE` (`nativa` por omisión o `contenedor`) elige la base en `notebooks/01-jc-exploracion.ipynb`.

## 5. Cómo reconstruir la base

Requisitos: Docker Desktop, uv, el archivo `.env` (copia de `.env.example` con `ORACLE_SYS_PASSWORD`, `ORACLE_USER`, `ORACLE_PASSWORD` y `ORACLE_DSN`) y `data/interim/`, que genera `scripts/descargar_sbs.py`.

En el contenedor (validación final y reproducción):

```bash
docker compose up -d
uv sync --locked
uv run python scripts/descargar_sbs.py
uv run python scripts/cargar_oracle.py --base contenedor
```

En la base nativa de desarrollo (D-PF01-03):

```bash
uv run python scripts/cargar_oracle.py
```

Resultados esperados (carga del 2026-10-14, iguales en las dos bases):

| Tabla | Filas |
|---|---|
| `stg_estados_financieros` · `stg_indicadores` · `stg_riesgos` | 50 790 · 15 086 · 86 842 |
| `dim_columna_empresa` · `dim_corte` · `dim_cuadro` | 38 · 9 · 12 |
| `dim_cuenta` · `dim_empresa` · `dim_indicador` · `dim_riesgo` | 127 · 20 · 126 · 60 |
| `fct_estado_financiero` · `fct_indicador` · `fct_riesgo` | 50 790 · 15 086 · 78 064 |

| Cuadre de O1 | Filas | Cumplen |
|---|---|---|
| `vw_cuadre_balance` | 168 | 168 (100 %) |
| `vw_cuadre_totales` | 7 196 | 7 196 (100 %) |
| `vw_cuadre_cuadros_sbs` | 8 778 | 8 778 (100 %) |

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d).

El programa termina con código 0 y las 5 vistas en estado VALID. Una ejecución completa tarda de 30 a 70 segundos. La prueba de integración `tests/test_carga_oracle.py` repite estas comprobaciones contra la base que indiquen `ORACLE_USER`, `ORACLE_PASSWORD` y `ORACLE_DSN` en el entorno, y se omite si faltan esas variables, como en GitHub Actions.

## 6. Observaciones de estructura (verificadas el 2026-10-11)

| Tema | Observación | Tratamiento |
|---|---|---|
| Formato de los libros | `.xlsx` (2021, 2022, 2024, ago-2025, ago-2026), `.xlsm` (2023) y `.xls` BIFF (2020 y dic-2025); el libro de 2019 tiene extensión `.xls`, pero es `.xlsx` | El motor de lectura se elige por la firma del archivo |
| Nombres de hoja | Diciembre de 2020 publica «P003 » y «P004 » con espacio final | Se normalizan |
| Encabezados | La fila de encabezado está entre la 4 y la 7 según la hoja y el corte; P003 repite el encabezado a mitad de hoja con llamadas propias | Se detecta en cada hoja y se usa el encabezado vigente para cada tramo |
| Empresas absorbidas o en liquidación | En P009 a P014, diciembre de 2020 agrega `Rigel (1)`, `Coface Seguros (2)` y `Total + Rigel + Coface Seguros (3)`; diciembre de 2022 agrega `Mapfre Perú (abs) (2)` y `Total + Mapfre Perú (abs) (3)` | Se conservan con `es_total`; qué total usar para los cuadres se decide en 2.2 |
| Indicadores de solvencia | En diciembre de 2019, 2021 y 2023, P004 no publica los seis primeros indicadores de solvencia (de «Patrimonio Efectivo / Requerimientos Patrimoniales» a «Reservas Técnicas / Patrimonio Efectivo») | No generan filas |
| Consistencia | P009 a P016 de agosto de 2026 coinciden celda por celda con S-401, S-402 y S-403 (8 778 celdas, diferencia máxima 0) | Prueba en `tests/test_datos_sbs.py` |

## 7. Catálogos versionados (`src/pf_01_siniestralidad_sbs/catalogos/`)

Se versionan en Git porque son decisiones del proyecto, no datos de la fuente. El paquete 2.3 los carga como dimensiones en Oracle (sección 4.1).

### 7.1 `empresas.csv` · Tabla de equivalencias de empresas

Una fila por rótulo de la fuente y rango de cortes. Una columna de empresa de cualquier hoja se asigna con su rótulo normalizado (mayúsculas, sin tildes) y el corte.

| Columna | Descripción |
|---|---|
| `clave_fuente` | Rótulo normalizado tal como aparece en la fuente (p. ej., `SECREX`, `MAPFRE PERU (ABS)`) |
| `corte_desde`, `corte_hasta` | Rango de cortes en que el rótulo tiene esa equivalencia |
| `empresa_id`, `empresa` | Empresa para el análisis en el tiempo, con su denominación vigente (p. ej., `CESCE`, Cesce Perú) |
| `entidad` | Denominación en ese período, según las notas al pie de la SBS; si la nota no la da, el rótulo publicado |
| `estado` | `vigente`, `liquidada` o `absorbida` en ese corte |
| `en_total_simple` | `false` en las columnas de flujos de empresas que dejaron de operar en el año (decisión D-PF01-01) |
| `evento`, `fuente_evento` | Cambio de denominación, fusión o liquidación y la resolución SBS que lo autoriza |

Equivalencias que cambian el análisis por empresa: Ohio National Vida pasa a AuguStar (2025), Secrex a Cesce Perú (2025), Vida Cámara a Vivir Seguros (2021) y Cardif a BNP Paribas Cardif (solo el rótulo); Mapfre Perú y Mapfre Perú Vida se agrupan como Mapfre Perú por la fusión de 2022. Rigel y Coface Seguros se liquidaron en 2020 y no tienen sucesora.

### 7.2 `riesgos.csv` · Catálogo de riesgos

| Columna | Descripción |
|---|---|
| `riesgo_id`, `clave`, `riesgo` | Orden, rótulo normalizado y rótulo vigente (agosto de 2026) |
| `nivel`, `clave_padre` | Jerarquía de cinco niveles: TOTAL, ramo, subgrupo de vida, riesgo y detalle |
| `tipo` | `total`, `agregado`, `riesgo` (50 filas que suman el total) o `detalle` («del cual», no suma) |
| `ramo` | Ramos generales, Ramos de accidentes y enfermedades o Ramos de vida |
| `riesgo_comparable` | Agrupación para comparar en el tiempo: Cauciones y las dos filas de Fianzas forman «Cauciones y fianzas» |
| `corte_desde`, `nota` | Primer corte en que se publica y observaciones |

Observaciones del catálogo:
- El Seguro del Sistema Privado de Pensiones suma Renta de Jubilados, Seguros Previsionales, Pensiones de Invalidez y Pensiones de Sobrevivencia.
- El «Seguro de Invalidez, Sobrevivencia y Gastos de Sepelio» es un detalle de Seguros Previsionales; en las hojas de siniestros (P012 a P014) se abre a su vez en una fila por cada uno de esos tres componentes.
- Las dos filas de Fianzas se publican desde diciembre de 2023. Ese año, las primas de Cauciones bajaron de 420 667 a 155 098 mil soles y aparecieron 299 897 mil soles en «Fianzas que garantizan otras obligaciones» (SBS, s. f.-a): es una reclasificación, por lo que Cauciones solo se compara en el tiempo junto con las Fianzas.
- Las diferencias de rótulo entre cortes («Miscelaneos», «Vida Ley ex-trabajadores») se resuelven con el rótulo normalizado.

### 7.3 `cortes.csv` y `excepciones.csv`

`cortes.csv` registra, por corte, los meses acumulados (12 u 8) y la versión del plan de cuentas: anterior a la Resolución SBS N.º 976-2021 (2019 y 2020), Resolución SBS N.º 976-2021 (desde junio de 2021) y Resolución SBS N.º 085-2026 (desde marzo de 2026). `excepciones.csv` documenta las diferencias de la propia fuente que los controles informan sin tratarlas como fallas.

## 8. Controles de validación (paquete 2.2)

Se ejecutan con `uv run python scripts/validar_datos.py`, que escribe `reports/validacion_datos.md`, y con `uv run pytest` cuando hay datos en `data/interim/`. Tolerancia: 1 mil soles. Los tres cuadres de O1 se repiten en Oracle con las vistas de la sección 3.

| Control | Regla |
|---|---|
| Estructura por corte | 12 hojas por corte; toda columna de empresa tiene una sola equivalencia y todo riesgo está en el catálogo |
| Cuadre con los totales publicados | Suma de las empresas en operación = «Total»; suma de todas las columnas de empresa = «Total + …» (D-PF01-01), en P001 a P003 y P009 a P014 |
| Jerarquía de riesgos | Cada agregado = suma de sus componentes, por columna, en P009 a P014 |
| Activo = Pasivo + Patrimonio | Por corte y empresa en moneda TOTAL; Pasivo + Patrimonio = «Total pasivo y patrimonio» también en MN y ME |
| MN + ME = TOTAL | Por fila y empresa en P001 y P002, salvo la utilidad por acción (en soles por acción) |
| Boletín frente a S-401, S-402 y S-403 | Igualdad exacta de P009 a P016 en agosto de 2026 |
| Cifras acumuladas en el año | Razón diciembre / agosto de 2025 de los totales de flujo entre 1.3 y 1.7 (12 / 8 = 1.5) |
| Versión del plan de cuentas | La nota al pie de P001 cita la resolución registrada para el corte |

Excepciones de la fuente: en P001 de diciembre de 2021, 2022 y 2023, la fila «Pérdida neta no realizada por valorización de las inversiones disponibles para la venta» de Avla Perú publica en TOTAL un monto que no figura en MN ni en ME (de −361.983, −282.818 y −141.053 mil soles), y la diferencia se arrastra al total de empresas.

## Referencias

Superintendencia de Banca, Seguros y AFP. (s. f.-a). *Boletín mensual* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-367

Superintendencia de Banca, Seguros y AFP. (s. f.-b). *Índice de siniestralidad directa y retenida según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-403

Superintendencia de Banca, Seguros y AFP. (s. f.-c). *Primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-401

Superintendencia de Banca, Seguros y AFP. (s. f.-d). *Siniestros de primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-402
