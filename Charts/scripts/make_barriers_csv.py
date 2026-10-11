"""Build Charts/Data/Barriers.csv for the Section 5 barriers heatmap.

Reads the "Barriers to use" tab of Charts/Raw_Data/Internet_Use_Combined.xlsx (share of each group
who report each barrier to using the internet more; people could pick more than one, so a group's
shares add up to a little over 100%) and adds a short column label for each barrier (the full survey wording is kept for tooltips).
Shares stay as decimals (0.29 = 29%); the chart formats them as percentages.

Uses only the Python standard library.
Run from the repo root:  python3 Charts/scripts/make_barriers_csv.py
"""
import csv
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

SOURCE = Path('Charts/Raw_Data/Internet_Use_Combined.xlsx')
SHEET = 'Barriers to use'
OUT = Path('Charts/Data/Barriers.csv')

# survey wording -> short label used on the chart
SHORT = {
    'No barriers - I use the internet regularly and do not need to use more often': 'No barriers',
    'I am concerned about privacy or scams': 'Privacy or scams',
    'My internet connection is too slow/unreliable': 'Slow connection',
    'The internet is not a priority for me': 'Not a priority',
    'The internet is too expensive for me': 'Too expensive',
    'I am concerned about online content that can offend, shame or cause conflict': 'Offensive content',
    'I am not confident using the internet': 'Not confident',
    'I do not have convenient access to the internet': 'No easy access',
    'Other': 'Other',
    'I have a disability that restricts me from using the internet': 'Disability',
    'Not enough content is available in my first language': 'Language',
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


rows = read_sheet(SOURCE, SHEET)
assert rows[0] == ['Dimension', 'Group', 'Barrier', 'Share'], f'unexpected columns: {rows[0]}'
out_rows = [{'Dimension': d, 'Group': g, 'Barrier': SHORT[b], 'Wording': b, 'Share': round(float(s), 4)} for d, g, b, s in rows[1:]]

with open(OUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['Dimension', 'Group', 'Barrier', 'Wording', 'Share'])
    writer.writeheader()
    writer.writerows(out_rows)
print(f'Wrote {len(out_rows)} rows to {OUT}')
