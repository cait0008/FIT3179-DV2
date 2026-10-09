"""Build Charts/Data/ExclusionBands.csv for the Section 4 diverging stacked bar.

Reads the "Digital exclusion" tab of Charts/Raw_Data/Internet_Use_Combined.xlsx
(share of each group in each ADII band) and writes one row per group per band (long format).
Shares stay as decimals (0.41 = 41%); the chart formats them as percentages.

Uses only the Python standard library (an .xlsx file is a zip of XML files).
Run from the repo root:  python3 Charts/scripts/make_exclusion_bands_csv.py
"""
import csv
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

SOURCE = Path('Charts/Raw_Data/Internet_Use_Combined.xlsx')
SHEET = 'Digital exclusion'
OUT = Path('Charts/Data/ExclusionBands.csv')
BANDS = ['Highly excluded', 'Excluded', 'Included', 'Highly included']

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


rows = read_sheet(SOURCE, SHEET)
header, data = rows[0], rows[1:]
assert header[2:] == BANDS, f'unexpected columns: {header}'

out_rows = []
for dimension, group, *shares in data:
    for band, share in zip(BANDS, shares):
        out_rows.append({'Dimension': dimension, 'Group': group, 'Band': band, 'Share': round(float(share), 4)})

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['Dimension', 'Group', 'Band', 'Share'])
    writer.writeheader()
    writer.writerows(out_rows)
print(f'Wrote {len(out_rows)} rows to {OUT}')
