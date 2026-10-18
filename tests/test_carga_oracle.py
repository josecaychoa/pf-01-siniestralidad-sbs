"""Prueba de integración de la carga en Oracle (paquete 2.3). Solo lee la base.

Se omite si el entorno no tiene ORACLE_USER, ORACLE_PASSWORD y ORACLE_DSN, como en GitHub
Actions. Ejecutar antes la carga: uv run python scripts/cargar_oracle.py
"""

import csv
import os
from pathlib import Path

import oracledb
import pytest

VARIABLES = ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN")
INTERIM = Path(__file__).resolve().parents[1] / "data" / "interim"
HECHOS = {
    "fct_estado_financiero": "stg_estados_financieros",
    "fct_indicador": "stg_indicadores",
    "fct_riesgo": "stg_riesgos",
}
CUADRES = ("vw_cuadre_balance", "vw_cuadre_totales", "vw_cuadre_cuadros_sbs")

pytestmark = pytest.mark.skipif(
    not all(os.environ.get(v) for v in VARIABLES), reason="sin variables de conexión a Oracle"
)


@pytest.fixture(scope="module")
def cursor():
    with oracledb.connect(
        user=os.environ["ORACLE_USER"],
        password=os.environ["ORACLE_PASSWORD"],
        dsn=os.environ["ORACLE_DSN"],
    ) as conexion:
        yield conexion.cursor()


def contar(cursor, consulta: str) -> int:
    cursor.execute(consulta)
    return cursor.fetchone()[0]


@pytest.mark.skipif(not (INTERIM / "riesgos.csv").exists(), reason="sin data/interim")
@pytest.mark.parametrize("nombre", ["estados_financieros", "indicadores", "riesgos"])
def test_stg_igual_a_data_interim(cursor, nombre):
    with (INTERIM / f"{nombre}.csv").open(encoding="utf-8", newline="") as archivo:
        filas = sum(1 for _ in csv.reader(archivo)) - 1
    assert contar(cursor, f"SELECT COUNT(*) FROM stg_{nombre}") == filas


@pytest.mark.parametrize(("hechos", "stg"), HECHOS.items())
def test_hechos_con_todas_las_celdas_del_boletin(cursor, hechos, stg):
    celdas = contar(cursor, f"SELECT COUNT(*) FROM {stg} WHERE serie = 'S-367'")
    assert contar(cursor, f"SELECT COUNT(*) FROM {hechos}") == celdas > 0


def test_vistas_validas(cursor):
    assert contar(cursor, "SELECT COUNT(*) FROM user_views") == 12  # 5 de 02 y 7 de 04
    consulta = "SELECT COUNT(*) FROM user_objects WHERE object_type = 'VIEW' AND status <> 'VALID'"
    assert contar(cursor, consulta) == 0


@pytest.mark.parametrize("vista", CUADRES)
def test_cuadres_de_o1(cursor, vista):
    assert contar(cursor, f"SELECT COUNT(*) FROM {vista}") > 0
    assert contar(cursor, f"SELECT COUNT(*) FROM {vista} WHERE NOT cumple") == 0


def test_siniestralidad_comparable_en_dim_riesgo(cursor):
    cursor.execute(
        "SELECT siniestralidad_comparable, COUNT(*) FROM dim_riesgo "
        "GROUP BY siniestralidad_comparable"
    )
    assert dict(cursor.fetchall()) == {"S": 50, "N": 10}
