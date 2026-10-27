"""Pruebas de serie_sistema (paquete 4.2, #11): serie, figura publicada y tabla del informe.

La serie publicada debe cuadrar con la tabla 1 de reports/validacion_resultados.md (O2).
Ninguna prueba escribe en reports/figures/: la figura publicada puede llevar un manifiesto
de procedencia (Content Credentials) que no debe regenerarse; las escrituras van a tmp_path.
"""

import re
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import pytest

from pf_01_siniestralidad_sbs.serie_sistema import (
    Corte,
    construir_svg,
    corte_interanual,
    leer_serie,
    mes_largo,
    tabla_markdown,
)

RAIZ = Path(__file__).resolve().parents[1]
CSV = RAIZ / "data" / "processed" / "indicadores_riesgo.csv"
SVG = RAIZ / "reports" / "figures" / "PF-01_serie.svg"

ENCABEZADO = (
    "fecha_corte,meses_acumulados,riesgo_comparable,n_riesgos,ramo,siniestralidad_comparable,"
    "columna_total,primas_netas,primas_retenidas,siniestros_netos,siniestros_retenidos,"
    "indice_siniestralidad_directa,indice_siniestralidad_retenida,indice_directa_publicado,"
    "indice_retenida_publicado"
)


def sin_procedencia(svg: str) -> str:
    """Quita el manifiesto C2PA (espacio de nombres y <metadata>) que agrega la publicación."""
    svg = re.sub(r' xmlns:c2pa="[^"]*"', "", svg)
    return re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.DOTALL)


@pytest.fixture
def serie_publicada():
    return leer_serie(CSV)


def test_leer_serie_suma_los_riesgos_de_cada_corte(tmp_path):
    ruta = tmp_path / "indicadores.csv"
    ruta.write_text(
        "\n".join(
            [
                ENCABEZADO,
                "2026-08-31,8,A,1,Ramos generales,S,TOTAL,100,50,40,10,40,20,40,20",
                "2026-08-31,8,B,1,Ramos generales,S,TOTAL,100,50,60,15,60,30,60,30",
                "2025-08-31,8,A,1,Ramos generales,S,TOTAL,80,40,20,8,25,20,25,20",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    serie = leer_serie(ruta)
    assert [c.fecha for c in serie] == [date(2025, 8, 31), date(2026, 8, 31)]
    ultimo = serie[-1]
    assert ultimo.primas_netas == 200.0
    assert ultimo.directa == pytest.approx(50.0)
    assert ultimo.retenida == pytest.approx(25.0)


def test_serie_publicada_cuadra_con_la_nota_de_validacion(serie_publicada):
    """Tabla 1 de reports/validacion_resultados.md, corte de agosto de 2026."""
    assert len(serie_publicada) == 9
    ultimo = serie_publicada[-1]
    assert ultimo.fecha == date(2026, 8, 31)
    assert ultimo.meses == 8
    assert ultimo.primas_netas == pytest.approx(16_784_650, abs=1)
    assert ultimo.directa == pytest.approx(48.9141, abs=1e-4)
    assert ultimo.retenida == pytest.approx(45.7487, abs=1e-4)
    assert serie_publicada[0].directa == pytest.approx(52.9937, abs=1e-4)


def test_corte_interanual_toma_el_mismo_mes_del_anio_anterior(serie_publicada):
    ultimo, anterior = corte_interanual(serie_publicada)
    assert ultimo.fecha == date(2026, 8, 31)
    assert anterior.fecha == date(2025, 8, 31)
    assert ultimo.directa - anterior.directa == pytest.approx(7.5427, abs=1e-4)


def test_mes_largo_en_minuscula():
    assert mes_largo(date(2026, 8, 31)) == "agosto de 2026"


def test_tabla_markdown_con_primas_en_millones(serie_publicada):
    ultima = tabla_markdown(serie_publicada).splitlines()[-1]
    assert ultima == "| 2026-08-31 | 8 | 16 784.7 | 48.9 | 45.7 |"


def test_svg_bien_formado_con_las_cifras(serie_publicada):
    svg = construir_svg(serie_publicada)
    raiz = ET.fromstring(svg)
    assert raiz.tag == "{http://www.w3.org/2000/svg}svg"
    for cifra in ("48.9 %", "45.7 %", "7.5", "Portafolio · PF-01"):
        assert cifra in svg
    assert "href" not in svg  # sin recursos externos


def test_svg_marca_los_cortes_de_agosto_con_puntos_huecos(serie_publicada):
    svg = construir_svg(serie_publicada)
    huecos = svg.count('fill="#FFFFFF" stroke=')
    assert huecos == 4  # 2 cortes de agosto por 2 series


def test_figura_publicada_coincide_con_la_generada(serie_publicada):
    publicada = SVG.read_text(encoding="utf-8")
    assert sin_procedencia(publicada) == construir_svg(serie_publicada)


def test_informe_contiene_la_tabla_de_la_serie(serie_publicada):
    informe = (RAIZ / "reports" / "informe.md").read_text(encoding="utf-8")
    assert tabla_markdown(serie_publicada) in informe


def test_corte_calcula_los_indices():
    corte = Corte(date(2026, 8, 31), 8, 100.0, 50.0, 40.0, 10.0)
    assert corte.directa == pytest.approx(40.0)
    assert corte.retenida == pytest.approx(20.0)
