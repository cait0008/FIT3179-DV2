"""Build Charts/Data/Capitals.csv for the Section 3 proportional symbol map.

One row per capital city: location, population, and its state/territory's ADII score.
- ADII score and gap: read from the "National & states" tab of
  Charts/Raw_Data/ADII_National_LGA_Combined.xlsx (these are whole-state scores, not city-only scores).
- Population: ABS 2021 Census, usual resident population of each Greater Capital City Statistical Area
  (the ACT for Canberra). VERIFY against ABS QuickStats before submitting: https://abs.gov.au/census/find-census-data/quickstats/2021
- Coordinates: approximate city-centre latitude/longitude.

Uses only the Python standard library.
Run from the repo root:  python3 Charts/scripts/make_capitals_csv.py
"""
import csv
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

WORKBOOK = Path('Charts/Raw_Data/ADII_National_LGA_Combined.xlsx')
SHEET = 'National & states'
OUT = Path('Charts/Data/Capitals.csv')

# state: (city, latitude, longitude, population - ABS 2021 Census GCCSA, to verify)
CAPITALS = {
    'NSW': ('Sydney', -33.87, 151.21, 5231147),
    'VIC': ('Melbourne', -37.81, 144.96, 4917750),
    'QLD': ('Brisbane', -27.47, 153.03, 2526238),
    'WA': ('Perth', -31.95, 115.86, 2116647),
    'SA': ('Adelaide', -34.93, 138.60, 1387290),
    'TAS': ('Hobart', -42.88, 147.33, 247086),
    'NT': ('Darwin', -12.46, 130.85, 139902),
    'ACT': ('Canberra', -35.28, 149.13, 454499),
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


state_scores = {area: (float(score), float(gap)) for grouping, area, score, gap, *_ in read_sheet(WORKBOOK, SHEET)[1:]
                if grouping == 'State/territory'}

out_rows = []
for state, (city, lat, lon, population) in CAPITALS.items():
    score, gap = state_scores[state]
    out_rows.append({'City': city, 'State': state, 'Latitude': lat, 'Longitude': lon, 'Population': population,
                     'State ADII score': round(score, 1), 'Gap from national average': round(gap, 1)})

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
    writer.writeheader()
    writer.writerows(out_rows)
print(f'Wrote {len(out_rows)} capitals to {OUT}')
