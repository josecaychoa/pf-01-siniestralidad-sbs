# Modelo de datos de PF-01

Diseño del modelo lógico y relacional elaborado con Oracle SQL Developer Data Modeler 23.1.

## Cómo abrirlo

En Data Modeler, usar File > Open y seleccionar `pf01_modelo.dmd`. La carpeta `pf01_modelo/` debe estar junto a ese archivo. Los archivos `*.local` los regenera la herramienta al abrir el diseño y no se versionan.

## Contenido

- Modelo lógico: 10 entidades y 14 relaciones.
- Modelo relacional: 10 tablas con prefijos `dim_` (dimensiones) y `fct_` (hechos).
- `ddl_generado_datamodeler.sql`: DDL generado por Data Modeler para Oracle Database 21c. Es solo de referencia y no se ejecuta. Los scripts idempotentes del proyecto estarán en `sql/oracle/`.
- Diagramas del modelo lógico y relacional (SVG y PDF): `docs/diagramas/`.

## Referencias

Este documento no cita fuentes externas.
