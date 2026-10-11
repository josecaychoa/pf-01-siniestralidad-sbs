"""Descarga reproducible de los archivos de la SBS y registro en data/raw/manifest.csv.

Reglas (acta, sección 9, riesgos R3 y R5; 04, sección 8):
- data/raw es inmutable: un archivo ya descargado no se sobrescribe.
- El manifiesto se versiona y funciona como referencia: si un archivo nuevo no coincide con el
  SHA-256 registrado, la SBS lo reemplazó y el proceso se detiene para que el director decida.
- Pausa entre descargas y reintentos con espera creciente; solo se acepta un ZIP o un libro Excel.
"""

from __future__ import annotations

import csv
import hashlib
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pf_01_siniestralidad_sbs.fuentes import ArchivoSBS

ZONA_LIMA = ZoneInfo("America/Lima")
AGENTE = "pf-01-siniestralidad-sbs/0.1 (portafolio de analitica; descarga de datos publicos)"

# Firmas de archivo aceptadas: ZIP/OOXML (xlsx, xlsm) y OLE2 (xls de Excel 97-2003).
FIRMA_ZIP = b"PK\x03\x04"
FIRMA_OLE2 = bytes.fromhex("D0CF11E0A1B11AE1")


class DescargaError(RuntimeError):
    """La descarga falló o el contenido no es el esperado."""


class ArchivoReemplazadoError(RuntimeError):
    """El SHA-256 del archivo no coincide con el registrado en el manifiesto."""


@dataclass
class RegistroManifiesto:
    """Una fila de data/raw/manifest.csv."""

    archivo: str
    serie: str
    corte: str
    url: str
    fecha_descarga: str
    last_modified: str
    bytes: int
    sha256: str
    libro_interno: str


CAMPOS_MANIFIESTO = [f.name for f in fields(RegistroManifiesto)]


def sha256(ruta: Path) -> str:
    """SHA-256 en hexadecimal de un archivo."""
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 16), b""):
            h.update(bloque)
    return h.hexdigest()


def validar_firma(contenido: bytes) -> None:
    """Rechaza respuestas que no son ZIP ni Excel (p. ej., una página HTML de bloqueo)."""
    if not (contenido.startswith(FIRMA_ZIP) or contenido.startswith(FIRMA_OLE2)):
        raise DescargaError("El servidor no devolvió un ZIP ni un libro Excel")


def libro_interno(ruta: Path) -> str:
    """Nombre del único libro dentro de un ZIP del Boletín Mensual; vacío si no es ZIP."""
    if ruta.suffix.upper() != ".ZIP":
        return ""
    with zipfile.ZipFile(ruta) as z:
        libros = [n for n in z.namelist() if not n.endswith("/")]
    if len(libros) != 1:
        raise DescargaError(f"{ruta.name}: se esperaba un libro y hay {len(libros)}")
    return libros[0]


def leer_manifiesto(ruta: Path) -> dict[str, RegistroManifiesto]:
    """Lee el manifiesto existente, indexado por nombre de archivo."""
    if not ruta.exists():
        return {}
    with ruta.open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    return {
        fila["archivo"]: RegistroManifiesto(**{**fila, "bytes": int(fila["bytes"])})
        for fila in filas
    }


def escribir_manifiesto(ruta: Path, registros: dict[str, RegistroManifiesto]) -> None:
    """Escribe el manifiesto ordenado por serie y corte (UTF-8, separador coma)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    orden = sorted(registros.values(), key=lambda r: (r.serie, r.corte))
    with ruta.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS_MANIFIESTO, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(asdict(r) for r in orden)


def obtener(url: str, reintentos: int = 3, espera: float = 2.0) -> tuple[bytes, str]:
    """GET con reintentos y espera creciente (2, 4 y 8 s). Devuelve contenido y Last-Modified."""
    ultimo_error: Exception | None = None
    for intento in range(1, reintentos + 2):
        try:
            solicitud = urllib.request.Request(url, headers={"User-Agent": AGENTE})
            with urllib.request.urlopen(solicitud, timeout=60) as respuesta:
                contenido = respuesta.read()
                ultima_modificacion = respuesta.headers.get("Last-Modified", "")
            validar_firma(contenido)
            return contenido, ultima_modificacion
        except (urllib.error.URLError, TimeoutError, DescargaError) as error:
            ultimo_error = error
            if intento <= reintentos:
                time.sleep(espera * 2 ** (intento - 1))
    raise DescargaError(f"{url}: falló tras {reintentos + 1} intentos ({ultimo_error})")


def descargar(
    archivos: list[ArchivoSBS],
    dir_raw: Path,
    pausa: float = 2.0,
    obtener_fn=obtener,
) -> dict[str, RegistroManifiesto]:
    """Descarga los archivos que falten en dir_raw y actualiza el manifiesto.

    - Archivo presente y registrado: se verifica su SHA-256 (no se descarga).
    - Archivo ausente y registrado: se descarga y debe coincidir con el SHA-256 registrado.
    - Archivo ausente y sin registro: se descarga y se registra.
    """
    dir_raw.mkdir(parents=True, exist_ok=True)
    ruta_manifiesto = dir_raw / "manifest.csv"
    registros = leer_manifiesto(ruta_manifiesto)

    for i, archivo in enumerate(archivos):
        destino = dir_raw / archivo.nombre
        previo = registros.get(archivo.nombre)

        if destino.exists():
            huella = sha256(destino)
            if previo and previo.sha256 != huella:
                raise ArchivoReemplazadoError(
                    f"{archivo.nombre}: el archivo local no coincide con el manifiesto"
                )
            if previo:
                print(f"  ok      {archivo.nombre} (ya descargado, SHA-256 verificado)")
                continue
            ultima_modificacion = ""  # archivo copiado a mano: se registra sin cabecera
        else:
            if i > 0:
                time.sleep(pausa)
            contenido, ultima_modificacion = obtener_fn(archivo.url)
            huella = hashlib.sha256(contenido).hexdigest()
            if previo and previo.sha256 != huella:
                raise ArchivoReemplazadoError(
                    f"{archivo.nombre}: la SBS publicó una versión distinta "
                    f"(registrado {previo.sha256[:12]}…, descargado {huella[:12]}…). "
                    "Revisar el cambio antes de actualizar el manifiesto."
                )
            destino.write_bytes(contenido)
            print(f"  nuevo   {archivo.nombre} ({len(contenido):,} bytes)".replace(",", " "))
            if previo:
                continue  # coincide con la referencia: se conserva el registro original

        registros[archivo.nombre] = RegistroManifiesto(
            archivo=archivo.nombre,
            serie=archivo.serie,
            corte=archivo.corte.isoformat(),
            url=archivo.url,
            fecha_descarga=datetime.now(ZONA_LIMA).isoformat(timespec="seconds"),
            last_modified=ultima_modificacion,
            bytes=destino.stat().st_size,
            sha256=huella,
            libro_interno=libro_interno(destino),
        )

    escribir_manifiesto(ruta_manifiesto, registros)
    return registros
