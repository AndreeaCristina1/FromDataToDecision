# -*- coding: utf-8 -*-
"""Loading of the INS TEMPO-Online panel (year x locality x type of structure) from data/raw/tempo_panel/.

Layout of the source files (kept exactly as received, with Romanian headers):
  * rows 1-5: title, header, years (columns D:AB = 2001..2025), unit of measure;
  * column A: type of tourist accommodation structure (filled only on the first row of a block, then "-");
  * column C: locality (SIRUTA code + name) or "TOTAL" for the type total; type "Total" is the county aggregate;
  * empty cells are marked ":" and become NaN (see the additivity checks in stage1_describe/).

The Romanian type names are the keys of the data; TYPE_EN gives the English names used in the outputs.
"""
import numpy as np
import openpyxl

from .paths import RAW_TEMPO

YEARS = list(range(2001, 2026))
FILES = {
    "C": "capacitati cazare turism 2001-2025.xlsx",   # capacity in operation (bed-days)
    "S": "sosiri turisti 2001-2025.xlsx",             # arrivals (tourists)
    "N": "innoptari turisti 2001-2025.xlsx",          # overnight stays
}
FILES_RESIDENCE = {                                    # county level, by residence of the tourists
    "S": "sosiri turisti romani-straini 2001-2025.xlsx",
    "N": "innoptari turisti romani-straini 2001-2025.xlsx",
}
LABEL = {"C": "capacity_bed_days", "S": "arrivals", "N": "overnight_stays"}

AGRO = "Pensiuni agroturistice"
HOTELS = "Hoteluri"
TYPE_EN = {
    "Total": "Total", "Hoteluri": "Hotels", "Hosteluri": "Hostels", "Hoteluri apartament": "Apartment hotels",
    "Moteluri": "Motels", "Vile turistice": "Tourist villas", "Cabane turistice": "Tourist chalets", "Campinguri": "Campsites",
    "Popasuri turistice": "Tourist stopovers", "Casute turistice": "Tourist cottages", "Pensiuni turistice": "Tourist guesthouses",
    "Pensiuni agroturistice": "Agritourism guesthouses", "Apartamente si camere de inchiriat": "Apartments and rooms for rent",
}


def type_en(name):
    return TYPE_EN.get(name, name)


def _num(v):
    if v is None:
        return np.nan
    s = str(v).strip()
    if s in (":", "", "-"):
        return np.nan
    try:
        return float(s)
    except ValueError:
        return np.nan


def _sheet_rows(filename):
    wb = openpyxl.load_workbook(RAW_TEMPO / filename, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i >= 5:
            yield row


def load_panel(key):
    """Return {(type, locality): array of 25 values}; type "Total" is the county aggregate, locality "TOTAL" the type total."""
    out, cur = {}, None
    for row in _sheet_rows(FILES[key]):
        a, loc = row[0], row[2]
        if loc is None:
            continue
        if a not in (None, "-"):
            cur = str(a).strip()
        out[(cur, str(loc).strip())] = np.array([_num(x) for x in row[3:28]], dtype=float)
    return out


def split_locality(raw):
    """'78711 BAIA DE FIER' -> ('78711', 'Baia de Fier'); 'TOTAL' -> ('', 'TOTAL')."""
    if raw == "TOTAL":
        return "", raw
    parts = raw.split(" ", 1)
    code, name = (parts[0], parts[1]) if len(parts) == 2 and parts[0].isdigit() else ("", raw)
    name = name.title().replace(" De ", " de ").replace("Municipiul ", "").replace("Oras ", "")
    return code, name


def load_county_by_residence(key):
    """County level: {(type, 'Total' | 'Romani' | 'Straini'): array of 25 values}."""
    out, cur = {}, None
    for row in _sheet_rows(FILES_RESIDENCE[key]):
        a, who = row[0], row[1]
        if who is None:
            continue
        if a not in (None, "-"):
            cur = str(a).strip()
        out[(cur, str(who).strip())] = np.array([_num(x) for x in row[3:28]], dtype=float)
    return out


if __name__ == "__main__":
    for k in "CSN":
        panel = load_panel(k)
        print(k, len(panel), "series |", sorted({t for t, _ in panel}))
        print("   localities:", len({u for _, u in panel if u != "TOTAL"}))
