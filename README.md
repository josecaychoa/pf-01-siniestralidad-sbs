# PF-01 · Producción y siniestralidad por riesgo del mercado asegurador peruano, 2019-2026

`Portafolio · PF-01` · José Caycho A. · octubre de 2026

> En agosto de 2026, la siniestralidad directa del sistema asegurador peruano subió a 48.9 %, 7.5 puntos porcentuales (p. p.) más que un año antes, con primas que crecieron 9.0 % (Superintendencia de Banca, Seguros y AFP [SBS], s. f.-a). Este repositorio reproduce el análisis completo, de la descarga de los boletines al tablero, y deja los indicadores validados en 9.9 minutos por corte, frente a los 95.0 del proceso manual.

## Problema

¿Qué riesgos del sistema asegurador peruano crecen en primas con una siniestralidad mayor que la del conjunto, y cómo evolucionó el índice del sistema entre 2019 y 2026? Es una pregunta de monitoreo del mercado que un analista responde cada mes con los boletines de la SBS (s. f.-a). El proyecto la contesta con un flujo reproducible que valida sus propias cifras y separa, en una matriz de cuadrantes, los riesgos que crecen con siniestralidad contenida de los que crecen por encima del corte del sistema. El alcance describe cifras agregadas por riesgo; excluye juicios sobre la gestión de las empresas y cualquier dato personal ([`docs/01_acta.md`](docs/01_acta.md), sección 4).

## Datos

| Fuente | Documento o serie | Fecha de corte | Condiciones de uso |
|---|---|---|---|
| SBS | Boletín mensual (S-367), 9 cortes | Diciembre de 2019 a 2025 y agosto de 2025 y 2026 | No declaradas (ver nota) |
| SBS | S-401 · Primas de seguros netas, cedidas y retenidas según riesgos | 2026-08-31 | No declaradas |
| SBS | S-402 · Siniestros de primas de seguros netas, cedidas y retenidas según riesgos | 2026-08-31 | No declaradas |
| SBS | S-403 · Índice de siniestralidad directa y retenida según riesgos | 2026-08-31 | No declaradas |

Los datos se descargaron el 11 de octubre de 2026 con `uv run python scripts/descargar_sbs.py`; los archivos originales no se versionan y [`data/raw/manifest.csv`](data/raw/manifest.csv) registra la URL, la fecha de descarga y la huella SHA-256 de cada uno. Sobre las condiciones de uso: el portal de la SBS indica «Todos los derechos reservados» y su página de datos abiertos no declara una licencia, así que el proyecto publica solo agregados propios con su cita y no redistribuye los archivos originales (detalle en [`data/README.md`](data/README.md)). Este proyecto no usa datos personales.

## Método

El flujo de datos tiene tres etapas ETL (extracción, transformación y carga) y una de consumo (figura 1). El detalle de cada etapa, las decisiones de diseño y el modelo relacional están en [`docs/04_arquitectura.md`](docs/04_arquitectura.md).

1. Extracción: `scripts/descargar_sbs.py` descarga los boletines por HTTPS, los guarda sin modificar en `data/raw/` y los contrasta con el manifiesto.
2. Transformación: `src/pf_01_siniestralidad_sbs/extraccion.py` lleva las hojas a formato largo en `data/interim/`; los catálogos resuelven empresas, riesgos, cortes y excepciones, y `scripts/validar_datos.py` aplica los controles de cuadre y de estructura.
3. Carga: `scripts/cargar_oracle.py` puebla en Oracle las 3 tablas `stg_`, las 7 dimensiones `dim_`, las 3 tablas de hechos `fct_` y las 12 vistas `vw_` de `sql/oracle/`.
4. Consumo: `scripts/exportar_indicadores.py` escribe los CSV versionados de `data/processed/` que leen el informe, las figuras y el tablero Power BI.

**Figura 1**

*Arquitectura del flujo de datos de PF-01*

![Arquitectura del flujo de datos de PF-01](docs/diagramas/PF-01_arquitectura.svg)

*Nota.* Elaboración propia.

El proceso que el proyecto reemplaza y el que propone están modelados en BPMN 2.0 con Bizagi Modeler 4.3 (figuras 2 y 3). El AS-IS es un supuesto declarado, la elaboración manual del reporte en hoja de cálculo, y no describe la práctica de una empresa en particular. En el TO-BE, seis tareas de servicio, que son los scripts del repositorio, reemplazan la descarga, la copia, la homologación, el cálculo y el cuadre manuales. La tabla 1 compara el tiempo de una actualización con un corte nuevo, desde la publicación del boletín hasta los indicadores validados. Los diagramas conservan el formato estándar de Bizagi (D-PF01-20); el modelo editable, un archivo BPMN por diagrama y la documentación en PDF están en [`docs/procesos/`](docs/procesos/).

**Figura 2**

*Proceso actual (AS-IS) del reporte de siniestralidad por riesgo*

![Proceso actual (AS-IS) del reporte de siniestralidad por riesgo](docs/procesos/PF-01_proceso_asis.svg)

*Nota.* Elaboración propia con base en un supuesto declarado: elaboración manual en hoja de cálculo.

**Tabla 1**

*Tiempo de una actualización con un corte nuevo, AS-IS frente a TO-BE, por actividad*

| Actividad | AS-IS (min) | TO-BE (min) | Ahorro (min) | Ahorro (%) |
|---|---:|---:|---:|---:|
| Obtención | 6.0 | 0.7 | 5.3 | 88.5 % |
| Consolidación | 46.0 | 1.5 | 44.5 | 96.7 % |
| Cálculo | 15.0 | 0.8 | 14.2 | 94.5 % |
| Control | 28.0 | 6.8 | 21.2 | 75.6 % |
| **Total** | **95.0** | **9.9** | **85.1** | **89.6 %** |

*Nota.* AS-IS: estimación del autor con las cantidades del proyecto y tiempos unitarios declarados. TO-BE: mediana de tres corridas medidas del flujo del repositorio el 2026-10-19, que reprocesa los 9 cortes e incluye la pausa de 2 s entre descargas, más 6 min estimados de lectura de las dos notas de validación. Equipo: Intel Core i7-1355U, 15.7 GB de RAM, Windows 11 Pro y Oracle Database 23ai Free 23.6. Las cifras se redondean a un decimal, por lo que la suma de las filas puede diferir del total. Detalle por tarea en [`PF-01_tiempos.csv`](docs/procesos/PF-01_tiempos.csv); versión con la identidad visual en [SVG](docs/procesos/PF-01_tiempos.svg) y [PDF](docs/procesos/PF-01_tiempos.pdf), generada con `scripts/figura_tiempos.py`. Elaboración propia.

**Figura 3**

*Proceso propuesto (TO-BE) del reporte de siniestralidad por riesgo*

![Proceso propuesto (TO-BE) del reporte de siniestralidad por riesgo](docs/procesos/PF-01_proceso_tobe.svg)

*Nota.* Elaboración propia. Las tareas de servicio son los scripts del repositorio; el ahorro de la anotación proviene de la tabla 1.

## Gestión del proyecto

| Elemento | Archivo |
|---|---|
| Acta y objetivos SMART | [`docs/01_acta.md`](docs/01_acta.md) |
| EDT y Gantt de la línea base v1.0 (vista resumida, congelada al aprobar el plan) | [`docs/02_edt_gantt.md`](docs/02_edt_gantt.md) |
| Gantt de Microsoft Project con el avance real (PDF, se actualiza en cada registro de avance) | [`gestion/cronograma/PF-01_seguimiento.pdf`](gestion/cronograma/PF-01_seguimiento.pdf) |
| Gantt de la línea base v1.0 en Microsoft Project (PDF, fijado el 2026-10-11) | [`gestion/cronograma/PF-01_linea_base.pdf`](gestion/cronograma/PF-01_linea_base.pdf) |
| Cronograma de Microsoft Project (`.mpp` y XML) | [`gestion/cronograma/`](gestion/cronograma/) |
| Arquitectura del flujo de datos y modelo relacional | [`docs/04_arquitectura.md`](docs/04_arquitectura.md) |
| Procesos AS-IS y TO-BE en Bizagi (`.bpm`, BPMN 2.0, SVG y PDF) y tabla de tiempos (CSV, SVG y PDF) | [`docs/procesos/`](docs/procesos/) |
| Cierre, desvíos y lecciones | [`docs/05_cierre_lecciones.md`](docs/05_cierre_lecciones.md) |

## Resultados

La siniestralidad directa del sistema pasó de 53.0 % en diciembre de 2019 a un máximo de 59.3 % en diciembre de 2021, bajó en los cuatro cortes anuales siguientes hasta 39.4 % en diciembre de 2025 y repuntó a 48.9 % en agosto de 2026, 7.5 p. p. por encima de agosto de 2025; la retenida cerró en 45.7 % (figura 4). Las primas netas acumuladas del corte llegaron a 16 784.7 millones de soles, 9.0 % más que un año antes (SBS, s. f.-a, s. f.-b, s. f.-c, s. f.-d).

**Figura 4**

*Índice de siniestralidad del sistema asegurador peruano por corte, 2019-2026*

![Serie 2019-2026 del índice de siniestralidad del sistema: la directa sube a 48.9 % en agosto de 2026, 7.5 puntos porcentuales más que en agosto de 2025; la retenida llega a 45.7 %](reports/figures/PF-01_serie.svg)

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d). Figura y tabla de la serie generadas con `uv run python scripts/figura_serie.py`; los puntos huecos marcan los cortes de agosto (8 meses acumulados).

De los 48 riesgos del corte, 35 quedan clasificados en la matriz de cuadrantes: 9 crecen con una siniestralidad directa mayor que el corte de 44.0 % y concentran 5 305.3 millones de soles de primas, con Vida Individual de Largo Plazo, Asistencia Médica y Vehículos a la cabeza (83.7 % del cuadrante). La figura 5 muestra la página «Matriz de riesgos» del tablero Power BI, cuya segmentación «Medida» alterna entre la siniestralidad directa y la retenida ([`dashboards/powerbi/README.md`](dashboards/powerbi/README.md)). Las tablas completas, la lectura con la medida retenida y las conclusiones están en el informe de resultados ([`reports/informe.md`](reports/informe.md)).

**Figura 5**

*Matriz de riesgos con la siniestralidad directa, agosto de 2026*

![Página «Matriz de riesgos» del tablero con la medida Directa: 9 de 35 riesgos crecen con una siniestralidad directa mayor que el corte de 44.0 %](reports/figures/PF-01_tablero_directa.png)

*Nota.* Elaboración propia con datos de SBS (s. f.-a). Los ejes se recortan en 60 % de variación y 100 % de siniestralidad (D-PF01-13): 3 de los 35 riesgos clasificados quedan fuera de escala y no se dibujan, aunque cuentan en las tablas.

## Cómo reproducir

Sin Oracle, con [uv](https://docs.astral.sh/uv/) instalado (verificado desde un clon limpio el 26 de octubre de 2026: 129 pruebas superadas y 50 omitidas en 3 s):

```bash
git clone https://github.com/josecaychoa/pf-01-siniestralidad-sbs.git
cd pf-01-siniestralidad-sbs
uv sync --locked
uv run pytest
```

Las 50 pruebas omitidas son las de integración, que requieren la base Oracle o los archivos de `data/raw/`. El flujo completo las habilita y requiere Docker:

```bash
cp .env.example .env            # completar las variables locales
docker compose up -d
uv run python scripts/descargar_sbs.py
uv run python scripts/cargar_oracle.py --base contenedor
uv run python scripts/exportar_indicadores.py --base contenedor
uv run pytest
```

Los conteos de filas y los cuadres esperados tras la carga están en el diccionario de datos ([`docs/03_diccionario_datos.md`](docs/03_diccionario_datos.md), sección 5). El tablero no necesita Oracle: lee los CSV versionados de `data/processed/` y se abre con Power BI Desktop en Windows según la guía de [`dashboards/powerbi/README.md`](dashboards/powerbi/README.md).

## Estructura

```text
├── assets/                        # estilo matplotlib y tema de Power BI de la marca
├── dashboards/powerbi/            # tablero en formato PBIP (informe PBIR y modelo TMDL)
├── data/                          # raw (inmutable, no versionada), interim y processed (CSV versionados)
├── docs/                          # acta · EDT y Gantt · diccionario · arquitectura · diagramas · modelo · procesos
├── gestion/cronograma/            # cronograma de Microsoft Project (.mpp, XML y PDF)
├── notebooks/                     # exploración de las vistas vw_
├── reports/                       # informe de resultados, notas de validación y figuras
├── scripts/                       # descarga, validación, carga, exportación, figuras y lint de texto
├── sql/oracle/                    # scripts idempotentes: DDL · vistas · carga (prefijos stg_, dim_, fct_, vw_)
├── src/pf_01_siniestralidad_sbs/  # paquete Python del flujo
└── tests/                         # 179 pruebas (129 se ejecutan sin Oracle)
```

## Limitaciones

- Los cortes de agosto acumulan 8 meses y los de diciembre, 12; el índice no está anualizado, así que las comparaciones interanuales válidas son entre cortes del mismo mes.
- La matriz usa un solo corte (agosto de 2026). Para otro corte hay que regenerar los CSV con `uv run python scripts/exportar_indicadores.py`.
- 5 riesgos previsionales y 8 riesgos bajo el umbral de materialidad quedan fuera de la clasificación por cuadrante; en diciembre de 2020, 5 celdas del índice publicado difieren del calculado porque la fuente usó el Total simple (D-PF01-18).
- Los índices describen montos agregados por riesgo: no miden rentabilidad técnica ni suficiencia de primas.
- Este análisis tiene fines demostrativos y no constituye asesoría regulatoria, actuarial ni financiera.

## Referencias

Superintendencia de Banca, Seguros y AFP. (s. f.-a). *Boletín mensual* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-367

Superintendencia de Banca, Seguros y AFP. (s. f.-b). *Índice de siniestralidad directa y retenida según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-403

Superintendencia de Banca, Seguros y AFP. (s. f.-c). *Primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-401

Superintendencia de Banca, Seguros y AFP. (s. f.-d). *Siniestros de primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-402

## Licencia

Código bajo licencia MIT. Los datos conservan las condiciones de uso de su fuente original.

## Autor

José Caycho A. · Business Analyst Senior · Procesos · Datos
linkedin.com/in/jcaychoasin · github.com/josecaychoa
