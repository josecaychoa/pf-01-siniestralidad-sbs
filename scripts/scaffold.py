"""Crea la estructura estándar de un repositorio del portafolio JC. (04_estandares_tecnicos).
Uso: python scaffold.py <carpeta> --pf PF-01 --titulo "Siniestralidad por ramo" [--forzar]
No sobrescribe archivos existentes salvo con --forzar. Solo biblioteca estándar."""

import argparse
import re
from datetime import date
from pathlib import Path

CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1"
SETUP_UV = "astral-sh/setup-uv@1c37ad07a6a961277cf70c0d37d6f313000f5884  # v10.3.0"

CARPETAS = [
    "data/raw",
    "data/interim",
    "data/processed",
    "data/external",
    "docs",
    "docs/diagramas",
    "docs/procesos",
    "gestion/cronograma",
    "notebooks",
    "sql/oracle",
    "sql/sqlserver",
    "dashboards/powerbi",
    "reports/figures",
    "linkedin",
    "assets",
    "scripts",
    "tests",
    ".github/workflows",
    ".github/ISSUE_TEMPLATE",
]


def archivos(nombre, modulo, pf, titulo, anio):
    """Devuelve {ruta: contenido} con los archivos base del repositorio."""
    return {
        "README.md": f"""# {pf} · {titulo}

`Portafolio · {pf}` · José Caycho A. · <mes año>

> <Resumen en dos líneas con el hallazgo principal, su cifra y su fuente.>

## Problema
## Datos
| Fuente | Documento o serie | Fecha de corte | Condiciones de uso |
|---|---|---|---|
## Método
<!-- Arquitectura (Visio): docs/diagramas/ · Proceso (Bizagi): docs/procesos/ -->
<!-- Cronograma (Project): gestion/cronograma/ · cada SVG como figura APA con «Nota.» -->
## Gestión del proyecto
| Elemento | Archivo |
|---|---|
| Acta y objetivos SMART | `docs/01_acta.md` |
| EDT y Gantt (vista resumida de la línea base) | `docs/02_edt_gantt.md` |
| Cronograma con línea base y seguimiento (Microsoft Project) | `gestion/cronograma/` |
| Cierre, desvíos y lecciones | `docs/05_cierre_lecciones.md` |
## Resultados
## Cómo reproducir
```bash
git clone https://github.com/josecaychoa/{nombre}.git
cd {nombre}
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
""",
        "CLAUDE.md": f"""# CLAUDE.md · {pf} {titulo}

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
""",
        "CHANGELOG.md": "# Changelog\n\n## [Sin publicar]\n- Estructura inicial del repositorio.\n",
        "LICENSE": f"""MIT License

Copyright (c) {anio} José Caycho A.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",
        "pyproject.toml": f"""[project]
name = "{nombre}"
version = "0.1.0"
description = "{pf} · {titulo}"
readme = "README.md"
requires-python = ">=3.13"
dependencies = []

[dependency-groups]
dev = ["pytest>=9.1", "ruff>=0.17", "pre-commit>=4.6", "pypdf>=6"]

[build-system]
requires = ["uv_build>=0.13.0,<0.14"]
build-backend = "uv_build"

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "N", "SIM", "PD"]

[tool.pytest.ini_options]
testpaths = ["tests"]
""",
        ".python-version": "3.13\n",
        ".gitignore": """.env
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
data/raw/*
data/interim/*
data/processed/*
data/external/*
!data/**/.gitkeep
.ipynb_checkpoints/
*.pbix
""",
        ".env.example": "ORACLE_USER=\nORACLE_PASSWORD=\nORACLE_DSN=localhost:1521/<servicio>\n",
        ".pre-commit-config.yaml": """repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.17.0
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format
""",
        ".github/workflows/ci.yml": f"""name: ci
on:
  push:
    branches: [main]
  pull_request:
permissions:
  contents: read
jobs:
  calidad:
    runs-on: ubuntu-latest
    steps:
      - uses: {CHECKOUT}
      - uses: {SETUP_UV}
      - run: uv sync --locked
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run pytest
""",
        ".github/pull_request_template.md": (
            "## Resumen\n\n## Evidencia\n- [ ] ruff y pytest en verde\n"
            "- [ ] Cifras nuevas con su cita APA 7 y ortografía RAE\n\nCloses #\n"
        ),
        ".github/ISSUE_TEMPLATE/tarea.md": (
            "---\nname: Tarea de la EDT\nabout: Paquete de trabajo del proyecto\n---\n\n"
            "## Paquete EDT\n\n## Criterios de aceptación\n- [ ] \n\n## Evidencia de cierre\n"
        ),
        "data/README.md": (
            "# Datos\n\n| Archivo | Fuente | URL | Documento o serie | Fecha de corte "
            "| Fecha de descarga | Condiciones de uso |\n|---|---|---|---|---|---|---|\n"
        ),
        "docs/01_acta.md": f"# Acta de constitución · {pf}: {titulo}\n\n(Plantilla 03a)\n",
        "docs/02_edt_gantt.md": (
            f"# EDT y Gantt · {pf}\n\n(Plantillas 03b y 03c)\n\n"
            "La línea base formal es la Baseline del cronograma de Microsoft Project en "
            "`gestion/cronograma/`. El Gantt de este archivo es su vista resumida.\n"
        ),
        "docs/03_diccionario_datos.md": f"# Diccionario de datos · {pf}\n",
        "docs/04_arquitectura.md": f"# Arquitectura · {pf}\n",
        "docs/05_cierre_lecciones.md": f"# Cierre · {pf}\n\n(Plantilla 03e)\n",
        f"src/{modulo}/__init__.py": f'"""{pf} · {titulo}."""\n\n__version__ = "0.1.0"\n',
        "tests/test_humo.py": (
            f'"""Prueba de humo: el paquete se importa."""\n\nimport {modulo}\n\n\n'
            f"def test_version():\n    assert {modulo}.__version__\n"
        ),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("carpeta")
    p.add_argument("--pf", required=True, help="Identificador, por ejemplo PF-01")
    p.add_argument("--titulo", required=True)
    p.add_argument("--forzar", action="store_true", help="Sobrescribir archivos existentes")
    a = p.parse_args()
    raiz = Path(a.carpeta)
    nombre = raiz.resolve().name.lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", nombre):
        raise SystemExit(f"Nombre de repositorio no válido: {nombre}")
    modulo = nombre.replace("-", "_")
    for c in CARPETAS:
        (raiz / c).mkdir(parents=True, exist_ok=True)
    creados, omitidos = 0, 0
    for ruta, texto in archivos(nombre, modulo, a.pf, a.titulo, date.today().year).items():
        destino = raiz / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        if destino.exists() and not a.forzar:
            omitidos += 1
            continue
        destino.write_text(texto, encoding="utf-8", newline="\n")
        creados += 1
    for c in CARPETAS:
        # .gitkeep solo en las carpetas que quedaron vacías, para que Git las conserve
        if not any((raiz / c).iterdir()):
            (raiz / c / ".gitkeep").touch()
    print(f"{nombre}: {creados} archivos creados, {omitidos} omitidos (ya existían).")
    print("Siguiente: copiar assets/jc-editorial.mplstyle, scripts/verificar_pdf.py y")
    print("scripts/lint_texto.py desde sus skills; luego uv lock && uv sync.")


if __name__ == "__main__":
    main()
