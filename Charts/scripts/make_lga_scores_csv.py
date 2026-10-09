"""Build Charts/Data/LGA_ADII.csv for the Section 3 LGA choropleth.

Reads the "LGA scores" tab of Charts/Raw_Data/ADII_National_LGA_Combined.xlsx (ADII score per LGA)
and attaches each LGA's ABS 2025 code (LGA_CODE25) from the LGA boundary file, so the map can join
on the code instead of on names.

Names are matched within each state. Most match directly (ignoring ABS suffixes such as
"Campbelltown (NSW)"); the rest differ only in wording and are listed in NAME_FIXES below.
The script stops with an error if any ADII LGA can't be matched.

Uses only the Python standard library.
Run from the repo root:  python3 Charts/scripts/make_lga_scores_csv.py
"""
import csv
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

WORKBOOK = Path('Charts/Raw_Data/ADII_National_LGA_Combined.xlsx')
SHEET = 'LGA scores'
BOUNDARIES = Path('Charts/Raw_Data/Shape_Files/LGA_2025_AUST_GDA2020.json')
OUT = Path('Charts/Data/LGA_ADII.csv')

STATES = {'1': 'NSW', '2': 'VIC', '3': 'QLD', '4': 'SA', '5': 'WA', '6': 'TAS', '7': 'NT', '8': 'ACT', '9': 'OT'}

# (state, ADII name) -> ABS 2025 name, where the wording differs
NAME_FIXES = {
    ('NSW', 'Armidale Regional'): 'Armidale',
    ('NSW', 'Bathurst Regional'): 'Bathurst',
    ('NSW', 'Cootamundra-Gundagai Regional'): 'Cootamundra-Gundagai',
    ('NSW', 'Greater Hume Shire'): 'Greater Hume',
    ('NSW', 'Mid-Western Regional'): 'Mid-Western',
    ('NSW', 'Nambucca'): 'Nambucca Valley',
    ('NSW', 'Queanbeyan-Palerang Regional'): 'Queanbeyan-Palerang',
    ('NSW', 'Snowy Monaro Regional'): 'Snowy Monaro',
    ('NSW', 'Sutherland Shire'): 'Sutherland',
    ('NSW', 'Tamworth Regional'): 'Tamworth',
    ('NSW', 'The Hills Shire'): 'The Hills',
    ('NSW', 'Upper Hunter Shire'): 'Upper Hunter',
    ('NSW', 'Upper Lachlan Shire'): 'Upper Lachlan',
    ('NSW', 'Warrumbungle Shire'): 'Warrumbungle',
    ('NSW', 'Unincorporated'): 'Unincorporated NSW',
    ('VIC', 'Colac-Otway'): 'Colac Otway',
    ('VIC', 'Moreland'): 'Merri-bek',  # renamed in 2022
    ('VIC', 'Unincorporated'): 'Unincorporated Vic',
    ('QLD', 'Blackall-Tambo'): 'Blackall Tambo',
    ('SA', 'Anangu Pitjantjatjara'): 'Anangu Pitjantjatjara Yankunytjatjara',
    ('SA', 'Berri and Barmera'): 'Berri Barmera',
    ('SA', 'Light (RegC)'): 'Light',
    ('SA', 'Lower Eyre Peninsula'): 'Lower Eyre',
    ('SA', 'Naracoorte and Lucindale'): 'Naracoorte Lucindale',
    ('SA', 'Norwood Payneham St Peters'): 'Norwood Payneham and St Peters',
    ('SA', 'Orroroo/Carrieton'): 'Orroroo Carrieton',
    ('SA', 'Port Pirie City and Dists'): 'Port Pirie',
    ('SA', 'The Coorong'): 'Coorong',
    ('SA', 'Unincorporated'): 'Unincorporated SA',
    ('TAS', 'Glamorgan/Spring Bay'): 'Glamorgan-Spring Bay',
    ('TAS', 'Waratah/Wynyard'): 'Waratah-Wynyard',
    ('WA', 'Augusta-Margaret River'): 'Augusta Margaret River',
    ('WA', 'Kalgoorlie/Boulder'): 'Kalgoorlie-Boulder',
    ('NT', 'Unincorporated'): 'Unincorporated NT',
    ('ACT', 'Unincorporated'): 'Unincorporated ACT',  # the ACT has no councils; ABS covers it as one area
}

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL_ID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def read_sheet(path, sheet_name):
    """Return the rows of one worksheet as lists of strings."""
    z = zipfile.ZipFile(path)
    shared = [''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS)]
    targets = {r.get('Id'): r.get('Target') for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    sheet = next(s for s in ET.fromstring(z.read('xl/workbook.xml')).find('m:sheets', NS) if s.get('name') == sheet_name)
    xml = ET.fromstring(z.read('xl/' + targets[sheet.get(REL_ID)].replace('/xl/', '').lstrip('/')))
    rows = []
    for row in xml.iter('{%s}row' % NS['m']):
        values = []
        for cell in row.findall('m:c', NS):
            v = cell.find('m:v', NS)
            values.append('' if v is None else (shared[int(v.text)] if cell.get('t') == 's' else v.text))
        rows.append(values)
    return rows


def strip_suffix(name):
    """'Campbelltown (NSW)' -> 'campbelltown' (ABS adds a state suffix to names used in more than one state)."""
    return re.sub(r'\s*\((NSW|Vic\.|Qld|SA|WA|Tas\.|NT|ACT|OT)\)\s*$', '', name).strip().lower()


# ABS boundaries: (state, name without suffix) -> properties, for shapes that have a geometry
topology = json.loads(BOUNDARIES.read_text())
abs_lgas = {}
for geom in topology['objects']['LGA_2025_AUST_GDA2020']['geometries']:
    if not geom.get('type'):
        continue  # "No usual address", "Migratory - Offshore - Shipping": no shape to draw
    p = geom['properties']
    abs_lgas[(STATES[p['STE_CODE21']], strip_suffix(p['LGA_NAME25']))] = p

out_rows, unmatched = [], []
for state, name, score, gap, *_ in read_sheet(WORKBOOK, SHEET)[1:]:
    abs_name = NAME_FIXES.get((state, name), name)
    p = abs_lgas.get((state, strip_suffix(abs_name)))
    if p is None:
        unmatched.append((state, name))
        continue
    out_rows.append({
        'LGA_CODE25': p['LGA_CODE25'],
        'LGA_NAME25': p['LGA_NAME25'],
        'ADII_name': name,
        'State': state,
        'ADII score': round(float(score), 1),
        'Gap from national average': round(float(gap), 1),
    })

if unmatched:
    raise SystemExit(f'Could not match {len(unmatched)} LGAs - add them to NAME_FIXES: {unmatched}')

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
    writer.writeheader()
    writer.writerows(out_rows)

scored = {r['LGA_CODE25'] for r in out_rows}
no_score = sorted(f"{STATES[p['STE_CODE21']]} {p['LGA_NAME25']}" for p in abs_lgas.values() if p['LGA_CODE25'] not in scored)
print(f'Wrote {len(out_rows)} LGAs to {OUT}')
print(f'{len(no_score)} LGA shapes have no ADII score (will show as "no data"): {no_score}')
