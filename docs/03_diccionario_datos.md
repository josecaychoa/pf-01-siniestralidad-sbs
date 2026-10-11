# Diccionario de datos · PF-01

`Portafolio · PF-01` · Versión 0.2 · 2026-10-11 · Paquetes 2.1 (tablas intermedias) y 2.2 (catálogos y validación). Las tablas del modelo Oracle se agregan en el paquete 2.3.

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

## 3. Catálogos versionados (`src/pf_01_siniestralidad_sbs/catalogos/`)

Se versionan en Git porque son decisiones del proyecto, no datos de la fuente. El paquete 2.3 los carga como dimensiones en Oracle.

### 3.1 `empresas.csv` · Tabla de equivalencias de empresas

Una fila por rótulo de la fuente y rango de cortes. Una columna de empresa de cualquier hoja se asigna con su clave normalizada (mayúsculas, sin tildes) y el corte.

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

### 3.2 `riesgos.csv` · Catálogo de riesgos

| Columna | Descripción |
|---|---|
| `riesgo_id`, `clave`, `riesgo` | Orden, clave normalizada y rótulo vigente (agosto de 2026) |
| `nivel`, `clave_padre` | Jerarquía de cinco niveles: TOTAL, ramo, subgrupo de vida, riesgo y detalle |
| `tipo` | `total`, `agregado`, `riesgo` (50 filas que suman el total) o `detalle` («del cual», no suma) |
| `ramo` | Ramos generales, Ramos de accidentes y enfermedades o Ramos de vida |
| `riesgo_comparable` | Agrupación para comparar en el tiempo: Cauciones y las dos filas de Fianzas forman «Cauciones y fianzas» |
| `corte_desde`, `nota` | Primer corte en que se publica y observaciones |

Observaciones del catálogo:
- El Seguro del Sistema Privado de Pensiones suma Renta de Jubilados, Seguros Previsionales, Pensiones de Invalidez y Pensiones de Sobrevivencia. El «Seguro de Invalidez, Sobrevivencia y Gastos de Sepelio» es un detalle de Seguros Previsionales, y en las hojas de siniestros (P012 a P014) se abre a su vez en Invalidez, Sobrevivencia y Gastos de Sepelio.
- Las dos filas de Fianzas se publican desde diciembre de 2023. Ese año, las primas de Cauciones bajaron de 420 667 a 155 098 mil soles y aparecieron 299 897 mil soles en «Fianzas que garantizan otras obligaciones» (SBS, s. f.-a): es una reclasificación, por lo que Cauciones solo se compara en el tiempo junto con las Fianzas.
- Las diferencias de rótulo entre cortes («Miscelaneos», «Vida Ley ex-trabajadores») se resuelven con la clave normalizada.

### 3.3 `cortes.csv` y `excepciones.csv`

`cortes.csv` registra, por corte, los meses acumulados (12 u 8) y la versión del plan de cuentas: anterior a la Resolución SBS N.º 976-2021 (2019 y 2020), Resolución SBS N.º 976-2021 (desde junio de 2021) y Resolución SBS N.º 085-2026 (desde marzo de 2026). `excepciones.csv` documenta las diferencias de la propia fuente que los controles informan sin tratarlas como fallas.

## 4. Controles de validación (paquete 2.2)

Se ejecutan con `uv run python scripts/validar_datos.py`, que escribe `reports/validacion_datos.md`, y con `uv run pytest` cuando hay datos en `data/interim/`. Tolerancia: 1 mil soles.

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
