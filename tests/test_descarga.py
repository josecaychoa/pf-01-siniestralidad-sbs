"""Pruebas de la descarga y del manifiesto, sin red (la descarga se simula)."""

import hashlib
import io
import zipfile
from datetime import date

import pytest

from pf_01_siniestralidad_sbs.descarga import (
    ArchivoReemplazadoError,
    DescargaError,
    descargar,
    leer_manifiesto,
    validar_firma,
)
from pf_01_siniestralidad_sbs.fuentes import ArchivoSBS, catalogo


def zip_con_libro(nombre: str = "Avance 2026 08_act.xlsx", contenido: bytes = b"x") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr(nombre, contenido)
    return buffer.getvalue()


def test_catalogo_y_urls():
    archivos = catalogo()
    assert len(archivos) == 12
    assert sum(a.serie == "S-367" for a in archivos) == 9
    assert archivos[0].url == (
        "https://intranet2.sbs.gob.pe/estadistica/financiera/2019/Diciembre/S-367-di2019.ZIP"
    )
    assert archivos[-1].nombre == "S-403-ag2026.XLS"
    assert ArchivoSBS("S-401", date(2025, 9, 30), "XLS").url.endswith(
        "/2025/Setiembre/S-401-se2025.XLS"
    )


def test_validar_firma_rechaza_html():
    validar_firma(b"PK\x03\x04...")
    validar_firma(bytes.fromhex("D0CF11E0A1B11AE1"))
    with pytest.raises(DescargaError):
        validar_firma(b"<html>Incapsula</html>")


def test_descarga_registra_y_luego_verifica(tmp_path):
    archivo = ArchivoSBS("S-367", date(2026, 8, 31), "ZIP")
    contenido = zip_con_libro()
    llamadas = []

    def falso(url):
        llamadas.append(url)
        return contenido, "Mon, 05 Oct 2026 21:44:09 GMT"

    registros = descargar([archivo], tmp_path, pausa=0, obtener_fn=falso)
    reg = registros[archivo.nombre]
    assert reg.sha256 == hashlib.sha256(contenido).hexdigest()
    assert reg.libro_interno == "Avance 2026 08_act.xlsx"
    assert reg.fecha_descarga.endswith("-05:00")
    assert leer_manifiesto(tmp_path / "manifest.csv")[archivo.nombre] == reg

    # Segunda corrida: el archivo ya existe y coincide; no se vuelve a descargar.
    descargar([archivo], tmp_path, pausa=0, obtener_fn=falso)
    assert len(llamadas) == 1


def test_archivo_reemplazado_por_la_sbs_detiene_el_proceso(tmp_path):
    archivo = ArchivoSBS("S-367", date(2026, 8, 31), "ZIP")
    descargar([archivo], tmp_path, pausa=0, obtener_fn=lambda u: (zip_con_libro(), ""))
    (tmp_path / archivo.nombre).unlink()  # clon limpio: el manifiesto existe, el archivo no
    nuevo = zip_con_libro(contenido=b"version corregida")
    with pytest.raises(ArchivoReemplazadoError, match="versión distinta"):
        descargar([archivo], tmp_path, pausa=0, obtener_fn=lambda u: (nuevo, ""))
    assert not (tmp_path / archivo.nombre).exists()  # data/raw no se modifica


def test_archivo_local_alterado(tmp_path):
    archivo = ArchivoSBS("S-401", date(2026, 8, 31), "XLS")
    xls = bytes.fromhex("D0CF11E0A1B11AE1") + b"datos"
    descargar([archivo], tmp_path, pausa=0, obtener_fn=lambda u: (xls, ""))
    (tmp_path / archivo.nombre).write_bytes(xls + b"!")
    with pytest.raises(ArchivoReemplazadoError, match="no coincide"):
        descargar([archivo], tmp_path, pausa=0, obtener_fn=lambda u: (xls, ""))
