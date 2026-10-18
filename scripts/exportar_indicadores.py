"""Exporta las vistas del análisis de 3.2 a CSV en data/processed/ (issue #8).

Uso (desde la raíz del repositorio, después de scripts/cargar_oracle.py):
    uv run python scripts/exportar_indicadores.py                    # base nativa (D-PF01-03)
    uv run python scripts/exportar_indicadores.py --base contenedor  # ORACLE_DSN de .env
    uv run python scripts/exportar_indicadores.py --destino otra/carpeta

Escribe un CSV por vista de indicadores.VISTAS_EXPORTADAS (parámetros, cortes, indicadores,
crecimiento, matriz y participación por empresa) e imprime las filas por archivo y el resumen
de la matriz. De data/processed/ solo se versiona matriz_riesgos.csv. Usuario y contraseña:
ORACLE_USER y ORACLE_PASSWORD del entorno o de .env, nunca impresos. Base: nativa
(localhost:1521/FREEPDB1, por defecto) o contenedor (ORACLE_DSN de .env); --dsn indica otra.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import oracledb

from pf_01_siniestralidad_sbs.carga import conectar
from pf_01_siniestralidad_sbs.indicadores import exportar_vistas, leer_vista, resumen_matriz

RAIZ = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada; devuelve 0 si los seis archivos se escribieron."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", choices=("nativa", "contenedor"), default="nativa")
    parser.add_argument("--dsn", help="DSN explícito; tiene prioridad sobre --base")
    parser.add_argument(
        "--destino", type=Path, default=RAIZ / "data" / "processed", help="carpeta de salida"
    )
    args = parser.parse_args(argv)

    try:
        with conectar(RAIZ / ".env", args.base, args.dsn) as conexion:
            print(f"Conectado a {conexion.dsn} · Oracle {conexion.version} · modo Thin")
            filas = exportar_vistas(conexion, args.destino)
            resumen = resumen_matriz(leer_vista(conexion, "vw_matriz_riesgo"))
    except (oracledb.Error, KeyError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Archivos escritos en {args.destino}:")
    for nombre, n in filas.items():
        print(f"  {nombre:<36} {n:>6} filas")
    print("Matriz de riesgos (vw_matriz_riesgo):")
    print(
        f"  filas {resumen['filas']} · sobre el umbral {resumen['sobre_umbral']} · "
        f"no comparables (rentas y SPP) {resumen['no_comparables']}"
    )
    print(
        f"  corte de siniestralidad directa {resumen['corte_siniestralidad_directa']} % · "
        f"retenida {resumen['corte_siniestralidad_retenida']} %"
    )
    print(
        "  cuadrante interanual directa: "
        + " · ".join(
            f"{'nulo' if clave is None else clave}: {n}"
            for clave, n in resumen["por_cuadrante_interanual_directa"].items()
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
