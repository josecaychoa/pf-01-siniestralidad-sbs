"""Pruebas de la serie mensual S-401 y S-402 (paquete 4.4, #56; CC-PF-01-02).

La serie versionada (data/processed/serie_mensual_riesgos.csv) debe cuadrar con el corte de 3.2
(data/processed/indicadores_riesgo.csv) en agosto de 2025 y de 2026, y ubicar el cambio del
cuadro S-402 en marzo de 2026 (Resolución SBS N.º 00085-2026). Las pruebas que releen los
cuadros originales se omiten sin data/raw/mensual/, como en GitHub Actions.
"""

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from pf_01_siniestralidad_sbs.fuentes import catalogo_mensual, cortes_mensuales, fin_de_mes
from pf_01_siniestralidad_sbs.serie_mensual import (
    MEDIDAS,
    CuadreError,
    _cuadrar,
    construir_serie,
    leer_csv,
)

RAIZ = Path(__file__).resolve().parents[1]
CSV = RAIZ / "data" / "processed" / "serie_mensual_riesgos.csv"
INDICADORES = RAIZ / "data" / "processed" / "indicadores_riesgo.csv"
DIR_MENSUAL = RAIZ / "data" / "raw" / "mensual"
VIDA = "Vida Individual de Largo Plazo"


@pytest.fixture(scope="module")
def serie():
    return leer_csv(CSV)


def test_fin_de_mes_incluye_febrero_y_diciembre():
    assert fin_de_mes(2026, 2) == date(2026, 2, 28)
    assert fin_de_mes(2025, 12) == date(2025, 12, 31)


def test_cortes_mensuales_de_enero_de_2025_a_agosto_de_2026():
    cortes = cortes_mensuales()
    assert len(cortes) == 20
    assert cortes[0] == date(2025, 1, 31) and cortes[-1] == date(2026, 8, 31)


def test_catalogo_mensual_con_40_cuadros_y_su_url():
    archivos = catalogo_mensual()
    assert len(archivos) == 40
    assert archivos[0].nombre == "S-401-en2025.XLS"
    assert archivos[-1].url.endswith("/2026/Agosto/S-402-ag2026.XLS")


def test_serie_con_20_meses_y_48_riesgos(serie):
    assert len(serie) == 960
    assert serie["fecha_corte"].nunique() == 20
    assert serie["riesgo_comparable"].nunique() == 48


@pytest.mark.parametrize("corte", ["2025-08-31", "2026-08-31"])
def test_agosto_cuadra_con_el_corte_de_3_2(serie, corte):
    """Mismos montos por riesgo que el Boletín Mensual (S-367) usado en 3.2 (± 0.01 mil soles)."""
    indicadores = pd.read_csv(INDICADORES)
    referencia = indicadores[indicadores["fecha_corte"] == corte].set_index("riesgo_comparable")
    mensual = serie[serie["fecha_corte"] == date.fromisoformat(corte)].set_index(
        "riesgo_comparable"
    )
    assert set(mensual.index) == set(referencia.index)
    for medida in MEDIDAS:
        diferencia = (mensual[medida] - referencia[medida]).abs().max()
        assert diferencia < 0.01, medida


def test_montos_del_mes_suman_el_acumulado(serie):
    agosto = serie[serie["fecha_corte"] == date(2026, 8, 31)].set_index("riesgo_comparable")
    del_anio = serie[serie["fecha_corte"].map(lambda d: d.year) == 2026]
    suma = del_anio.groupby("riesgo_comparable")["siniestros_netos_mes"].sum()
    assert (suma - agosto["siniestros_netos"]).abs().max() < 0.05


def test_cuadro_s402_cambia_en_marzo_de_2026(serie):
    titulos = serie.drop_duplicates("fecha_corte").set_index("fecha_corte")
    con_obligaciones = titulos["cuadro_siniestros"].str.contains("Otras Obligaciones")
    assert not con_obligaciones[titulos.index < date(2026, 3, 31)].any()
    assert con_obligaciones[titulos.index >= date(2026, 3, 31)].all()
    notas = titulos.loc[titulos.index >= date(2026, 3, 31), "nota_plan_de_cuentas"]
    assert notas.str.contains("085-2026").all()


def test_quiebre_de_vida_individual_de_largo_plazo(serie):
    vida = serie[serie["riesgo_comparable"] == VIDA].set_index("fecha_corte")[
        "siniestros_netos_mes"
    ]
    assert vida[date(2026, 3, 31)] == pytest.approx(310_648.1, abs=0.1)
    antes = vida[vida.index < date(2026, 3, 31)].mean()
    despues = vida[vida.index > date(2026, 3, 31)].mean()
    assert antes == pytest.approx(9_512.6, abs=0.1)
    assert despues / antes > 10


def test_cuadrar_detecta_diferencias():
    tabla = pd.DataFrame(
        {"fecha_corte": [date(2026, 1, 31)] * 2, **{m: [1.0, 2.0] for m in MEDIDAS}}
    )
    _cuadrar(tabla, {(date(2026, 1, 31), "primas_netas"): 3.0})
    with pytest.raises(CuadreError):
        _cuadrar(tabla, {(date(2026, 1, 31), "primas_netas"): 10.0})


@pytest.mark.skipif(
    not (DIR_MENSUAL / "S-402-ag2026.XLS").exists(), reason="sin data/raw/mensual: descargar"
)
def test_serie_versionada_igual_a_la_reconstruida(serie):
    reconstruida = construir_serie(DIR_MENSUAL)
    pd.testing.assert_frame_equal(
        reconstruida.reset_index(drop=True), serie.reset_index(drop=True), atol=0.01
    )


def test_verificar_meses_detecta_un_mes_faltante():
    from pf_01_siniestralidad_sbs.serie_mensual import MesesIncompletosError, _verificar_meses

    completa = pd.DataFrame(
        {"riesgo_comparable": ["A"] * 3, "fecha_corte": [fin_de_mes(2026, m) for m in (1, 2, 3)]}
    )
    _verificar_meses(completa)
    with pytest.raises(MesesIncompletosError):
        _verificar_meses(completa.drop(index=1))
