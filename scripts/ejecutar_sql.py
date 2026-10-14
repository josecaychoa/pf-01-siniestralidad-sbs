"""Ejecuta un script de sql/oracle/ en Oracle con python-oracledb (modo Thin).

Uso (desde la raíz del repositorio):
    uv run python scripts/ejecutar_sql.py sql/oracle/01_ddl_tablas.sql
    uv run python scripts/ejecutar_sql.py sql/oracle/02_vistas.sql --base contenedor

Separa las sentencias con la convención de SQL*Plus y SQLcl («;» al final de la línea y «/»
después de un bloque PL/SQL) y se detiene en el primer error, que deshace la transacción en
curso. Usuario y contraseña: ORACLE_USER y ORACLE_PASSWORD del entorno o de .env, nunca
impresos. Base: nativa (localhost:1521/FREEPDB1, D-PF01-03, por defecto) o contenedor
(ORACLE_DSN de .env); --dsn indica otra.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import oracledb

from pf_01_siniestralidad_sbs.carga import EjecucionSQLError, conectar, ejecutar_script

RAIZ = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada; devuelve 0 si todas las sentencias se ejecutaron sin errores."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("script", type=Path, help="ruta del archivo .sql")
    parser.add_argument("--base", choices=("nativa", "contenedor"), default="nativa")
    parser.add_argument("--dsn", help="DSN explícito; tiene prioridad sobre --base")
    args = parser.parse_args(argv)

    try:
        with conectar(RAIZ / ".env", args.base, args.dsn) as conexion:
            print(f"Conectado a {conexion.dsn} · Oracle {conexion.version} · modo Thin")
            ejecutadas = ejecutar_script(conexion, args.script)
    except (EjecucionSQLError, oracledb.Error, KeyError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"{args.script.name}: {ejecutadas} sentencias ejecutadas sin errores")
    return 0


if __name__ == "__main__":
    sys.exit(main())
