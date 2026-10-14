"""Paquete 2.3 de PF-01: crea el modelo de datos en Oracle y lo carga desde data/interim.

Uso (desde la raíz del repositorio, después de scripts/descargar_sbs.py):
    uv run python scripts/cargar_oracle.py                    # base nativa (D-PF01-03)
    uv run python scripts/cargar_oracle.py --base contenedor  # ORACLE_DSN de .env

Orden: 01_ddl_tablas.sql -> 02_vistas.sql -> tablas stg_ -> dimensiones de catálogo ->
03_carga_modelo.sql. Es idempotente: cada ejecución reemplaza los datos y deja las mismas
filas. Al final informa las filas por tabla, el estado de las vistas y los cuadres de O1.
Devuelve 1 si un paso falla o si alguna vista queda no válida; los incumplimientos de los
cuadres se informan, pero no detienen la carga.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import oracledb

from pf_01_siniestralidad_sbs.carga import (
    EjecucionSQLError,
    cargar_catalogos,
    cargar_stg,
    conectar,
    ejecutar_script,
)

RAIZ = Path(__file__).resolve().parents[1]
DIR_SQL = RAIZ / "sql" / "oracle"
TABLAS = (
    "stg_estados_financieros",
    "stg_indicadores",
    "stg_riesgos",
    "dim_columna_empresa",
    "dim_corte",
    "dim_cuadro",
    "dim_cuenta",
    "dim_empresa",
    "dim_indicador",
    "dim_riesgo",
    "fct_estado_financiero",
    "fct_indicador",
    "fct_riesgo",
)
CUADRES = ("vw_cuadre_balance", "vw_cuadre_totales", "vw_cuadre_cuadros_sbs")


def miles(n: int) -> str:
    """Entero con separador de millares de espacio (RAE)."""
    return f"{n:,}".replace(",", " ")


def sin_mensajes(_: str) -> None:
    """Descarta los PROMPT de los scripts; el resumen lo imprime este programa."""


def cargar(conexion: oracledb.Connection) -> None:
    """Ejecuta los pasos de la carga en orden e imprime el tiempo de cada uno."""
    for script in ("01_ddl_tablas.sql", "02_vistas.sql"):
        inicio = time.perf_counter()
        ejecutadas = ejecutar_script(conexion, DIR_SQL / script, sin_mensajes)
        print(f"  {script}: {ejecutadas} sentencias · {time.perf_counter() - inicio:.1f} s")

    inicio = time.perf_counter()
    conteo = cargar_stg(conexion, RAIZ / "data" / "interim")
    filas = ", ".join(f"{tabla} {miles(n)}" for tabla, n in conteo.items())
    print(f"  tablas stg_: {filas} · {time.perf_counter() - inicio:.1f} s")

    # Catálogos y 03_carga_modelo.sql forman una sola transacción, que confirma el script.
    inicio = time.perf_counter()
    try:
        catalogos = cargar_catalogos(conexion)
        ejecutadas = ejecutar_script(conexion, DIR_SQL / "03_carga_modelo.sql", sin_mensajes)
    except BaseException:
        conexion.rollback()
        raise
    filas = ", ".join(f"{tabla} {miles(n)}" for tabla, n in catalogos.items())
    print(f"  catálogos: {filas}")
    print(f"  03_carga_modelo.sql: {ejecutadas} sentencias · {time.perf_counter() - inicio:.1f} s")


def informar(conexion: oracledb.Connection) -> bool:
    """Imprime filas por tabla, vistas y cuadres; devuelve False si hay vistas no válidas."""
    cursor = conexion.cursor()
    print("Filas por tabla:")
    for tabla in TABLAS:  # nombres fijos del modelo, no datos de entrada
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        print(f"  {tabla:<24} {miles(cursor.fetchone()[0]):>8}")

    cursor.execute(
        "SELECT object_name, status FROM user_objects WHERE object_type = 'VIEW' "
        "ORDER BY object_name"
    )
    vistas = cursor.fetchall()
    no_validas = [nombre for nombre, estado in vistas if estado != "VALID"]
    print(f"Vistas: {len(vistas)} · no válidas: {', '.join(no_validas) or 'ninguna'}")

    print("Cuadres de O1:")
    for vista in CUADRES:
        cursor.execute(f"SELECT COUNT(*), COUNT(CASE WHEN cumple THEN 1 END) FROM {vista}")
        total, cumplen = cursor.fetchone()
        print(
            f"  {vista:<22} {miles(total):>7} filas · {miles(cumplen):>7} cumplen · "
            f"{miles(total - cumplen):>5} no cumplen"
        )
    return not no_validas


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada; devuelve 0 si la carga terminó y todas las vistas son válidas."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", choices=("nativa", "contenedor"), default="nativa")
    parser.add_argument("--dsn", help="DSN explícito; tiene prioridad sobre --base")
    args = parser.parse_args(argv)

    inicio = time.perf_counter()
    try:
        with conectar(RAIZ / ".env", args.base, args.dsn) as conexion:
            print(f"Conectado a {conexion.dsn} · Oracle {conexion.version} · modo Thin")
            cargar(conexion)
            vistas_validas = informar(conexion)
    except (EjecucionSQLError, oracledb.Error, KeyError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Tiempo total: {time.perf_counter() - inicio:.1f} s")
    return 0 if vistas_validas else 1


if __name__ == "__main__":
    sys.exit(main())
