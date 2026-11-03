"""Paquete 5.2 de PF-01: compone el documento PDF de LinkedIn (#15).

Uso (desde la raíz del repositorio, después de scripts/figuras_linkedin.py):
    uv run python scripts/componer_documento.py                       # solo el HTML
    uv run --with playwright python scripts/componer_documento.py --pdf

Escribe linkedin/documento.html, con 10 páginas de 1080 × 1350 px según la skill
linkedin-pieza-editorial v1.3 y la marca JC. v2.4, y, con --pdf, linkedin/documento.pdf
exportado con Chromium (Playwright). Playwright no es dependencia del proyecto: `--with` lo
instala solo para esta ejecución; la primera vez hace falta `uv run --with playwright
playwright install chromium`. Las figuras se insertan en línea para que usen la fuente Geist
(licencia OFL, en linkedin/fuentes/), en instancias
estáticas de 400, 600 y 700 para que el PDF incruste TrueType y no Type 3.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from pf_01_siniestralidad_sbs import pieza_linkedin as pl

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[1]
CARPETA = RAIZ / "linkedin"
FIGURAS = CARPETA / "figuras"
HTML = CARPETA / "documento.html"
PDF = CARPETA / "documento.pdf"
TOTAL = 10
P = " %"  # espacio fino no separable antes del signo de porcentaje (RAE)

SELLO = "Datos al 31 de agosto de 2026 · Boletín mensual y cuadros por riesgo de la SBS"
REPOSITORIO = "github.com/josecaychoa/pf-01-siniestralidad-sbs"
FIRMA = "José Caycho A. · Business Analyst Senior y DBA · Procesos · Datos"
PERFILES = "linkedin.com/in/jcaychoasin · github.com/josecaychoa"
PORTAFOLIO = "github.com/josecaychoa"

REFERENCIAS = [
    "Superintendencia de Banca, Seguros y AFP. (s. f.-a). <i>Boletín mensual</i> [Conjunto de "
    "datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/"
    "EstadisticaSistemaFinancieroResultados.aspx?c=S-367",
    "Superintendencia de Banca, Seguros y AFP. (s. f.-b). <i>Índice de siniestralidad directa y "
    "retenida según riesgos</i> [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de "
    "https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-403",
    "Superintendencia de Banca, Seguros y AFP. (s. f.-c). <i>Primas de seguros netas, cedidas y "
    "retenidas según riesgos</i> [Conjunto de datos]. Recuperado el 11 y el 27 de octubre de 2026, "
    "de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-401",
    "Superintendencia de Banca, Seguros y AFP. (s. f.-d). <i>Siniestros de primas de seguros "
    "netas, cedidas y retenidas según riesgos</i> [Conjunto de datos]. Recuperado el 11 y el 27 de "
    "octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/"
    "EstadisticaSistemaFinancieroResultados.aspx?c=S-402",
    "Superintendencia de Banca, Seguros y AFP. (2026). <i>Resolución S.B.S. N.º 00085-2026: "
    "Modifica el Plan de Cuentas para las Empresas del Sistema Asegurador</i>. "
    "https://intranet2.sbs.gob.pe/dv_int_cn/2551/v1.0/Adjuntos/R.%2000085-2026.pdf",
]

ESTILO = """
@font-face { font-family: Geist; src: url("fuentes/Geist-400.ttf"); font-weight: 400; }
@font-face { font-family: Geist; src: url("fuentes/Geist-600.ttf"); font-weight: 600; }
@font-face { font-family: Geist; src: url("fuentes/Geist-700.ttf"); font-weight: 700; }
@font-face { font-family: "Geist Mono"; src: url("fuentes/GeistMono-400.ttf"); font-weight: 400; }
@page { size: 1080px 1350px; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Geist, Arial, sans-serif; color: #141822; background: #F4F6F9; }
.pagina { width: 1080px; height: 1350px; position: relative; overflow: hidden;
  background: #F4F6F9; page-break-after: always; break-after: page; }
.pagina:last-child { page-break-after: auto; break-after: auto; }
.oscura { background: #0F1F45; color: #FFFFFF; }
.marca { position: absolute; left: 72px; top: 52px; font-size: 44px; font-weight: 700;
  letter-spacing: -0.05em; color: #141822; }
.marca b { color: #2A5CDA; }
.oscura .marca { color: #FFFFFF; } .oscura .marca b { color: #7379B4; }
.etiqueta { position: absolute; right: 72px; top: 66px; font-size: 18px; color: #636975; }
.oscura .etiqueta { color: #DAE9FF; }
.figura-n { position: absolute; left: 72px; top: 118px; font-size: 18px; font-weight: 600;
  color: #636975; }
.titular { position: absolute; left: 72px; top: 150px; width: 936px; font-size: 54px;
  font-weight: 600; line-height: 1.12; letter-spacing: -0.025em; color: #141822; }
.titular span { color: #636975; }
.tarjeta { position: absolute; left: 72px; top: 420px; width: 936px; height: 730px;
  background: #FFFFFF; border-radius: 28px; padding: 40px; }
.tarjeta svg { display: block; }
.pie { position: absolute; left: 72px; right: 72px; bottom: 72px; display: flex;
  justify-content: space-between; align-items: flex-end; gap: 32px; font-size: 18px;
  line-height: 1.4; color: #636975; }
.pie .folio { white-space: nowrap; }
.pie p + p { margin-top: 4px; }
.texto { font-size: 28px; line-height: 1.42; color: #141822; }
.texto p + p { margin-top: 24px; }
.recuadro { margin-top: 36px; background: #EFE9FE; border-radius: 24px; padding: 28px 32px;
  font-size: 25px; line-height: 1.42; color: #0F1F45; }
.recuadro.cielo { background: #DAE9FF; }
.recuadro strong { font-weight: 600; }
table { width: 100%; border-collapse: collapse; font-size: 24px; line-height: 1.35; }
th { background: #0F1F45; color: #FFFFFF; font-weight: 600; text-align: left; padding: 12px 16px; }
td { padding: 12px 16px; vertical-align: top; color: #141822; }
tr:nth-child(even) td { background: #F4F6F9; }
td:first-child { font-weight: 600; width: 160px; }
.referencias { position: absolute; left: 72px; top: 260px; width: 936px; height: 960px;
  background: #FFFFFF; border-radius: 28px; padding: 48px 48px; }
.referencias p { font-size: 20px; line-height: 1.45; padding-left: 40px; text-indent: -40px;
  color: #141822; overflow-wrap: anywhere; }
.referencias p + p { margin-top: 22px; }
.portada-titular { position: absolute; left: 72px; top: 250px; width: 936px; font-size: 90px;
  font-weight: 600; line-height: 1.06; letter-spacing: -0.03em; color: #FFFFFF; }
.portada-titular span { color: #DAE9FF; }
.cifra { position: absolute; left: 72px; top: 640px; font-size: 220px; font-weight: 600;
  letter-spacing: -0.04em; color: #00B4A4; line-height: 1; }
.cifra-frase { position: absolute; left: 72px; top: 900px; width: 860px; font-size: 30px;
  line-height: 1.35; color: #DAE9FF; }
.firma { position: absolute; left: 72px; right: 72px; bottom: 72px; font-size: 22px;
  line-height: 1.45; color: #DAE9FF; }
.firma strong { color: #FFFFFF; font-weight: 600; }
.firma .fuente { margin-top: 18px; font-size: 18px; }
.cierre-titular { position: absolute; left: 72px; top: 250px; width: 936px; font-size: 72px;
  font-weight: 600; line-height: 1.1; letter-spacing: -0.03em; color: #FFFFFF; }
.cierre-titular span { color: #DAE9FF; }
.cierre-datos { position: absolute; left: 72px; top: 620px; width: 936px; font-size: 30px;
  line-height: 1.5; color: #DAE9FF; }
.cierre-datos .url { color: #FFFFFF; font-weight: 600; font-size: 36px; }
.cierre-datos code { font-family: "Geist Mono", Consolas, monospace; font-size: 26px;
  color: #FFFFFF; }
"""


def nota(contenido: str) -> str:
    """Nota APA 7 con «Nota.» en cursiva."""
    return f"<p><i>Nota.</i> {contenido}</p>"


def cabecera(oscura: bool = False) -> str:
    del oscura
    return '<div class="marca">JC<b>.</b></div><div class="etiqueta">Portafolio · PF-01</div>'


def pie(numero: int, contenido_nota: str) -> str:
    return (
        f'<div class="pie"><div>{nota(contenido_nota)}<p>{SELLO}</p></div>'
        f'<div class="folio">{numero:02d} / {TOTAL:02d}</div></div>'
    )


def titular(idea: str, continuacion: str, etiqueta: str = "") -> str:
    etiqueta_html = f'<div class="figura-n">{etiqueta}</div>' if etiqueta else ""
    return f'{etiqueta_html}<h1 class="titular">{idea} <span>{continuacion}</span></h1>'


def svg_en_linea(nombre: str, n: int) -> str:
    """SVG de linkedin/figuras con identificadores únicos dentro del documento."""
    svg = (FIGURAS / nombre).read_text(encoding="utf-8")
    svg = svg.replace('id="t"', f'id="t{n}"').replace('id="d"', f'id="d{n}"')
    return svg.replace('aria-labelledby="t d"', f'aria-labelledby="t{n} d{n}"')


def pagina_figura(numero: int, n: int, archivo: str, idea: str, cont: str, fuente: str) -> str:
    return (
        f'<section class="pagina">{cabecera()}{titular(idea, cont, f"Figura {n}")}'
        f'<div class="tarjeta">{svg_en_linea(archivo, n)}</div>{pie(numero, fuente)}</section>'
    )


def paginas() -> list[str]:
    nombres = sorted(pl.FIGURAS)
    portada = (
        '<section class="pagina oscura">'
        f"{cabecera(True)}"
        '<h1 class="portada-titular">Dos riesgos explican el alza '
        "<span>de la siniestralidad de 2026.</span></h1>"
        '<div class="cifra">+7.5 p.&nbsp;p.</div>'
        '<p class="cifra-frase">La siniestralidad directa del sistema asegurador peruano pasó de '
        f"41.4{P} a 48.9{P} entre agosto de 2025 y agosto de 2026.</p>"
        f'<div class="firma"><strong>{FIRMA}</strong><br>{PERFILES}<br>Noviembre de 2026'
        '<p class="fuente">Elaboración propia con datos de la Superintendencia de Banca, '
        "Seguros y AFP [SBS] (s. f.-a).</p></div></section>"
    )
    fuente_contribucion = (
        "Elaboración propia con datos de SBS (s. f.-a, s. f.-c, s. f.-d). Contribución = "
        "siniestros del riesgo sobre las primas del sistema en cada corte; suman el cambio total."
    )
    titular_metodo = titular(
        "El índice calculado replica el de la SBS",
        "con una diferencia máxima de 0.0015 p.&nbsp;p.",
        "Tabla 1",
    )
    nota_metodo = (
        "Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d). "
        "Validación en reports/validacion_resultados.md."
    )
    metodo = (
        f'<section class="pagina">{cabecera()}{titular_metodo}'
        '<div class="tarjeta"><table>'
        "<tr><th>Etapa</th><th>Qué hice</th></tr>"
        "<tr><td>Datos</td><td>Cuatro conjuntos públicos de la SBS: 9 cortes de 2019 a 2026 y "
        "los cuadros mensuales de 2025 y 2026, con un manifiesto de URL, fecha y SHA-256.</td></tr>"
        "<tr><td>Proceso</td><td>Python 3.13 con uv, carga en Oracle Database 23ai Free e "
        "indicadores en vistas SQL.</td></tr>"
        "<tr><td>Control</td><td>Índice del sistema cuadrado con el publicado en los 9 cortes; "
        "pruebas automatizadas, entre ellas que las contribuciones suman el cambio.</td></tr>"
        "</table>"
        '<div class="recuadro"><strong>Lo que corregí.</strong> La primera versión del informe '
        "decía que la siniestralidad «rompió la tendencia» en 2026. Al descomponer el cambio por "
        "riesgo vi que el alza se concentraba en dos riesgos, y que uno coincidía con un cambio "
        "contable. Ahora descompongo toda variación agregada antes de escribir una conclusión."
        "</div></div>"
        f"{pie(7, nota_metodo)}"
        "</section>"
    )
    limitaciones = (
        f'<section class="pagina">{cabecera()}'
        f"{titular('El quiebre contable es una inferencia,', 'no un dato confirmado por la SBS.')}"
        '<div class="tarjeta"><div class="texto">'
        "<p>No pude leer el Anexo de la Resolución SBS N.º 00085-2026 (SBS, 2026). "
        "La atribución se apoya en el mes, en el título y en la nota del cuadro de "
        "siniestros (SBS, s. f.-d).</p>"
        "<p>Renta Particular (+1.60 p.&nbsp;p.), otro seguro de vida con ahorro, también sube en "
        "marzo de 2026; su efecto no está aislado.</p>"
        "<p>Los cortes de agosto acumulan 8 meses y solo se comparan entre sí. Los montos son "
        "nominales y el análisis no evalúa a las empresas.</p></div>"
        '<div class="recuadro cielo"><strong>Qué implica.</strong> Antes de comparar el índice de '
        "2026 con años anteriores, conviene separar el efecto contable del técnico. Sin ese "
        "ajuste, la comparación probablemente sobrestima el deterioro.</div></div>"
        f"{pie(8, 'Elaboración propia con datos de SBS (s. f.-a, s. f.-d, 2026).')}"
        "</section>"
    )
    referencias = (
        f'<section class="pagina">{cabecera()}'
        '<h1 class="titular">Referencias</h1><div class="referencias">'
        + "".join(f"<p>{r}</p>" for r in REFERENCIAS)
        + f'</div><div class="pie"><div></div><div class="folio">09 / {TOTAL:02d}</div></div>'
        "</section>"
    )
    cierre = (
        '<section class="pagina oscura">'
        f"{cabecera(True)}"
        '<h1 class="cierre-titular">Los datos, el código y las pruebas '
        "<span>están en el repositorio público.</span></h1>"
        f'<div class="cierre-datos"><p class="url">{REPOSITORIO}</p>'
        "<p>Para reproducirlo: <code>uv sync</code> y los pasos de «Cómo reproducir» del "
        "README.</p>"
        f"<p>Todos los proyectos del portafolio: <strong>{PORTAFOLIO}</strong></p></div>"
        f'<div class="firma"><strong>{FIRMA}</strong><br>{PERFILES}<br>'
        "Estrategia, procesos y datos.</div></section>"
    )
    return [
        portada,
        pagina_figura(
            2,
            1,
            nombres[0],
            "Vida Individual e Incendio suman +8.0 p.&nbsp;p.;",
            "los otros 46 riesgos restan 0.5.",
            fuente_contribucion,
        ),
        pagina_figura(
            3,
            2,
            nombres[1],
            "Sin esos dos riesgos,",
            f"el índice pasa de 44.7{P} a 45.0{P}.",
            "Elaboración propia con datos de SBS (s. f.-a, s. f.-c, s. f.-d). Índice directo "
            "acumulado de enero a agosto.",
        ),
        pagina_figura(
            4,
            3,
            nombres[2],
            "Vida Individual salta en marzo de 2026,",
            "cuando cambia el plan de cuentas.",
            "Elaboración propia con datos de SBS (s. f.-c, s. f.-d, 2026). Siniestros del mes: "
            "diferencia entre acumulados; marzo mezcla el criterio nuevo y el anterior.",
        ),
        pagina_figura(
            5,
            4,
            nombres[3],
            f"Incendio: 224.0{P} de siniestralidad directa;",
            f"55.4{P} en lo que se retuvo.",
            "Elaboración propia con datos de SBS (s. f.-a, s. f.-c, s. f.-d).",
        ),
        pagina_figura(
            6,
            5,
            nombres[4],
            f"Doce meses a agosto de 2026: 44.5{P},",
            f"tras cuatro años de descenso hasta 39.4{P}.",
            "Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d). Doce meses, "
            f"para comparar con los cierres anuales; el 48.9{P} de la portada y de la figura 2 es "
            "el acumulado de enero a agosto. Último punto: diciembre de 2025 más enero a agosto "
            "de 2026, menos enero a agosto de 2025.",
        ),
        metodo,
        limitaciones,
        referencias,
        cierre,
    ]


def documento() -> str:
    cuerpo = "\n".join(paginas())
    html = (
        '<!doctype html>\n<html lang="es"><head><meta charset="utf-8">'
        "<title>PF-01 · Dos riesgos explican el alza de la siniestralidad de 2026</title>"
        f"<style>{ESTILO}</style></head><body>\n{cuerpo}\n</body></html>\n"
    )
    assert len(re.findall(r'<section class="pagina', html)) == TOTAL
    return html


def exportar_pdf() -> None:
    """Exporta el HTML a PDF con Chromium (Playwright)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page()
        pagina.goto(HTML.as_uri())
        pagina.evaluate("document.fonts.ready")
        pagina.pdf(
            path=str(PDF),
            width="1080px",
            height="1350px",
            print_background=True,
            prefer_css_page_size=True,
        )
        navegador.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pdf", action="store_true", help="exporta también el PDF")
    args = parser.parse_args(argv)
    HTML.write_text(documento(), encoding="utf-8")
    print(f"Escrito: {HTML}")
    if args.pdf:
        exportar_pdf()
        print(f"Escrito: {PDF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
