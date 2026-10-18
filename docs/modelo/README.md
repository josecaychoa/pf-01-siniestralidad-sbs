# Modelo de datos de PF-01

Diseño del modelo lógico y relacional elaborado con Oracle SQL Developer Data Modeler 23.1.

## Cómo abrirlo

En Data Modeler, usar File > Open y seleccionar `pf01_modelo.dmd`. La carpeta `pf01_modelo/` debe estar junto a ese archivo. Los archivos `*.local` los regenera la herramienta al abrir el diseño y no se versionan.

## Contenido

- Modelo lógico: 10 entidades y 14 relaciones.
- Modelo relacional: 10 tablas con prefijos `dim_` (dimensiones) y `fct_` (hechos).
- `ddl_generado_datamodeler.sql`: DDL generado por Data Modeler para Oracle Database 21c. Es solo de referencia y no se ejecuta. Los scripts idempotentes del proyecto están en `sql/oracle/`:
  - `01_ddl_tablas.sql`: tablas `stg_`, `dim_` y `fct_`, llaves, restricciones CHECK, índices y comentarios.
  - `02_vistas.sql`: vistas analíticas y de cuadre (`vw_`).
  - `03_carga_modelo.sql`: carga de `dim_` y `fct_` desde las tablas `stg_`.
  - `04_vistas_analisis.sql`: vistas del análisis de 3.2.
- Cómo reconstruir la base y resultados esperados: [diccionario de datos, sección 5](../03_diccionario_datos.md#5-cómo-reconstruir-la-base).
- Diagramas del modelo lógico y relacional (SVG y PDF): `docs/diagramas/`.
- Actualización del 2026-10-18: atributo siniestralidad_comparable en la entidad Riesgo y la tabla dim_riesgo (D-PF01-15), agregado en los dos modelos sin reingeniar; DDL de referencia (sitio 21c) y diagramas regenerados.

## Referencias

Este documento no cita fuentes externas.
