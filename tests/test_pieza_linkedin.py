"""Pruebas de las figuras del documento PDF de LinkedIn (paquete 5.2, #15).

Comprueban las cifras que sostienen el mensaje central y que cada SVG publicado en
linkedin/figuras/ coincide con el generado. Ninguna prueba escribe en el repositorio.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from pf_01_siniestralidad_sbs import contribucion as co
from pf_01_siniestralidad_sbs import pieza_linkedin as pl

RAIZ = Path(__file__).resolve().parents[1]
INDICADORES = RAIZ / "data" / "processed" / "indicadores_riesgo.csv"
MENSUAL = RAIZ / "data" / "processed" / "serie_mensual_riesgos.csv"
FIGURAS = RAIZ / "linkedin" / "figuras"


@pytest.fixture(scope="module")
def cifras():
    return pl.calcular(INDICADORES, MENSUAL)


def test_mensaje_central(cifras):
    d = cifras.directa
    assert round(d.indice_inicio, 1) == 41.4
    assert round(d.indice_fin, 1) == 48.9
    assert round(d.de(co.VIDA_LARGO_PLAZO).contribucion, 2) == 5.12
    assert round(d.de(co.INCENDIO).contribucion, 2) == 2.91
    assert round(cifras.sin_dos_inicio, 1) == 44.7
    assert round(cifras.sin_dos_fin, 1) == 45.0


def test_contribuciones_suman_el_cambio(cifras):
    d = cifras.directa
    assert sum(c.contribucion for c in d.contribuciones) == pytest.approx(d.cambio, abs=1e-9)


def test_incendio_y_doce_meses(cifras):
    assert round(cifras.incendio_directa, 1) == 224.0
    assert round(cifras.incendio_retenida, 1) == 55.4
    assert round(cifras.incendio_cedido, 1) == 89.1
    assert round(cifras.doce_meses, 1) == 44.5
    assert [a for a, _ in cifras.anuales] == list(range(2019, 2026))


def test_vida_mensual(cifras):
    assert len(cifras.vida_mensual) == 20
    marzo = dict(cifras.vida_mensual)[co.MES_NORMA]
    assert round(marzo, 1) == 310.6


@pytest.mark.parametrize("nombre", sorted(pl.FIGURAS))
def test_svg_valido_y_accesible(cifras, nombre):
    raiz = ET.fromstring(pl.FIGURAS[nombre](cifras))
    ns = "{http://www.w3.org/2000/svg}"
    assert raiz.get("viewBox") == f"0 0 {pl.ANCHO} {pl.ALTO}"
    assert raiz.find(f"{ns}title").text
    assert raiz.find(f"{ns}desc").text
    tamanos = [int(t.get("font-size")) for t in raiz.iter(f"{ns}text")]
    assert min(tamanos) >= 22  # legible en el teléfono (LI-05)


@pytest.mark.parametrize("nombre", sorted(pl.FIGURAS))
def test_figura_publicada_coincide(cifras, nombre):
    ruta = FIGURAS / nombre
    if not ruta.exists():
        pytest.skip(f"{ruta.name} aún no está publicada")
    assert ruta.read_text(encoding="utf-8") == pl.FIGURAS[nombre](cifras)
