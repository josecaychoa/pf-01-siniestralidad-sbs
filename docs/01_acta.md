# Acta de constitución · PF-01: Producción y siniestralidad por riesgo del mercado asegurador peruano, 2019-2026

`Portafolio · PF-01` · Versión 1.5 · 2026-10-21

| Campo | Valor |
|---|---|
| ID / Repositorio | PF-01 / github.com/josecaychoa/pf-01-siniestralidad-sbs |
| Director del proyecto | José Caycho A. |
| Issue padre | #1 |
| Fechas planificadas | Planificación: 2026-10-12 a 2026-10-16 · Ejecución y cierre: 2026-11-02 a 2026-11-26 |
| Publicación en LinkedIn | Jueves 2026-11-26, 08:00 (hora de Lima) |
| Esfuerzo estimado | 34.0 h: 28.5 h de núcleo (incluye el tablero Power BI, 4 h, y el modelo lógico y relacional del Data Modeler, 1.5 h) y 5.5 h opcionales (arquitectura en Visio, 2 h; proceso en Bizagi, 3.5 h) |
| Estado | Aprobado el 2026-10-11 |

## 1. Problema de negocio

Las empresas de seguros del Perú reportan a la Superintendencia de Banca, Seguros y AFP (SBS) sus estados financieros y sus primas y siniestros por riesgo y por empresa, y la SBS los publica cada mes en el Boletín Estadístico de Seguros (Superintendencia de Banca, Seguros y AFP [SBS], s. f.-a). La información llega en hojas separadas, en formato ancho, con una columna por empresa y cifras acumuladas en el año. Con esa forma cuesta responder una pregunta básica de suscripción: qué ramos crecen en primas y cuáles deterioran su siniestralidad al mismo tiempo.

El análisis sirve a un gerente técnico, a un analista de riesgos o a un supervisor para priorizar la revisión de los requisitos de suscripción y de la tarifa por ramo. Un ramo que crece con siniestralidad en alza es el primer candidato a revisión; uno que crece con siniestralidad estable o a la baja es candidato a expansión. La apertura por empresa muestra si el movimiento del ramo es general o se concentra en pocas compañías.

## 2. Objetivo general

Construir una base reproducible con los estados financieros, los indicadores y la producción y siniestralidad por riesgo y por empresa del sistema asegurador peruano, de 2019 a agosto de 2026, y clasificar los riesgos según el crecimiento de sus primas y su siniestralidad.

## 3. Objetivos SMART

| ID | Objetivo (específico, medible, alcanzable, relevante, con plazo) | Indicador de logro | Fecha |
|---|---|---|---|
| O1 | Construir en Oracle una base reproducible a partir del Boletín Mensual de la SBS (S-367) para 9 cortes (diciembre de 2019 a diciembre de 2025, agosto de 2025 y agosto de 2026), con: (a) el estado de situación financiera, el estado de resultados, las cifras consideradas en la elaboración de los indicadores y los indicadores, por empresa de seguros (hojas P001 a P004); y (b) las primas netas, cedidas y retenidas, los siniestros netos, cedidos y retenidos y los índices de siniestralidad directa y retenida, por riesgo y por empresa (hojas P009 a P016) | El 100 % de los totales calculados cuadra con las columnas Total publicadas, con una tolerancia de 1 mil soles por redondeo; el estado de situación financiera cumple Activo = Pasivo + Patrimonio por empresa; las hojas P009 a P016 de agosto de 2026 coinciden con los cuadros S-401, S-402 y S-403 publicados por separado | 2026-11-09 |
| O2 | Clasificar en una matriz de cuatro cuadrantes todos los riesgos con primas netas de al menos S/ 5 millones en el corte, según el crecimiento de sus primas netas (agosto de 2026 frente a agosto de 2025, y tasa de crecimiento anual compuesta 2019-2025) y su siniestralidad directa y retenida | La siniestralidad calculada replica el índice total del sistema publicado en la hoja P015 (S-403) con una diferencia no mayor de 0.1 puntos porcentuales | 2026-11-16 |
| O3 | Publicar el release v1.0.0, el README, el documento PDF de 6 a 8 páginas y el post de LinkedIn | URL del post y corte Cierre registrados en el tablero de indicadores. Meta de seguimiento, no de aceptación: tasa de interacción mayor que 5 % en el Día 30 | 2026-11-26 |

## 4. Alcance

**Incluye:**
- El Boletín Mensual de la SBS (S-367) de los 9 cortes de O1: hojas P001 a P004 (estados financieros, cifras para indicadores e indicadores por empresa) y P009 a P016 (primas, siniestros e índices de siniestralidad por riesgo y por empresa).
- Los cuadros S-401, S-402 y S-403 de agosto de 2026, solo como prueba de consistencia con el Boletín Mensual.
- Un script de descarga reproducible que registra la URL, la fecha de descarga y el SHA-256 de cada archivo.
- La transformación de las hojas a formato largo, con la moneda (MN, ME y total) en los estados financieros, y una tabla de equivalencias de empresas que recoge los cambios de razón social, las fusiones y las liquidaciones que la SBS anota al pie.
- El modelo de datos en Oracle AI Database 26ai Free, en un contenedor local, con vistas analíticas, y su modelo lógico y relacional en Oracle SQL Developer Data Modeler (`docs/modelo/`, con diagramas en `docs/diagramas/`; incluido por control de cambios del 2026-10-11, D-PF01-04).
- Los indicadores del análisis: crecimiento interanual y tasa de crecimiento anual compuesta de las primas netas, siniestralidad directa y retenida, participación de cada empresa en el riesgo y matriz de cuatro cuadrantes.
- Un umbral de materialidad de S/ 5 millones de primas netas acumuladas en el corte, tanto para los riesgos de la matriz como para las celdas empresa × riesgo.
- Informe, README, cronograma con línea base en Microsoft Project, post y documento PDF.
- Tablero Power BI en formato PBIP (paquete 4.1; núcleo desde el 2026-10-14, D-PF01-10).
- Arquitectura en Visio (paquete 2.4): una página con la arquitectura del flujo de datos por etapas ETL y consumo, exportada a SVG y PDF en `docs/diagramas/`; el modelo relacional se publica con el diagrama del Data Modeler (incluido por control de cambios del 2026-10-11; alcance ajustado el 2026-10-14, D-PF01-09).
- Proceso AS-IS y TO-BE en Bizagi (paquete 3.4): elaboración manual del reporte de siniestralidad por riesgo frente al flujo reproducible del proyecto, con el modelo `.bpm`, un BPMN por diagrama, SVG y PDF en `docs/procesos/` (incluido por control de cambios del 2026-10-11). Desde el 2026-10-18 incluye una tabla de tiempos por actividad, AS-IS frente a TO-BE (D-PF01-19, con su enmienda del 2026-10-19: AS-IS estimado por el autor y TO-BE medido), y los diagramas conservan el formato estándar de Bizagi (D-PF01-20).

**Excluye:**
- Datos personales reales.
- Cualquier dato, código o material confidencial de empleadores, clientes o terceros.
- Juicios sobre la gestión, la solvencia o la calidad de servicio de las empresas: el análisis describe cifras públicas.
- La interpretación de los estados financieros y de los indicadores de solvencia, rentabilidad y gestión: PF-01 los carga y valida en la base, y su análisis queda para PF-02 (solvencia y reservas) y PF-03 (ratio combinado y rentabilidad).
- La comparación de rubros contables entre cortes con planes de cuentas distintos (la SBS anota cambios desde junio de 2021 y desde marzo de 2026).
- Series mensuales obtenidas por diferencia de acumulados, estacionalidad y proyecciones.
- Las demás hojas del Boletín Mensual (rankings, reservas, retribuciones, gastos de administración y estructuras porcentuales).
- La interpretación actuarial de los riesgos de rentas y del Sistema Privado de Pensiones: aparecen en la matriz con una nota que explica por qué su siniestralidad no es comparable con la de los ramos generales.

## 5. Fuentes de datos

| Fuente | Documento o serie | Fecha de corte | Condiciones de uso | Cita en el texto (APA 7) |
|---|---|---|---|---|
| SBS | S-367 · Boletín Mensual: un ZIP por corte con un libro Excel de 33 hojas; se usan P001 a P004 y P009 a P016 (miles de soles; índices en porcentaje) | 31 de diciembre de 2019 a 2025; 31 de agosto de 2025 y de 2026 | No declaradas (ver nota) | (SBS, s. f.-b) |
| SBS | S-401 · Primas de seguros netas, cedidas y retenidas según riesgos | 31 de agosto de 2026 (prueba de consistencia) | No declaradas (ver nota) | (SBS, s. f.-e) |
| SBS | S-402 · Siniestros de primas de seguros netas, cedidas y retenidas según riesgos | Ídem | No declaradas (ver nota) | (SBS, s. f.-f) |
| SBS | S-403 · Índice de siniestralidad directa y retenida según riesgos | Ídem | No declaradas (ver nota) | (SBS, s. f.-d) |

**Notas sobre las fuentes (verificadas el 2026-10-10):**
- Los 9 boletines mensuales y los 27 cuadros individuales de los 9 cortes responden en el servidor de la SBS. El ZIP de agosto de 2026 contiene el libro `Avance 2026 08_act.xlsx` (33 hojas), actualizado el 5 de octubre de 2026; los ZIP de los demás cortes pesan entre 265 KB y 783 KB, y su estructura interna se verifica en el paquete 2.1.
- Las hojas P009 a P016 del Boletín Mensual tienen los mismos títulos que los cuadros S-401, S-402 y S-403: 18 empresas y una columna Total.
- Las hojas P001 (estado de situación financiera) y P002 (estado de resultados) se organizan en bloques de tres empresas, con columnas de moneda nacional, moneda extranjera y total. P003 (cifras para indicadores) y P004 (indicadores) tienen una columna por empresa; P004 declara «Información actualizada al 22/09/2026».
- Las cifras son acumuladas en el año. Se infiere del rótulo «Al 31 de Agosto del 2026» y de la magnitud de los totales, y se confirma en el paquete 2.2.
- **Condiciones de uso:** el portal indica «Todos los derechos reservados» y la página de datos abiertos de la SBS no declara una licencia (SBS, s. f.-c). El proyecto publica solo agregados propios con su cita y no redistribuye los archivos originales.

## 6. Entregables

| Entregable | Criterio de aceptación |
|---|---|
| Repositorio reproducible | `uv sync --locked`, `docker compose up -d` y el script de descarga reconstruyen la base desde cero, sin pasos manuales no documentados |
| Modelo de datos Oracle | DDL idempotente y vistas en `sql/oracle/` para estados financieros, indicadores y producción y siniestralidad; diccionario en `docs/03_diccionario_datos.md` |
| Informe | `reports/`: matriz, tablas y figuras con citas, notas y referencias en APA 7 y ortografía RAE |
| README | Problema, datos, método, resultados, reproducción y limitaciones (plantilla 03f) |
| Cronograma | `gestion/cronograma/`: `.mpp` con Baseline, XML (MSPDI) y PDF de línea base y de seguimiento |
| Modelo lógico y relacional | `docs/modelo/pf01_modelo.dmd` y diagramas `pf01_modelo_logico` y `pf01_modelo_relacional` (SVG y PDF) en `docs/diagramas/`, coherentes con el DDL |
| Arquitectura en Visio | `docs/diagramas/`: `PF-01_diagramas.vsdx` (una página), `PF-01_arquitectura.svg` y `PF-01_diagramas.pdf`; figura 1 de `docs/04_arquitectura.md` y del README (APA 7); modelo relacional con `pf01_modelo_relacional.svg` del Data Modeler (figura 2) |
| Proceso en Bizagi | `docs/procesos/`: `PF-01_proceso.bpm`, `PF-01_proceso_asis.bpmn` y `PF-01_proceso_tobe.bpmn` (BPMN 2.0), SVG AS-IS y TO-BE y `PF-01_proceso.pdf`; tabla de tiempos `PF-01_tiempos` en CSV, SVG y PDF; diagramas validados en Bizagi Modeler; figuras 2 y 3 y tabla 1 del README (APA 7) |
| Tablero Power BI | PBIP en `dashboards/powerbi/`; capturas en `reports/figures/` con nota APA |
| Post + documento PDF | Documento de 6 a 8 páginas de 1080 × 1350 con la matriz en la portada; checklist de la guía editorial y de la skill de marca; revisión anti-estilo-IA |

El documento PDF es el entregable que se muestra en LinkedIn.

## 7. Stack tecnológico

| Herramienta | Versión | Uso | Ficha o fuente de la versión |
|---|---|---|---|
| Python, uv, ruff y pytest | 3.13.5, 0.13.0, 0.17.0 y 9.1.1 | Entorno, calidad y pruebas | `04_estandares_tecnicos.md` (2026-10-09) |
| pandas | 3.0.6 | Transformación a formato largo | The pandas development team (2026) |
| openpyxl | 3.1.5 | Lectura del libro .xlsx del Boletín Mensual | Gazoni y Clark (2024) |
| xlrd | 2.0.2 | Lectura de los cuadros .XLS de la prueba de consistencia | Withers (2025) |
| python-oracledb | 26.0.1 (modo Thin) | Carga en Oracle | `04_estandares_tecnicos.md` (2026-10-09) |
| Oracle AI Database 26ai Free | 23.26.3, imagen `gvenzl/oracle-free:23.26.3` | Modelo de datos y vistas analíticas | `12_ficha_oracle-free.md` (2026-10-10); Oracle (s. f.-a, s. f.-b); Venzl (s. f.) |
| Docker Desktop | 4.84.0, motor WSL2 | Contenedor de Oracle, publicado en `127.0.0.1:1522` | `12_ficha_oracle-free.md` (2026-10-10) |
| Oracle SQL Developer | 26.2.0.186.2220 | Desarrollo y prueba interactiva del DDL, las vistas y las consultas sobre la base del contenedor | `12_ficha_sql-developer.md` (2026-10-11); Oracle (s. f.-c, s. f.-d) |
| Oracle SQL Developer Data Modeler | 23.1 (integrado en SQL Developer 26.2) | Modelo lógico y relacional (D-PF01-04) | `docs/modelo/README.md` (2026-10-11) |
| Power BI Desktop | 2.158.1177.0 (septiembre de 2026) | Tablero PBIP | `12_ficha_powerbi-pbip.md` (2026-10-10); Microsoft (s. f., 2026) |
| Microsoft Project | Professional 2021 | Línea base y seguimiento | `12_ficha_ms-project.md` (2026-10-10) |
| Microsoft Visio | Professional 2021 | Arquitectura del flujo de datos | `12_ficha_visio.md` (2026-10-10) |
| Bizagi Modeler | 4.3.0008 | Proceso AS-IS y TO-BE en BPMN 2.0 | `12_ficha_bizagi.md` (2026-10-10) |

Los gráficos del informe y del documento PDF siguen el estilo `jc-editorial` definido en `04_estandares_tecnicos.md`, sección 5.6.

## 8. Supuestos y restricciones

- El corte de agosto de 2026 está cerrado: la SBS publicó los cuadros el 22 de septiembre de 2026 y el Boletín Mensual el 5 de octubre de 2026, según la fecha de modificación del servidor.
- La siniestralidad se calcula como siniestros entre primas netas del mismo período. La SBS no declara la fórmula del índice en el archivo, así que se valida por cuadre (O2).
- Capacidad del director del proyecto: de 20 a 25 horas en noviembre. La primera semana concentra la carga de datos, con un ritmo de hasta 2.5 horas por día hábil; el resto del mes, de 1 a 1.5 horas.
- El repositorio vive en `C:\Portafolio\`, fuera de OneDrive, porque Power BI no guarda un PBIP directamente en OneDrive (Microsoft, s. f.) y por el estándar de `04_estandares_tecnicos.md`.
- No hay feriados nacionales en días hábiles entre el 12 de octubre y el 27 de noviembre de 2026 (09; pendiente de confirmar en gob.pe, que no respondió el 2026-10-10).
- Restricciones: solo datos públicos, citas APA 7, ortografía RAE y publicación manual en LinkedIn.

## 9. Riesgos iniciales

| ID | Riesgo | Probabilidad (A/M/B) | Impacto (A/M/B) | Respuesta |
|---|---|---|---|---|
| R1 | Los cambios del plan de cuentas que anota la SBS (junio de 2021 y marzo de 2026) rompen la comparabilidad de los estados financieros entre cortes | A | M | Cargar las cifras tal como se publican, con la versión del plan de cuentas de cada corte; PF-01 no compara rubros contables entre cortes |
| R2 | La estructura del Boletín Mensual cambia entre 2019 y 2026 (hojas, bloques de empresas, columnas MN y ME, formato .xls o .xlsx); los ZIP pesan entre 265 KB y 783 KB | A | M | Prueba de estructura por corte, tabla de equivalencias de empresas y catálogo de riesgos versionado; los cuadros individuales S-401 a S-403 sirven de respaldo |
| R3 | La SBS reemplaza archivos ya publicados (el Boletín de diciembre de 2021 se modificó en septiembre de 2023) | M | B | Manifiesto con fecha de descarga y SHA-256; los resultados se fechan con la descarga |
| R4 | Condiciones de uso no declaradas | M | M | Solo agregados propios con cita APA; sin redistribuir archivos; `data/raw/` fuera de Git |
| R5 | El servidor bloquea la descarga automatizada (las páginas del portal ya la bloquean) | M | M | Script con pausa y reintentos; plan B: descarga manual documentada, con verificación del hash |
| R6 | La mención de empresas por su nombre se lee como juicio sobre una compañía | B | A | Redacción descriptiva, solo cifras públicas citadas, sin calificativos; revisión del director antes de publicar |
| R7 | Las 20 a 25 horas no alcanzan: el plan de noviembre suma 24.5 h | A | M | Mitigación original: recortar el tablero opcional (4 h). Desde el 2026-10-14 el tablero es núcleo (D-PF01-10) y la ejecución va adelantada frente a la línea base, así que la capacidad de noviembre deja de ser restrictiva; si hiciera falta, se reduce el alcance del tablero (número de páginas), no el núcleo |
| R8 | Oracle Free no recibe parches de seguridad (Oracle, s. f.-a) | B | B | Contenedor solo local, puerto publicado únicamente en `127.0.0.1`, sin datos sensibles |
| R9 | La lectura de libros antiguos (.xls) falla | B | M | Prueba en el primer día de 2.1 con openpyxl y xlrd; si falla, se documenta la alternativa en el diccionario de datos |
| R10 | El equipo de desarrollo ya tiene una instalación nativa de Oracle 23ai Free (versión 23.6) con su listener en el puerto 1521 | A | B | El contenedor se publica en `127.0.0.1:1522` y el DSN del proyecto se declara en `.env` (`12_ficha_oracle-free.md`) |
| R11 | Microsoft Project 2021 y Visio 2021 terminan su soporte el 2026-10-14; siguen funcionando, pero sin actualizaciones de seguridad (fichas `ms-project` y `visio`) | A | B | Uso local, sin macros de terceros; se publican SVG, PDF y XML, que no dependen de la versión instalada |

## 10. Criterios de éxito y de cierre

- [ ] Objetivos O1, O2 y O3 cumplidos o justificados
- [ ] Release v1.0.0 publicado
- [ ] Post publicado y registrado en el tablero de indicadores
- [ ] Desvíos frente a la línea base explicados en `docs/05_cierre_lecciones.md`

## 11. Aprobación

Plan aprobado por José Caycho A. el 2026-10-11. En la misma fecha se incorporó Oracle SQL Developer al stack (versión 1.2 del acta) y, por control de cambios registrado en el issue #1, se incluyeron los paquetes 2.4 (Visio, #24) y 3.4 (Bizagi, #25), sin modificar la línea base del núcleo (versión 1.3). El 2026-10-14 se ajustó el alcance del paquete 2.4 (una página de arquitectura en Visio; modelo relacional desde el Data Modeler, D-PF01-09) y el tablero Power BI (4.1) pasó al núcleo (D-PF01-10); con el modelo lógico y relacional incorporado a 2.3 el 2026-10-11 (D-PF01-04), el esfuerzo total es de 32.5 h (versión 1.4). El 2026-10-18 el paquete 3.4 incorporó la tabla de tiempos AS-IS frente a TO-BE (D-PF01-19, enmendada el 2026-10-19) y el formato estándar de Bizagi en los diagramas (D-PF01-20), con 1.5 h más; el esfuerzo total es de 34.0 h (versión 1.5).

## Referencias

Gazoni, E., & Clark, C. (2024). *openpyxl* (Versión 3.1.5) [Software]. PyPI. https://pypi.org/project/openpyxl/3.1.5/

Microsoft. (s. f.). *Power BI Desktop projects (PBIP)*. Microsoft Learn. Recuperado el 10 de octubre de 2026, de https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview

Microsoft. (2026). *Power BI September 2026 feature summary*. Microsoft Fabric Community. https://community.fabric.microsoft.com/blog/fbc_pbiupdatesblog/power-bi-september-2026-feature-summary/5325831

Oracle. (s. f.-a). *Database 26ai FAQ*. Recuperado el 10 de octubre de 2026, de https://www.oracle.com/database/free/faq/

Oracle. (s. f.-b). *Get started with Oracle Database 26ai*. Recuperado el 10 de octubre de 2026, de https://www.oracle.com/database/free/get-started/

Oracle. (s. f.-c). *Oracle SQL Developer 26.2 release notes*. Recuperado el 11 de octubre de 2026, de https://www.oracle.com/tools/sqldev/sqldev-relnotes-26.2.html

Oracle. (s. f.-d). *Oracle SQL Developer downloads*. Recuperado el 11 de octubre de 2026, de https://www.oracle.com/database/sqldeveloper/technologies/download/

The pandas development team. (2026). *pandas* (Versión 3.0.6) [Software]. PyPI. https://pypi.org/project/pandas/3.0.6/

Superintendencia de Banca, Seguros y AFP. (s. f.-a). *Boletín estadístico de seguros*. Recuperado el 10 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaBoletinEstadistico.aspx?p=25

Superintendencia de Banca, Seguros y AFP. (s. f.-b). *Boletín mensual* [Conjunto de datos]. Recuperado el 10 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-367

Superintendencia de Banca, Seguros y AFP. (s. f.-c). *Datos abiertos*. Recuperado el 10 de octubre de 2026, de https://www.sbs.gob.pe/estadisticas-y-publicaciones/estadisticas-/datos-abiertos_

Superintendencia de Banca, Seguros y AFP. (s. f.-d). *Índice de siniestralidad directa y retenida según riesgos* [Conjunto de datos]. Recuperado el 10 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-403

Superintendencia de Banca, Seguros y AFP. (s. f.-e). *Primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 10 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-401

Superintendencia de Banca, Seguros y AFP. (s. f.-f). *Siniestros de primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 10 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-402

Venzl, G. (s. f.). *oci-oracle-free* [Software]. GitHub. Recuperado el 10 de octubre de 2026, de https://github.com/gvenzl/oci-oracle-free

Withers, C. (2025). *xlrd* (Versión 2.0.2) [Software]. PyPI. https://pypi.org/project/xlrd/2.0.2/
