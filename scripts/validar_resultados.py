"""Paquete 3.3 de PF-01: valida los resultados del análisis y escribe la nota (issue #9).

Uso (desde la raíz del repositorio, después de scripts/cargar_oracle.py):
    uv run python scripts/validar_resultados.py                    # base nativa (D-PF01-03)
    uv run python scripts/validar_resultados.py --base contenedor  # ORACLE_DSN de .env
    uv run python scripts/validar_resultados.py --salida otra/nota.md

Lee vw_cortes_analisis, vw_indicadores_riesgo y vw_matriz_riesgo y la fila Total de P009,
P015 y P016 en fct_riesgo; ejecuta los cinco controles de D-PF01-17
(src/pf_01_siniestralidad_sbs/validacion_resultados.py) y la corrida de las pruebas citadas,
y escribe reports/validacion_resultados.md. Devuelve 1 si algún control falla. Usuario y
contraseña: ORACLE_USER y ORACLE_PASSWORD del entorno o de .env, nunca impresos.
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import oracledb
import pandas as pd

from pf_01_siniestralidad_sbs import validacion_resultados as vr
from pf_01_siniestralidad_sbs.carga import conectar, leer_env
from pf_01_siniestralidad_sbs.indicadores import leer_vista

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[1]
COMANDO_PRUEBAS = (
    "uv",
    "run",
    "pytest",
    "-q",
    "-p",
    "no:cacheprovider",
    "tests/test_vistas_analisis.py",
    "tests/test_indicadores_oracle.py",
)
# Fila Total (columna «Total») de P009, P015 y P016, una fila por corte.
CONSULTA_PUBLICADOS = """
SELECT f.fecha_corte,
       MAX(CASE WHEN f.hoja = :hoja_primas THEN f.valor END)    AS total_p009,
       MAX(CASE WHEN f.hoja = :hoja_directa THEN f.valor END)   AS directa_publicada,
       MAX(CASE WHEN f.hoja = :hoja_retenida THEN f.valor END)  AS retenida_publicada,
       COUNT(*)                                                 AS n_celdas
  FROM fct_riesgo f
  JOIN dim_riesgo r           ON r.riesgo_id = f.riesgo_id
  JOIN dim_columna_empresa ce ON ce.columna_id = f.columna_id
 WHERE r.clave = :clave
   AND ce.tipo_columna = :tipo_columna
   AND f.hoja IN (:hoja_primas, :hoja_directa, :hoja_retenida)
 GROUP BY f.fecha_corte
 ORDER BY f.fecha_corte
"""


def leer_publicados(conexion: oracledb.Connection) -> pd.DataFrame:
    """Fila Total de P009, P015 y P016 por corte; exige una celda por hoja y corte."""
    cursor = conexion.cursor()
    cursor.execute(
        CONSULTA_PUBLICADOS,
        hoja_primas="P009",
        hoja_directa="P015",
        hoja_retenida="P016",
        clave="TOTAL",
        tipo_columna="total_simple",
    )
    columnas = [d[0].lower() for d in cursor.description]
    publicados = pd.DataFrame(cursor.fetchall(), columns=columnas)
    if publicados.empty or (publicados["n_celdas"] != 3).any():
        raise ValueError(
            "fct_riesgo no tiene una celda Total por hoja y corte en P009, P015 y P016"
        )
    publicados["fecha_corte"] = pd.to_datetime(publicados["fecha_corte"]).dt.date
    return publicados.drop(columns="n_celdas")


def version_motor(conexion: oracledb.Connection) -> str:
    """banner_full de v$version; product_component_version si el usuario no tiene acceso."""
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT banner_full FROM v$version")
    except oracledb.DatabaseError:
        cursor.execute("SELECT version_full FROM product_component_version")
    texto = str(cursor.fetchone()[0])
    return " · ".join(linea.strip() for linea in texto.splitlines() if linea.strip())


def fechas_descarga(ruta: Path) -> str:
    """Fechas de descarga distintas de data/raw/manifest.csv."""
    with ruta.open(encoding="utf-8", newline="") as archivo:
        fechas = sorted({fila["fecha_descarga"][:10] for fila in csv.DictReader(archivo)})
    return ", ".join(fechas)


def correr_pruebas(dsn: str) -> dict[str, object]:
    """Corre las pruebas citadas contra la misma base y devuelve la línea de resumen.

    El proceso hijo recibe ORACLE_USER y ORACLE_PASSWORD del entorno o de .env y ORACLE_DSN
    con el DSN de la conexión del script; nada de eso se imprime.
    """
    ruta_env = RAIZ / ".env"
    entorno = {**(leer_env(ruta_env) if ruta_env.exists() else {}), **os.environ}
    entorno["ORACLE_DSN"] = dsn
    proceso = subprocess.run(
        COMANDO_PRUEBAS,
        cwd=RAIZ,
        env=entorno,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    lineas = [linea.strip("= ").strip() for linea in proceso.stdout.splitlines()]
    resumen = next((linea for linea in reversed(lineas) if linea), "sin salida")
    return {
        "comando": " ".join(COMANDO_PRUEBAS),
        "resumen": resumen,
        "codigo": proceso.returncode,
    }


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada; devuelve 0 si los cinco controles están conformes."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", choices=("nativa", "contenedor"), default="nativa")
    parser.add_argument("--dsn", help="DSN explícito; tiene prioridad sobre --base")
    parser.add_argument(
        "--salida",
        type=Path,
        default=RAIZ / "reports" / "validacion_resultados.md",
        help="archivo de la nota",
    )
    args = parser.parse_args(argv)

    try:
        with conectar(RAIZ / ".env", args.base, args.dsn) as conexion:
            print(f"Conectado a {conexion.dsn} · Oracle {conexion.version} · modo Thin")
            dsn = conexion.dsn
            cortes = leer_vista(conexion, "vw_cortes_analisis")
            indicadores = leer_vista(conexion, "vw_indicadores_riesgo")
            matriz = leer_vista(conexion, "vw_matriz_riesgo")
            publicados = leer_publicados(conexion)
            version = version_motor(conexion)
    except (oracledb.Error, KeyError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    corte_actual: date = cortes["corte_actual"].iloc[0]
    contraste = vr.contraste_total_sistema(indicadores, publicados)
    total_p009 = publicados.loc[publicados["fecha_corte"] == corte_actual, "total_p009"]
    if total_p009.empty:
        print(f"ERROR: sin Total de P009 en {corte_actual}", file=sys.stderr)
        return 1
    por_riesgo = vr.control_indice_por_riesgo(indicadores)
    cobertura = vr.control_cobertura_matriz(matriz)
    resultados = [
        vr.control_o2(contraste, corte_actual),
        vr.control_serie_total(contraste),
        por_riesgo,
        cobertura,
        vr.control_primas_matriz(matriz, float(total_p009.iloc[0])),
    ]

    print("Pruebas citadas: " + " ".join(COMANDO_PRUEBAS))
    pruebas = correr_pruebas(dsn)
    print(f"  {pruebas['resumen']} (código {pruebas['codigo']})")

    entorno = {
        "fecha_generacion": datetime.now(ZoneInfo("America/Lima")).strftime("%Y-%m-%d"),
        "base": args.base if args.dsn is None else f"DSN explícito ({args.base})",
        "version": version,
        "corte_actual": f"{corte_actual:%Y-%m-%d} ({vr.mes_y_anio(corte_actual)})",
        "fecha_descarga": fechas_descarga(RAIZ / "data" / "raw" / "manifest.csv"),
    }
    nota = vr.informe(
        resultados, contraste, por_riesgo.detalle, cobertura.detalle, entorno, pruebas
    )
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(nota, encoding="utf-8", newline="\n")

    for r in resultados:
        estado = "ok   " if r.ok else "FALLA"
        print(
            f"  {estado} {r.control}: {vr.miles(r.revisados)} revisados, {r.fallas} fallas, "
            f"{r.excepciones} excepciones de la fuente"
        )
    actual = resultados[0].detalle.set_index("medida")
    for medida in vr.MEDIDAS if not actual.empty else ():
        print(
            f"  O2 {medida}: calculada {vr.decimales(actual.loc[medida, 'calculada'])} % · "
            f"publicada {vr.decimales(actual.loc[medida, 'publicada'])} % · "
            f"diferencia {vr.decimales(actual.loc[medida, 'diferencia'])} p. p."
        )
    try:
        destino = args.salida.resolve().relative_to(RAIZ)
    except ValueError:
        destino = args.salida
    print(f"Nota: {destino}")
    return 0 if all(r.ok for r in resultados) else 1


if __name__ == "__main__":
    sys.exit(main())
