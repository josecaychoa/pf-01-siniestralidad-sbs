# CLAUDE.md · PF-XX <Titulo del proyecto>

## Contexto
Proyecto de portafolio personal de analítica de datos (seguros y finanzas del Perú).
Acta: docs/01_acta.md · Plan: docs/02_edt_gantt.md · Datos: docs/03_diccionario_datos.md
Cronograma (Project): gestion/cronograma/ · Diagramas (Visio): docs/diagramas/
Procesos (Bizagi): docs/procesos/ · Los .mpp, .vsdx y .bpm los edita José en Windows;
Claude Code no los modifica ni los regenera.

## Reglas obligatorias
- Usar solo datos públicos o sintéticos. Nunca datos personales reales ni información
  confidencial de empleadores, clientes o terceros.
- Citas, tablas, figuras y referencias en APA 7 (en español): (SBS, 2026) en el texto,
  "Nota. Elaboración propia con datos de SBS (2026)." bajo cada figura o tabla y
  sección "Referencias" al final de README e informes.
- Ortografía RAE: tildes, punto decimal, millares con espacio, "12.5 %" y "N.º".
- Ninguna credencial en el código: usar variables de entorno (.env, fuera de Git).
- No hacer merge, release ni push a main: abrir un PR y esperar la revisión de José.

## Entorno
- Python 3.13 gestionado con uv (pyproject.toml + uv.lock).
- Instalar: `uv sync` · Calidad: `uv run ruff check .` y `uv run ruff format --check .`
- Pruebas: `uv run pytest` · Oracle: `docker compose up -d` (python-oracledb, modo Thin).

## Convenciones
- Nombres en inglés técnico; comentarios y docstrings en español.
- SQL Oracle-first en sql/oracle/; variante T-SQL en sql/sqlserver/ si aplica.
- Scripts SQL idempotentes, numerados (01_, 02_ ...) y con variables enlazadas.
- data/raw es inmutable; las transformaciones escriben en data/interim y data/processed.
- Gráficos con assets/jc-editorial.mplstyle: hallazgo en #2A5CDA, contexto en #C8CBCF.
- Antes de publicar texto: skill revision-anti-estilo-ia (scripts/lint_texto.py).

## Git
- Rama por issue: <tipo>/<n>-<descripcion-corta> (feat, fix, docs, data, test, refactor, ci, chore).
- Commits (Conventional Commits 1.0.0): <tipo>(<ámbito opcional>): <descripción en español>,
  en minúscula y sin punto final; pie Refs #<n>.
- Los cambios entran a main solo por PR; el PR incluye "Closes #<n>".
