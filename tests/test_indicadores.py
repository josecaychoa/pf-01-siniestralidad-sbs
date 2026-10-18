"""Pruebas unitarias del módulo indicadores (paquete 3.2), sin base de datos."""

import math

import pandas as pd
import pytest

from pf_01_siniestralidad_sbs.indicadores import (
    CLASIFICACIONES,
    ETIQUETAS_CUADRANTE,
    clasificar_indice,
    clasificar_matriz,
    corte_siniestralidad,
    cuadrante,
    indice_siniestralidad,
    resumen_matriz,
    signo,
    signos_coinciden,
    tcac,
    variacion_interanual,
)

# --------------------------------------------------------------------------------------
# Crecimiento (D-PF01-11)
# --------------------------------------------------------------------------------------


def test_variacion_interanual():
    assert variacion_interanual(110, 100) == pytest.approx(10)
    assert variacion_interanual(80, 100) == pytest.approx(-20)
    assert variacion_interanual(110, 0) is None
    assert variacion_interanual(110, -5) is None
    assert variacion_interanual(None, 100) is None
    assert variacion_interanual(110, None) is None


def test_tcac():
    assert tcac(100, 170, 6) == pytest.approx(9.2466, abs=1e-4)  # 2019 -> 2025
    assert tcac(100, 100, 6) == pytest.approx(0)
    assert tcac(0, 170, 6) is None
    assert tcac(100, 0, 6) is None
    assert tcac(100, 170, 0) is None
    assert tcac(None, 170, 6) is None
    assert tcac(100, None, 6) is None
    assert tcac(100, 170, None) is None


# --------------------------------------------------------------------------------------
# Índices (D-PF01-12 y D-PF01-14)
# --------------------------------------------------------------------------------------


def test_indice_siniestralidad():
    assert indice_siniestralidad(50, 200) == pytest.approx(25)
    assert indice_siniestralidad(-10, 200) == pytest.approx(-5)  # negativo, no se trunca
    assert indice_siniestralidad(50, 0) is None
    assert indice_siniestralidad(50, -200) is None
    assert indice_siniestralidad(None, 200) is None
    assert indice_siniestralidad(50, None) is None


def test_signo_y_signos_coinciden():
    assert (signo(3.5), signo(-0.1), signo(0), signo(0.0)) == (1, -1, 0, 0)
    assert signos_coinciden(10, 5) == "S"
    assert signos_coinciden(-10, -5) == "S"
    assert signos_coinciden(10, -5) == "N"
    assert signos_coinciden(0, 5) == "N"  # SIGN(0) = 0 difiere de 1
    assert signos_coinciden(0, 0) == "S"
    assert signos_coinciden(None, 5) is None
    assert signos_coinciden(10, None) is None


# --------------------------------------------------------------------------------------
# Clasificación de celdas (D-PF01-13 y D-PF01-14)
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("primas", "siniestros", "esperado"),
    [
        (None, 10, "sin_dato"),
        (100, None, "sin_dato"),
        (0, -10, "sin_primas"),  # primas 0 prevalece sobre siniestros negativos
        (0, 10, "sin_primas"),
        (-100, -10, "primas_negativas"),  # primas negativas prevalecen
        (-100, 10, "primas_negativas"),
        (100, -10, "negativo"),
        (100, 150, "mayor_100"),
        (100, 100, "en_rango"),  # igual a 100 % no es mayor_100
        (100, 50, "en_rango"),
        (100, 0, "en_rango"),
    ],
)
def test_clasificar_indice(primas, siniestros, esperado):
    assert clasificar_indice(primas, siniestros) == esperado
    assert esperado in CLASIFICACIONES


# --------------------------------------------------------------------------------------
# Cuadrantes (D-PF01-11, D-PF01-15 y D-PF01-16)
# --------------------------------------------------------------------------------------


def test_cuadrante_en_las_cuatro_celdas():
    corte = 44.0
    assert cuadrante(5, 60, corte) == 1
    assert cuadrante(5, 30, corte) == 2
    assert cuadrante(-5, 60, corte) == 3
    assert cuadrante(-5, 30, corte) == 4
    assert set(ETIQUETAS_CUADRANTE) == {1, 2, 3, 4}


def test_cuadrante_en_los_bordes():
    corte = 44.0
    assert cuadrante(0, 60, corte) == 1  # crecimiento igual al corte es «crece»
    assert cuadrante(0, 44.0, corte) == 2  # índice igual al corte es «bajo el corte»
    assert cuadrante(-0.000001, 44.0, corte) == 4
    assert cuadrante(5, 60, corte, corte_crecimiento=10) == 3  # otro corte de crecimiento


def test_cuadrante_nulo():
    assert cuadrante(5, 60, 44.0, sobre_umbral=False) is None
    assert cuadrante(5, 60, 44.0, comparable=False) is None
    assert cuadrante(None, 60, 44.0) is None
    assert cuadrante(5, None, 44.0) is None
    assert cuadrante(5, 60, None) is None


# --------------------------------------------------------------------------------------
# Corte de siniestralidad y matriz
# --------------------------------------------------------------------------------------


def marco_matriz() -> pd.DataFrame:
    """Cuatro filas: comparable sobre el umbral, no comparable, bajo el umbral y con NaN."""
    return pd.DataFrame(
        {
            "riesgo_comparable": ["A", "Renta", "B", "C"],
            "siniestralidad_comparable": ["S", "N", "S", "S"],
            "sobre_umbral": ["S", "S", "N", "S"],
            "primas_netas": [1000.0, 500.0, 10.0, 200.0],
            "siniestros_netos": [600.0, 450.0, 9.0, 20.0],
            "primas_retenidas": [800.0, 500.0, 10.0, 100.0],
            "siniestros_retenidos": [200.0, 450.0, 9.0, 60.0],
            "variacion_interanual": [5.0, 20.0, -3.0, math.nan],
            "tcac": [-2.0, 10.0, 4.0, 1.0],
            "indice_siniestralidad_directa": [60.0, 90.0, 90.0, 10.0],
            "indice_siniestralidad_retenida": [25.0, 90.0, 90.0, math.nan],
            "corte_siniestralidad_directa": [50.0, 50.0, 50.0, 50.0],
            "corte_siniestralidad_retenida": [28.888889, 28.888889, 28.888889, 28.888889],
            "cuadrante_interanual_directa": [1, math.nan, math.nan, math.nan],
        }
    )


def test_corte_siniestralidad():
    marco = marco_matriz()
    # Solo A y C: (600 + 20) / (1000 + 200) y (200 + 60) / (800 + 100).
    assert corte_siniestralidad(marco) == pytest.approx(100 * 620 / 1200)
    assert corte_siniestralidad(marco, "retenida") == pytest.approx(100 * 260 / 900)
    sin_primas = marco.assign(primas_netas=[0.0, 500.0, 10.0, 0.0])
    assert corte_siniestralidad(sin_primas) is None
    with pytest.raises(KeyError):
        corte_siniestralidad(marco, "cedida")


def test_clasificar_matriz():
    resultado = clasificar_matriz(marco_matriz())
    columnas = [
        "py_cuadrante_interanual_directa",
        "py_cuadrante_interanual_retenida",
        "py_cuadrante_tcac_directa",
        "py_cuadrante_tcac_retenida",
    ]
    assert all(columna in resultado.columns for columna in columnas)
    # A: crece 5 %, directa 60 > 50 (1); retenida 25 < 28.9 (2); TCAC -2: 3 y 4.
    assert list(resultado.loc[0, columnas]) == [1, 2, 3, 4]
    # Renta: no comparable; B: bajo el umbral; C: sin variación o sin índice retenido.
    assert resultado.loc[1, columnas].isna().all()
    assert resultado.loc[2, columnas].isna().all()
    assert pd.isna(resultado.loc[3, "py_cuadrante_interanual_directa"])
    assert resultado.loc[3, "py_cuadrante_tcac_directa"] == 2  # TCAC 1 %, índice 10 < 50
    assert pd.isna(resultado.loc[3, "py_cuadrante_tcac_retenida"])


def test_resumen_matriz():
    resumen = resumen_matriz(marco_matriz())
    assert resumen["filas"] == 4
    assert resumen["sobre_umbral"] == 3
    assert resumen["no_comparables"] == 1
    assert resumen["corte_siniestralidad_directa"] == 50.0
    assert resumen["por_cuadrante_interanual_directa"] == {1: 1, None: 3}
