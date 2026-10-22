"""Pruebas de tabla_tiempos (paquete 3.4, #25): cifras, figura publicada y tabla del README.

Ninguna prueba escribe en docs/procesos/: la figura publicada lleva un manifiesto de
procedencia (Content Credentials) que no debe regenerarse; las escrituras van a tmp_path.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from pf_01_siniestralidad_sbs.tabla_tiempos import (
    ACTIVIDADES,
    Cifras,
    construir_svg,
    escribir,
    filas,
    leer_totales,
    numero,
    pagina_impresion,
    partir,
    tabla_markdown,
)

RAIZ = Path(__file__).resolve().parents[1]
PROCESOS = RAIZ / "docs" / "procesos"
CSV = PROCESOS / "PF-01_tiempos.csv"
SVG = PROCESOS / "PF-01_tiempos.svg"

ENCABEZADO = (
    "proceso,actividad,tarea,metodo,cantidad,unidad,minutos_por_unidad,minutos,supuesto_o_fuente"
)


def sin_procedencia(svg: str) -> str:
    """Quita el manifiesto C2PA (espacio de nombres y <metadata>) que agrega la publicación."""
    svg = re.sub(r' xmlns:c2pa="[^"]*"', "", svg)
    return re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.DOTALL)


@pytest.fixture
def totales_publicados():
    return leer_totales(CSV)


def test_numero_con_punto_decimal_y_millares_con_espacio():
    assert numero(85.11) == "85.1"
    assert numero(0.69) == "0.7"
    assert numero(1234567.891, 2) == "1 234 567.89"


def test_cifras_calcula_ahorro_y_porcentaje():
    c = Cifras(asis=50.0, tobe=10.0)
    assert c.ahorro == 40.0
    assert c.porcentaje == 80.0


def test_leer_totales_suma_por_proceso_y_actividad(tmp_path):
    ruta = tmp_path / "tiempos.csv"
    ruta.write_text(
        "\n".join(
            [
                ENCABEZADO,
                "AS-IS,Obtención,a,Estimación del autor,2,boletín,3,6,x",
                "AS-IS,Obtención,b,Estimación del autor,1,revisión,4,4,x",
                "TO-BE,Obtención,c,Mediana de 3 corridas medidas,1,corrida,0.5,0.5,x",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    totales = leer_totales(ruta)
    assert totales["AS-IS"]["Obtención"] == 10.0
    assert totales["TO-BE"]["Obtención"] == 0.5
    assert totales["TO-BE"]["Control"] == 0.0


def test_csv_publicado_cubre_las_cuatro_actividades(totales_publicados):
    for proceso in ("AS-IS", "TO-BE"):
        assert set(totales_publicados[proceso]) == set(ACTIVIDADES)


def test_totales_publicados(totales_publicados):
    total = filas(totales_publicados)[-1][1]
    assert total.asis == pytest.approx(95.0)
    assert total.tobe == pytest.approx(9.89)
    assert numero(total.ahorro) == "85.1"
    assert numero(total.porcentaje) == "89.6"


def test_svg_bien_formado_con_las_cifras(totales_publicados):
    svg = construir_svg(totales_publicados)
    raiz = ET.fromstring(svg)
    assert raiz.tag == "{http://www.w3.org/2000/svg}svg"
    for cifra in ("95.0", "9.9", "85.1", "89.6 %", "Portafolio · PF-01"):
        assert cifra in svg
    assert "href" not in svg  # sin recursos externos


def test_figura_publicada_coincide_con_la_generada(totales_publicados):
    publicada = SVG.read_text(encoding="utf-8")
    assert sin_procedencia(publicada) == construir_svg(totales_publicados)


def test_readme_contiene_la_tabla_del_csv(totales_publicados):
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    assert tabla_markdown(totales_publicados) in readme


def test_tabla_markdown_total_en_negrita(totales_publicados):
    ultima = tabla_markdown(totales_publicados).splitlines()[-1]
    assert ultima == "| **Total** | **95.0** | **9.9** | **85.1** | **89.6 %** |"


def test_partir_no_supera_el_maximo_ni_corta_palabras():
    texto = "La actualización con un corte nuevo pasa de 95.0 a 9.9 minutos por actividad."
    lineas = partir(texto, 20)
    assert all(len(linea) <= 20 for linea in lineas)
    assert " ".join(lineas) == texto


def test_pagina_impresion_ajusta_la_pagina_a_la_figura(totales_publicados):
    svg = construir_svg(totales_publicados)
    html = pagina_impresion(svg)
    alto = re.search(r'height="(\d+)"', svg).group(1)
    assert f"@page{{size:1200px {alto}px;margin:0}}" in html
    assert svg.rstrip() in html


def test_escribir_no_reemplaza_sin_permiso(tmp_path):
    ruta = tmp_path / "figura.svg"
    assert escribir(ruta, "uno")
    assert not escribir(ruta, "dos")
    assert ruta.read_text(encoding="utf-8") == "uno"
    assert escribir(ruta, "dos", sobrescribir=True)
    assert ruta.read_text(encoding="utf-8") == "dos"
