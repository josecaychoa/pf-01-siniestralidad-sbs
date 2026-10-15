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

<!-- Proceso (Bizagi): docs/procesos/ · Cronograma (Project): gestion/cronograma/ · cada SVG como figura APA con «Nota.» -->
## Gestión del proyecto
| Elemento | Archivo |
|---|---|
| Acta y objetivos SMART | [`docs/01_acta.md`](docs/01_acta.md) |
| EDT y Gantt de la línea base v1.0 (vista resumida, congelada al aprobar el plan) | [`docs/02_edt_gantt.md`](docs/02_edt_gantt.md) |
| Gantt de Microsoft Project con el avance real (PDF) | [`gestion/cronograma/PF-01_linea_base.pdf`](gestion/cronograma/PF-01_linea_base.pdf) |
| Cronograma de Microsoft Project (`.mpp` y XML) | [`gestion/cronograma/`](gestion/cronograma/) |
| Arquitectura del flujo de datos y modelo relacional | [`docs/04_arquitectura.md`](docs/04_arquitectura.md) |
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
