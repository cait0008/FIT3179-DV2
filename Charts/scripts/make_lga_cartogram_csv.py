"""Build Charts/Data/LGA_Cartogram.csv for the Section 4 LGA Dorling cartogram.

One circle per LGA: area = population (ABS estimated resident population, 30 June 2025), colour = ADII gap.
Vega-Lite can't push circles apart, so this script does the layout and the chart just draws circles at x, y:
  1. Project each LGA's centre point (Charts/Data/LGA_Centroids.csv) with the same conic equal-area
     projection as the other maps, and fit Australia into the chart's WIDTH x HEIGHT pixels.
  2. Give each LGA a radius r = SCALE * sqrt(population), so circle area is proportional to population.
  3. Repeatedly push overlapping circles apart (big circles move less) while pulling each one gently back
     towards its real location. Circles from different states keep a small gap, so state borders show.
  4. Shrink the finished layout evenly (positions and radii together, so nothing starts overlapping) until it
     fits the chart, and centre it.

- Population: Charts/Raw_Data/PopulationEstimatebyLGA_ABS.xlsx (ABS Regional population 2024-25), Tables 1-7
  by LGA code; the ACT has no LGA table, so "Unincorporated ACT" takes the ACT total from Table 8.
- Scores: Charts/Data/LGA_ADII.csv. LGAs without an ADII score are left out (only Christmas Island, which
  would otherwise squeeze the mainland into a corner).

Uses only the Python standard library. Takes about 30 seconds.
Run from the repo root (after make_lga_scores_csv.py and make_lga_centroids_csv.py):
  python3 Charts/scripts/make_lga_cartogram_csv.py
"""
import csv
import math
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

WORKBOOK = Path('Charts/Raw_Data/PopulationEstimatebyLGA_ABS.xlsx')
OUT = Path('Charts/Data/LGA_Cartogram.csv')
WIDTH, HEIGHT, MARGIN = 1104, 640, 20  # must match "width" / "height" in s4_cartogram_lga.vl.json
SCALE = 0.045  # circle radius in px per sqrt(person), before the final fit
PULL = 0.06   # how strongly each circle is pulled back towards its real location on each step
STATE_GAP = 3   # extra px kept between circles from different states, so each state reads as its own cluster
TAS_GAP = 10    # wider gap for Tasmania (Bass Strait), which otherwise merges into Victoria
ACT_CODE = '89399'  # Unincorporated ACT

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL_ID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def read_sheet(path, sheet_name):
    """Return the rows of one worksheet as dicts of column letter -> value."""
    z = zipfile.ZipFile(path)
    shared = [''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS)]
    targets = {r.get('Id'): r.get('Target') for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    sheet = next(s for s in ET.fromstring(z.read('xl/workbook.xml')).find('m:sheets', NS) if s.get('name') == sheet_name)
    xml = ET.fromstring(z.read('xl/' + targets[sheet.get(REL_ID)].replace('/xl/', '').lstrip('/')))
    rows = []
    for row in xml.iter('{%s}row' % NS['m']):
        values = {}
        for cell in row.findall('m:c', NS):
            v = cell.find('m:v', NS)
            col = ''.join(ch for ch in cell.get('r') if ch.isalpha())
            values[col] = '' if v is None else (shared[int(v.text)] if cell.get('t') == 's' else v.text)
        rows.append(values)
    return rows


# ---- population by LGA code (column A = code, D = ERP at 30 June 2025) ----
population = {}
for table in range(1, 8):
    for row in read_sheet(WORKBOOK, f'Table {table}'):
        if row.get('A', '').isdigit() and row.get('D'):
            population[row['A']] = int(float(row['D']))
act = next(r for r in read_sheet(WORKBOOK, 'Table 8') if r.get('B') == 'Australian Capital Territory')
population[ACT_CODE] = int(float(act['D']))

scores = {r['LGA_CODE25']: r for r in csv.DictReader(open('Charts/Data/LGA_ADII.csv'))}
centres = {r['LGA_CODE25']: r for r in csv.DictReader(open('Charts/Data/LGA_Centroids.csv'))}
codes = [c for c in scores if c in centres and c in population]
state = {c: scores[c]['State'] for c in codes}
print('Scored LGAs with no population:', sorted(c for c in scores if c not in population))

# ---- 1. conic equal-area projection, parallels -18 / -36, rotated -132 degrees (same as the maps) ----
p0, p1 = math.radians(-18), math.radians(-36)
n = (math.sin(p0) + math.sin(p1)) / 2
c = 1 + math.sin(p0) * (2 * n - math.sin(p0))
r0 = math.sqrt(c) / n


def project(lon, lat):
    lam, phi = math.radians(lon - 132), math.radians(lat)
    rho = math.sqrt(c - 2 * n * math.sin(phi)) / n
    return rho * math.sin(lam * n), -(r0 - rho * math.cos(lam * n))  # y flipped so north is up on screen


raw = {code: project(float(centres[code]['Longitude']), float(centres[code]['Latitude'])) for code in codes}
xs, ys = [p[0] for p in raw.values()], [p[1] for p in raw.values()]
k = min((WIDTH - 2 * MARGIN) / (max(xs) - min(xs)), (HEIGHT - 2 * MARGIN) / (max(ys) - min(ys)))
home = {code: ((x - min(xs)) * k + MARGIN, (y - min(ys)) * k + MARGIN) for code, (x, y) in raw.items()}


# ---- 2 & 3. radii, then push circles apart ----
def layout(scale):
    r = {code: scale * math.sqrt(population[code]) for code in codes}
    pos = {code: list(home[code]) for code in codes}
    for step in range(520):
        for code in codes if step < 220 else []:  # pull back towards the real location (the last 300 steps only separate)
            pos[code][0] += (home[code][0] - pos[code][0]) * PULL
            pos[code][1] += (home[code][1] - pos[code][1]) * PULL
        for i, a in enumerate(codes):  # separate overlapping pairs
            for b in codes[i + 1:]:
                dx, dy = pos[b][0] - pos[a][0], pos[b][1] - pos[a][1]
                gap = r[a] + r[b] + (0.5 if state[a] == state[b] else TAS_GAP if 'TAS' in (state[a], state[b]) else STATE_GAP)
                if abs(dx) < gap and abs(dy) < gap:
                    d = math.hypot(dx, dy) or 0.01
                    if d < gap:
                        push = (gap - d) / d
                        wa = r[b] ** 2 / (r[a] ** 2 + r[b] ** 2)  # the smaller circle moves more
                        pos[a][0] -= dx * push * wa
                        pos[a][1] -= dy * push * wa
                        pos[b][0] += dx * push * (1 - wa)
                        pos[b][1] += dy * push * (1 - wa)
    left = min(pos[c][0] - r[c] for c in codes); right = max(pos[c][0] + r[c] for c in codes)
    top = min(pos[c][1] - r[c] for c in codes); bottom = max(pos[c][1] + r[c] for c in codes)
    return r, pos, (left, right, top, bottom)


# ---- 4. shrink evenly to fit, and centre ----
r, pos, (left, right, top, bottom) = layout(SCALE)
f = min(1, (WIDTH - 8) / (right - left), (HEIGHT - 8) / (bottom - top))
cx, cy = (left + right) / 2, (top + bottom) / 2
for code in codes:
    pos[code] = [WIDTH / 2 + (pos[code][0] - cx) * f, HEIGHT / 2 + (pos[code][1] - cy) * f]
    r[code] *= f
print(f'shrunk by {f:.2f}; largest radius {max(r.values()):.0f}px')

# ---- write ----
with open(OUT, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['LGA_CODE25', 'LGA', 'State', 'Population', 'ADII score', 'Gap from national average', 'x', 'y', 'r'])
    for code in sorted(codes, key=lambda c: -population[c]):  # biggest first, so small circles draw on top
        s = scores[code]
        writer.writerow([code, s['LGA_NAME25'], s['State'], population[code], s['ADII score'], s['Gap from national average'],
                         round(pos[code][0], 1), round(pos[code][1], 1), round(r[code], 2)])
print(f'Wrote {len(codes)} LGAs to {OUT}')
