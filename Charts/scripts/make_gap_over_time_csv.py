"""Build Charts/Data/GapOverTime.csv for the Section 6 "gap over time" chart.

Reads the "<Measure> over time" tabs of the Access and Digital Ability workbooks in Charts/Raw_Data
(Affordability and the overall ADII have no time series) and writes one row per group per year,
with the national average for that year and the group's gap from it.

Years are 2020, 2021, 2022 and 2024 (there was no 2023 survey). First Nations and remoteness groups
only have 2022 and 2024; empty cells are skipped.

Uses only the Python standard library.
Run from the repo root:  python3 Charts/scripts/make_gap_over_time_csv.py
"""
import csv
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

RAW = Path('Charts/Raw_Data')
OUT = Path('Charts/Data/GapOverTime.csv')
SOURCES = [
    ('Access', 'Access_Combined.xlsx', 'Access over time'),
    ('Digital Ability', 'Digital_Ability_Combined.xlsx', 'Digital Ability over time'),
]

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL_ID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def read_sheet(path, sheet_name):
    """Return the rows of one worksheet as lists of strings (empty cells kept as '')."""
    z = zipfile.ZipFile(path)
    shared = [''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS)]
    targets = {r.get('Id'): r.get('Target') for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    sheet = next(s for s in ET.fromstring(z.read('xl/workbook.xml')).find('m:sheets', NS) if s.get('name') == sheet_name)
    xml = ET.fromstring(z.read('xl/' + targets[sheet.get(REL_ID)].replace('/xl/', '').lstrip('/')))
    rows = []
    for row in xml.iter('{%s}row' % NS['m']):
        values = {}
        for cell in row.findall('m:c', NS):
            col = ''.join(ch for ch in cell.get('r') if ch.isalpha())  # e.g. 'C' from 'C5', so blanks keep their column
            v = cell.find('m:v', NS)
            values[col] = '' if v is None else (shared[int(v.text)] if cell.get('t') == 's' else v.text)
        rows.append([values.get(c, '') for c in 'ABCDEF'])
    return rows


out_rows = []
for measure, filename, sheet in SOURCES:
    rows = read_sheet(RAW / filename, sheet)
    years = rows[0][2:]
    national = dict(zip(years, (float(v) for v in rows[1][2:])))
    for dimension, group, *scores in rows[1:]:
        for year, score in zip(years, scores):
            if score == '':
                continue
            out_rows.append({
                'Measure': measure, 'Dimension': dimension, 'Group': group, 'Year': int(year),
                'Score': round(float(score), 1), 'National': round(national[year], 1),
                'Gap': round(float(score) - national[year], 1),
            })

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
    writer.writeheader()
    writer.writerows(out_rows)
print(f'Wrote {len(out_rows)} rows to {OUT}')
