"""Pruebas de la contribución por riesgo (paquete 4.4, #56; CC-PF-01-02).

La propiedad central: las contribuciones suman exactamente el cambio del índice del sistema.
Ninguna prueba escribe en reports/figures/ (manifiesto de procedencia); solo compara.
"""

import re
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import pytest

from pf_01_siniestralidad_sbs import contribucion as co
from pf_01_siniestralidad_sbs.serie_mensual import leer_csv

RAIZ = Path(__file__).resolve().parents[1]
INDICADORES = RAIZ / "data" / "processed" / "indicadores_riesgo.csv"
MENSUAL = RAIZ / "data" / "processed" / "serie_mensual_riesgos.csv"
FIGURAS = RAIZ / "reports" / "figures"
INICIO, FIN = date(2025, 8, 31), date(2026, 8, 31)


def sin_procedencia(svg: str) -> str:
    """Quita el manifiesto C2PA (espacio de nombres y <metadata>) que agrega la publicación."""
    svg = re.sub(r' xmlns:c2pa="[^"]*"', "", svg)
    return re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.DOTALL)


@pytest.fixture(scope="module")
def cortes():
    return co.leer_cortes(INDICADORES)


@pytest.fixture(scope="module")
def directa(cortes):
    return co.descomponer(cortes, INICIO, FIN, "directa")


@pytest.fixture(scope="module")
def retenida(cortes):
    return co.descomponer(cortes, INICIO, FIN, "retenida")


def riesgo(nombre, pn, sn, pr=1.0, sr=0.0):
    return co.Riesgo(nombre, "Ramo", pn, pr, sn, sr)


def test_contribuciones_suman_el_cambio_con_datos_sinteticos():
    sinteticos = {
        INICIO: [riesgo("A", 100, 40), riesgo("B", 100, 20)],
        FIN: [riesgo("A", 100, 40), riesgo("B", 200, 120), riesgo("C", 100, 10)],
    }
    d = co.descomponer(sinteticos, INICIO, FIN)
    assert d.indice_inicio == pytest.approx(30.0)
    assert d.indice_fin == pytest.approx(42.5)
    assert sum(c.contribucion for c in d.contribuciones) == pytest.approx(d.cambio, abs=1e-12)
    assert d.de("A").contribucion == pytest.approx(10.0 - 20.0)  # más primas en el sistema
    assert d.de("C").contribucion == pytest.approx(2.5)  # riesgo nuevo


def test_medida_desconocida():
    with pytest.raises(ValueError):
        co.indice([riesgo("A", 1, 1)], "anualizada")


def test_cambio_directo_del_sistema(directa):
    """Mismo cambio que la serie de 4.2 (tests/test_figura_serie.py)."""
    assert directa.indice_inicio == pytest.approx(41.3714, abs=1e-4)
    assert directa.indice_fin == pytest.approx(48.9141, abs=1e-4)
    assert directa.cambio == pytest.approx(7.5427, abs=1e-4)


@pytest.mark.parametrize("medida", ["directa", "retenida"])
def test_contribuciones_reales_suman_el_cambio(cortes, medida):
    d = co.descomponer(cortes, INICIO, FIN, medida)
    assert len(d.contribuciones) == 48
    assert sum(c.contribucion for c in d.contribuciones) == pytest.approx(d.cambio, abs=1e-9)


def test_dos_riesgos_explican_el_alza(directa, retenida):
    assert directa.contribuciones[0].riesgo == co.VIDA_LARGO_PLAZO
    assert directa.de(co.VIDA_LARGO_PLAZO).contribucion == pytest.approx(5.12, abs=0.005)
    assert directa.de(co.INCENDIO).contribucion == pytest.approx(2.91, abs=0.005)
    assert retenida.cambio == pytest.approx(5.50, abs=0.005)
    assert retenida.de(co.VIDA_LARGO_PLAZO).contribucion == pytest.approx(6.15, abs=0.005)


def test_indice_sin_los_dos_riesgos(cortes):
    excluidos = (co.VIDA_LARGO_PLAZO, co.INCENDIO)
    assert co.indice(cortes[INICIO], excluir=excluidos) == pytest.approx(44.71, abs=0.005)
    assert co.indice(cortes[FIN], excluir=excluidos) == pytest.approx(45.04, abs=0.005)


def test_principales_conservan_el_total(directa):
    filas = co.principales(directa)
    assert sum(c.contribucion for c in filas) == pytest.approx(directa.cambio, abs=1e-9)
    assert filas[4].riesgo == "Resto (42 riesgos)"


def test_tabla_del_informe(directa, retenida):
    tabla = co.tabla_markdown(directa, retenida)
    assert "| Vida Individual de Largo Plazo | 4.4 | 45.0 | +5.12 | +6.15 |" in tabla
    assert tabla.splitlines()[-1] == "| **Sistema** | **41.4** | **48.9** | **+7.54** | **+5.50** |"
    assert "−479.5" in tabla  # signo menos tipográfico
    informe = (RAIZ / "reports" / "informe.md").read_text(encoding="utf-8")
    assert tabla in informe


def meses_vida():
    tabla = leer_csv(MENSUAL)
    vida = tabla[tabla["riesgo_comparable"] == co.VIDA_LARGO_PLAZO]
    return [
        co.Mes(f.fecha_corte, f.siniestros_netos_mes, f.cuadro_siniestros)
        for f in vida.itertuples()
    ]


@pytest.mark.parametrize(
    ("archivo", "construir"),
    [
        ("PF-01_contribucion.svg", lambda d: co.construir_svg_contribucion(d)),
        ("PF-01_quiebre_vida.svg", lambda d: co.construir_svg_mensual(meses_vida())),
    ],
)
def test_figuras_publicadas_coinciden_con_las_generadas(directa, archivo, construir):
    generada = construir(directa)
    raiz = ET.fromstring(generada)
    assert raiz.tag == "{http://www.w3.org/2000/svg}svg"
    assert "href" not in generada  # sin recursos externos
    assert "Portafolio · PF-01" in generada
    publicada = (FIGURAS / archivo).read_text(encoding="utf-8")
    assert sin_procedencia(publicada) == generada
