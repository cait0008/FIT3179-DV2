"""Build Charts/Data/GroupsByMeasure.csv for the Section 4 heatmap.

Reads the "<Measure> score" tab of the three ADII sub-index workbooks in Charts/Raw_Data
and writes one row per group per measure (long format), with that measure's national
average on every row so the chart can colour each cell by its gap from the average.

Uses only the Python standard library (an .xlsx file is a zip of XML files).
Run from the repo root:  python3 Charts/scripts/make_groups_by_measure_csv.py
"""
import csv
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

RAW = Path('Charts/Raw_Data')
OUT = Path('Charts/Data/GroupsByMeasure.csv')
SOURCES = [
    ('Access', 'Access_Combined.xlsx', 'Access score'),
    ('Affordability', 'Affordability_Combined.xlsx', 'Affordability score'),
    ('Digital Ability', 'Digital_Ability_Combined.xlsx', 'Digital Ability score'),
]

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


out_rows = []
for measure, filename, sheet in SOURCES:
    rows = read_sheet(RAW / filename, sheet)[1:]  # skip header: Dimension, Group, score, difference
    national = next(float(r[2]) for r in rows if r[0] == 'National')
    # the 'National average' row is kept (first row) as a benchmark, matching the exclusion-bands chart
    for dimension, group, score, *_ in rows:
        out_rows.append({
            'Dimension': dimension,
            'Group': group,
            'Measure': measure,
            'Score': round(float(score), 1),
            'National': round(national, 1),
        })

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['Dimension', 'Group', 'Measure', 'Score', 'National'])
    writer.writeheader()
    writer.writerows(out_rows)
print(f'Wrote {len(out_rows)} rows to {OUT}')
