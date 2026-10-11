"""Pruebas de los controles del paquete 2.2 y de la integridad de los catálogos (sin datos SBS)."""

import pandas as pd
import pytest

from pf_01_siniestralidad_sbs.validacion import (
    asignar_empresas,
    balance,
    cuadre_totales,
    leer_catalogo,
    monedas,
    normalizar,
    plan_de_cuentas,
    tipo_total,
)

# --------------------------------------------------------------------------------------
# Catálogos
# --------------------------------------------------------------------------------------


def test_catalogo_de_empresas_sin_rangos_superpuestos():
    cat = leer_catalogo("empresas")
    assert (cat["corte_desde"] <= cat["corte_hasta"]).all()
    for _, grupo in cat.groupby("clave_fuente"):
        rangos = grupo.sort_values("corte_desde")[["corte_desde", "corte_hasta"]].to_numpy()
        for (_, fin), (inicio, _) in zip(rangos, rangos[1:], strict=False):
            assert fin < inicio
    assert set(cat["estado"]) <= {"vigente", "liquidada", "absorbida"}
    assert set(cat["en_total_simple"]) <= {"true", "false"}


def test_catalogo_de_riesgos_coherente():
    cat = leer_catalogo("riesgos")
    assert cat["clave"].is_unique
    assert set(cat["clave_padre"]) - {""} <= set(cat["clave"])
    assert (cat["clave"] == cat["riesgo"].map(normalizar)).all()
    assert (cat["tipo"] == "riesgo").sum() == 50
    assert cat.loc[cat["tipo"] == "total", "clave"].tolist() == ["TOTAL"]
    fianzas = cat[cat["riesgo_comparable"] == "Cauciones y fianzas"]
    assert sorted(fianzas["clave"].str[:8]) == ["CAUCIONE", "FIANZAS ", "FIANZAS "]


def test_catalogo_de_cortes():
    cat = leer_catalogo("cortes")
    assert len(cat) == 9 and cat["corte"].is_unique
    assert set(cat["meses_acumulados"]) == {"8", "12"}


# --------------------------------------------------------------------------------------
# Funciones auxiliares
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "clave"),
    [("Rímac ", "RIMAC"), ("Miscelaneos", "MISCELANEOS"), ("Misceláneos", "MISCELANEOS")],
)
def test_normalizar(texto, clave):
    assert normalizar(texto) == clave


def test_tipo_total():
    assert tipo_total("Total") == "simple"
    assert tipo_total("TOTAL EMPRESAS DE SEGUROS") == "simple"
    assert tipo_total("Total + Mapfre Perú (abs)") == "ampliado"
    assert tipo_total("Total +Rigel + Coface Seguros") == "ampliado"
    assert tipo_total("Rímac") == ""


def fila(corte, empresa, valor, hoja="P009", fila_=10, moneda="", concepto="Incendio", columna=1):
    return {
        "serie": "S-367",
        "corte": corte,
        "hoja": hoja,
        "fila": fila_,
        "columna": columna,
        "concepto": concepto,
        "empresa": empresa,
        "moneda": moneda,
        "valor": valor,
    }


def test_asignar_empresas_por_rango_de_corte():
    df = pd.DataFrame(
        [
            fila("2021-12-31", "MAPFRE PERU", 1.0),
            fila("2022-12-31", "Mapfre Perú", 1.0),
            fila("2022-12-31", "Mapfre Perú (abs)", 1.0),
            fila("2020-12-31", "Vida Cámara", 1.0),
            fila("2026-08-31", "Empresa Nueva", 1.0),
            fila("2026-08-31", "Total", 1.0),
        ]
    )
    salida = asignar_empresas(df, leer_catalogo("empresas")).set_index(["corte", "empresa"])
    assert salida.loc[("2021-12-31", "MAPFRE PERU"), "empresa_id"] == "MAPFRE"
    assert salida.loc[("2022-12-31", "Mapfre Perú (abs)"), "en_total_simple"] == "false"
    assert salida.loc[("2022-12-31", "Mapfre Perú"), "en_total_simple"] == "true"
    assert salida.loc[("2020-12-31", "Vida Cámara"), "empresa_canonica"] == "Vivir Seguros"
    assert salida.loc[("2026-08-31", "Empresa Nueva"), "empresa_id"] == ""  # sin equivalencia
    assert salida.loc[("2026-08-31", "Total"), "tipo_total"] == "simple"


# --------------------------------------------------------------------------------------
# Controles
# --------------------------------------------------------------------------------------


def test_cuadre_doble_control_d_pf01_01():
    c = "2022-12-31"
    df = pd.DataFrame(
        [
            fila(c, "Rímac", 100.0),
            fila(c, "Mapfre Perú", 50.0),
            fila(c, "Mapfre Perú (abs)", 20.0),
            fila(c, "Total", 150.0),
            fila(c, "Total + Mapfre Perú (abs)", 170.0),
        ]
    )
    r = cuadre_totales(df)
    assert r.ok and r.revisados == 2
    df.loc[df["empresa"] == "Total + Mapfre Perú (abs)", "valor"] = 172.0
    r = cuadre_totales(df)
    assert r.fallas == 1 and r.detalle["control"].tolist() == ["ampliado"]


def test_cuadre_tolera_redondeo_de_un_mil():
    c = "2024-12-31"
    df = pd.DataFrame(
        [fila(c, "Rímac", 100.4), fila(c, "Pacífico Seguros", 50.4), fila(c, "Total", 150.0)]
    )
    assert cuadre_totales(df).ok


def test_balance_exige_activo_igual_a_pasivo_mas_patrimonio_en_total():
    c = "2026-08-31"
    filas = []
    for moneda, (a, p, pt) in {
        "MN": (80, 30, 50),
        "ME": (20, 40, 0),
        "TOTAL": (100, 70, 30),
    }.items():
        for concepto, valor in (
            ("TOTAL ACTIVO", a),
            ("TOTAL PASIVO ", p),
            ("PATRIMONIO", pt),
            ("TOTAL PASIVO Y PATRIMONIO", p + pt),
        ):
            filas.append(fila(c, "INSUR", float(valor), "P001", 1, moneda, concepto, columna=2))
    df = pd.DataFrame(filas)
    assert balance(df).ok  # MN y ME no cuadran por separado, y no se exige
    df.loc[(df["concepto"] == "TOTAL ACTIVO") & (df["moneda"] == "TOTAL"), "valor"] = 105.0
    assert balance(df).fallas == 1


def test_monedas_excluye_utilidad_por_accion():
    c = "2025-12-31"
    df = pd.DataFrame(
        [
            fila(c, "INSUR", 1.0, "P002", 5, "MN", "Primas"),
            fila(c, "INSUR", 2.0, "P002", 5, "ME", "Primas"),
            fila(c, "INSUR", 3.0, "P002", 5, "TOTAL", "Primas"),
            fila(c, "INSUR", 9.5, "P002", 6, "TOTAL", "UTILIDAD (PERDIDA) POR ACCIÓN BÁSICA"),
        ]
    )
    r = monedas(df)
    assert r.ok and r.revisados == 1


def test_plan_de_cuentas():
    cortes = leer_catalogo("cortes")
    notas = {c: "" for c in cortes["corte"]}
    for c in cortes["corte"]:
        if c >= "2021-12-31":
            notas[c] = "A partir de junio de 2021 ... Resolución SBS N° 976-2021 (31/03/2021)."
    notas["2026-08-31"] += " | A partir de marzo de 2026 ... Resolución SBS N° 085-2026."
    assert plan_de_cuentas(notas, cortes).ok
    notas["2020-12-31"] = "Resolución SBS N° 976-2021"
    assert plan_de_cuentas(notas, cortes).fallas == 1
