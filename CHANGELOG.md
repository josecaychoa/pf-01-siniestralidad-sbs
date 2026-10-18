# Changelog

## [Sin publicar]
- Atributo `siniestralidad_comparable` (S/N) en `riesgos.csv` y `dim_riesgo`, con la sección 3b de evolución del esquema en `01_ddl_tablas.sql`; decisiones D-PF01-11 a D-PF01-16 registradas en #8 (#8).
- Notebook de exploración `notebooks/01-jc-exploracion.ipynb` (8 tablas, 5 figuras, 12 hallazgos y 11 casos atípicos) sobre las vistas vw_; dependencias matplotlib 3.11.2, ipykernel y nbconvert; variable `PF01_BASE` (#7).
- Diagrama de arquitectura del flujo de datos en Visio (`docs/diagramas/PF-01_diagramas.vsdx`, `PF-01_arquitectura.svg` y `PF-01_diagramas.pdf`), `docs/04_arquitectura.md` con las figuras 1 (arquitectura) y 2 (modelo relacional), figura 1 en el README, acta 1.4 y EDT 1.5 (#24).
- Contenedor Oracle AI Database 26ai Free (`gvenzl/oracle-free:23.26.3`) en `docker-compose.yml`, `.env.example` con cuatro variables, dependencia python-oracledb 26.0.1 y convención de nombres SQL en español (D-PF01-05) (#6).
- Plantilla de PR con «Prueba local antes del merge: sí / no» (lección L-PF01-11).
- Acta 1.3 y EDT 1.4: se incluyen los paquetes 2.4 (Visio, #24) y 3.4 (Bizagi, #25) por control de cambios (#1).
- Catálogos versionados de empresas (equivalencias), riesgos (jerarquía y agrupación comparable), cortes (plan de cuentas) y excepciones de la fuente (#5).
- Validación de las tablas intermedias con `scripts/validar_datos.py` e informe en `reports/validacion_datos.md` (#5).
- `.gitattributes`: finales de línea LF en los informes de `reports/` (#5).
- `.gitattributes`: finales de línea LF en los CSV (#4).
- Descarga reproducible de los 9 boletines mensuales S-367 y de los cuadros S-401, S-402 y S-403 de agosto de 2026, con manifiesto de SHA-256 (#4).
- Extracción de P001 a P004 y P009 a P016 a formato largo en `data/interim/` (#4).
- Estructura inicial del repositorio.
