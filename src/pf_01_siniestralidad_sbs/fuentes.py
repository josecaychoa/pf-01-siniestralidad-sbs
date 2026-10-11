"""Catálogo de los archivos de la SBS que usa PF-01 (paquete 2.1 de la EDT).

Fuente: Superintendencia de Banca, Seguros y AFP (SBS), Boletín Estadístico de Seguros.
Patrón de URL verificado el 2026-10-11 (Contexto 05, catálogo de fuentes):
https://intranet2.sbs.gob.pe/estadistica/financiera/<año>/<Mes>/<serie>-<mm><año>.<ext>
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

URL_BASE = "https://intranet2.sbs.gob.pe/estadistica/financiera"

# Mes en español (carpeta del servidor) y abreviatura del nombre del archivo.
MESES: dict[int, tuple[str, str]] = {
    1: ("Enero", "en"),
    2: ("Febrero", "fe"),
    3: ("Marzo", "ma"),
    4: ("Abril", "ab"),
    5: ("Mayo", "my"),
    6: ("Junio", "jn"),
    7: ("Julio", "jl"),
    8: ("Agosto", "ag"),
    9: ("Setiembre", "se"),
    10: ("Octubre", "oc"),
    11: ("Noviembre", "no"),
    12: ("Diciembre", "di"),
}

# Nueve cortes del objetivo O1 del acta: diciembre de 2019 a 2025, agosto de 2025 y de 2026.
CORTES_BOLETIN: tuple[date, ...] = (
    date(2019, 12, 31),
    date(2020, 12, 31),
    date(2021, 12, 31),
    date(2022, 12, 31),
    date(2023, 12, 31),
    date(2024, 12, 31),
    date(2025, 12, 31),
    date(2025, 8, 31),
    date(2026, 8, 31),
)

# Cuadros individuales: solo agosto de 2026, como prueba de consistencia.
CORTE_CONSISTENCIA = date(2026, 8, 31)
SERIES_CONSISTENCIA: tuple[str, ...] = ("S-401", "S-402", "S-403")


@dataclass(frozen=True)
class ArchivoSBS:
    """Un archivo publicado por la SBS: serie, fecha de corte y extensión en el servidor."""

    serie: str
    corte: date
    extension: str

    @property
    def nombre(self) -> str:
        """Nombre del archivo tal como lo publica la SBS (p. ej., S-367-ag2026.ZIP)."""
        _, abrev = MESES[self.corte.month]
        return f"{self.serie}-{abrev}{self.corte.year}.{self.extension}"

    @property
    def url(self) -> str:
        """URL de descarga directa en intranet2.sbs.gob.pe."""
        carpeta_mes, _ = MESES[self.corte.month]
        return f"{URL_BASE}/{self.corte.year}/{carpeta_mes}/{self.nombre}"


def catalogo() -> list[ArchivoSBS]:
    """Devuelve los 12 archivos del paquete 2.1: 9 boletines S-367 y 3 cuadros de consistencia."""
    archivos = [ArchivoSBS("S-367", corte, "ZIP") for corte in sorted(CORTES_BOLETIN)]
    archivos += [ArchivoSBS(serie, CORTE_CONSISTENCIA, "XLS") for serie in SERIES_CONSISTENCIA]
    return archivos
