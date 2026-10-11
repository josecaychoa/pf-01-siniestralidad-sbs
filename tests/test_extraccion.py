"""Pruebas de la extracción a formato largo con hojas sintéticas (sin datos de la SBS)."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from pf_01_siniestralidad_sbs.extraccion import (
    EstructuraError,
    Libro,
    a_numero,
    extraer_hoja,
    leer_corte,
    motor_excel,
    separar_llamadas,
)

N = np.nan
CORTE = date(2026, 8, 31)


def libro(hoja: str, filas: list[list[object]]) -> Libro:
    return Libro("S-367", CORTE, "abc", {hoja: pd.DataFrame(filas, dtype=object)})


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Avla Perú 5/", ("Avla Perú", "5/")),
        ("Total + Rigel + Coface Seguros (3)", ("Total + Rigel + Coface Seguros", "(3)")),
        ("Mapfre Perú (abs) (2)", ("Mapfre Perú (abs)", "(2)")),
        ("Nacional de Seguros 7/ 8/", ("Nacional de Seguros", "7/ 8/")),
        (
            "Índice (Plan de Cuentas desde Mar26) 7/ 9/ / Patrimonio",
            (
                "Índice (Plan de Cuentas desde Mar26) / Patrimonio",
                "7/ 9/",
            ),
        ),
        ("Liquidez Corriente ", ("Liquidez Corriente", "")),
    ],
)
def test_separar_llamadas(texto, esperado):
    assert separar_llamadas(texto) == esperado


def test_leer_corte_admite_setiembre_y_septiembre():
    assert leer_corte(pd.DataFrame([["Al 30 de Setiembre del 2025"]])) == date(2025, 9, 30)
    assert leer_corte(pd.DataFrame([[N], ["Al 31 de Agosto del 2026"]])) == CORTE
    with pytest.raises(EstructuraError):
        leer_corte(pd.DataFrame([["sin fecha"]]))


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(1, 1.0), (-2.5, -2.5), ("3.5", 3.5), ("", None), ("n.a.", None), ("-", None), (N, None)],
)
def test_a_numero(valor, esperado):
    assert a_numero(valor) == esperado


def test_motor_por_firma_y_no_por_extension():
    assert motor_excel(b"PK\x03\x04resto") == "openpyxl"
    assert motor_excel(bytes.fromhex("D0CF11E0A1B11AE1")) == "xlrd"


def hoja_riesgos() -> list[list[object]]:
    return [
        ["Primas de Seguros Netas según Riesgos 1/", N, N, N],
        ["Al 31 de Agosto del 2026", N, N, N],
        ["( En Miles de Soles )", N, N, N],
        [N, N, N, N],
        ["Riesgos / Empresas", "Avla Perú 1/", "Rigel (2)", "Total"],
        [N, N, N, N],
        ["RAMOS GENERALES", 10.0, 0, 10.0],
        ["   Incendio", 4.0, "n.a.", 4.0],
        [N, N, N, N],
        ["Riesgos / Empresas", "Avla Perú (3)", "Rigel", "Total"],
        ["Vida", 1.0, 2.0, 3.0],
        ["Mediante Resolución SBS N° 1-2020, se autorizó…", N, N, N],
    ]


def test_matriz_formato_largo_y_encabezado_repetido():
    filas = extraer_hoja(libro("P009", hoja_riesgos()), "P009")
    df = pd.DataFrame(filas)
    assert len(df) == 3 + 2 + 3  # «n.a.» no es un valor; la nota al pie no entra
    assert set(df.unidad) == {"En Miles de Soles"}
    assert df.cuadro.iloc[0] == "Primas de Seguros Netas según Riesgos"
    incendio = df[df.concepto == "Incendio"].iloc[0]
    assert (incendio.sangria, incendio.fila, incendio.columna) == (3, 8, 2)
    assert (incendio.empresa, incendio.llamadas_empresa) == ("Avla Perú", "1/")
    vida = df[(df.concepto == "Vida") & (df.columna == 2)].iloc[0]
    assert vida.llamadas_empresa == "(3)"  # se usa el encabezado repetido
    assert df[df.es_total].empresa.unique().tolist() == ["Total"]


def test_corte_del_rotulo_distinto_al_del_archivo():
    filas = hoja_riesgos()
    filas[1][0] = "Al 31 de Diciembre del 2025"
    with pytest.raises(EstructuraError, match="rótulo"):
        extraer_hoja(libro("P009", filas), "P009")


def test_indicadores_con_seccion():
    filas = [
        ["Indicadores por Empresas de Seguros 1/", N, N, N],
        ["Al 31 de Agosto del 2026", N, N, N],
        [N, N, N, N],
        ["Indicadores / Empresas", N, "AuguStar", "Total"],
        [N, N, N, N],
        ["DE SOLVENCIA  (N° de veces)", N, N, N],
        [N, "Patrimonio Efectivo / Requerimientos Patrimoniales", "", ""],
        [N, "Liquidez Corriente ", 1.5, 1.2],
        ["DE GESTIÓN", N, N, N],
        [N, "ROE", 0.1, "-"],
    ]
    df = pd.DataFrame(extraer_hoja(libro("P004", filas), "P004"))
    assert len(df) == 3
    assert df.set_index("concepto").seccion.to_dict() == {
        "Liquidez Corriente": "DE SOLVENCIA (N° de veces)",
        "ROE": "DE GESTIÓN",
    }


def test_bloques_mn_me_total_con_etiqueta_repetida():
    filas = [
        ["Estado de Situación Financiera", N, N, N, N, N, N, N, N],
        ["Al 31 de Agosto del 2026", N, N, N, N, N, N, N, N],
        ["(En Miles de  Soles)", N, N, N, N, N, N, N, N],
        ["Activo", N, "EMPRESA A 1/", N, N, "Activo", "TOTAL EMPRESAS DE SEGUROS", N, N],
        [N, "MN", "ME", "TOTAL", N, N, "MN", "ME", "TOTAL"],
    ]
    for k in range(5):
        etiqueta = f"   Cuenta {k}"
        filas.append([etiqueta, 1.0, 2.0, 3.0, N, etiqueta, 10.0, 20.0, 30.0])
    filas.append(["Tipo de Cambio Contable: S/ 3.621", N, N, N, N, N, N, N, N])
    df = pd.DataFrame(extraer_hoja(libro("P001", filas), "P001"))
    assert len(df) == 5 * 2 * 3
    assert sorted(df.moneda.unique()) == ["ME", "MN", "TOTAL"]
    a = df[(df.empresa == "EMPRESA A") & (df.moneda == "TOTAL")]
    assert a.valor.tolist() == [3.0] * 5 and set(a.llamadas_empresa) == {"1/"}
    assert df[df.es_total].empresa.unique().tolist() == ["TOTAL EMPRESAS DE SEGUROS"]
    assert set(df.sangria) == {3}


def test_bloques_sin_fila_de_monedas():
    filas = [["Estado", N], ["Al 31 de Agosto del 2026", N], ["Activo", "EMPRESA"]]
    with pytest.raises(EstructuraError, match="monedas"):
        extraer_hoja(libro("P001", filas), "P001")
