# PF-01 · Producción y siniestralidad por riesgo del mercado asegurador peruano, 2019-2026

`Portafolio · PF-01` · José Caycho A. · <mes año>

> <Resumen en dos líneas con el hallazgo principal, su cifra y su fuente.>

## Problema
## Datos
| Fuente | Documento o serie | Fecha de corte | Condiciones de uso |
|---|---|---|---|
## Método
El flujo de datos tiene tres etapas ETL (extracción, transformación y carga) y una de consumo (figura 1). El detalle de cada etapa, las decisiones de diseño y el modelo relacional están en [`docs/04_arquitectura.md`](docs/04_arquitectura.md).

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

<!-- Cronograma (Project): gestion/cronograma/ · cada SVG como figura APA con «Nota.» -->
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
## Cómo reproducir
```bash
git clone https://github.com/josecaychoa/pf-01-siniestralidad-sbs.git
cd pf-01-siniestralidad-sbs
uv sync --locked
uv run pytest
```
## Limitaciones
- Este análisis tiene fines demostrativos y no constituye asesoría regulatoria, actuarial
  ni financiera.
## Referencias
<!-- Lista APA 7 en orden alfabético; un párrafo por referencia (13_guia_apa_rae.md) -->
## Licencia
Código bajo licencia MIT. Los datos conservan las condiciones de uso de su fuente original.
## Autor
José Caycho A. · Business Analyst Senior · Procesos · Datos
linkedin.com/in/jcaychoasin · github.com/josecaychoa
