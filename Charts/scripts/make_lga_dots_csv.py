"""Build Charts/Data/LGA_Dots.csv for the Section 4 dot density map.

One dot = PEOPLE_PER_DOT people, scattered at random inside each LGA's real boundary, so dots pile up
where people actually live. Each dot carries its council's ADII gap, which the map uses for colour
(it is the council's average score, not the score of the people the dot stands for).

- Population and gap: the Australia rows of Charts/Data/LGA_Cartogram.csv (ABS ERP 2025 + ADII 2025).
- Boundaries: Charts/Raw_Data/Shape_Files/LGA_2025_AUST_GDA2020.json.
A council's dot count is population / PEOPLE_PER_DOT; the leftover fraction becomes one extra dot by chance
(e.g. 0.6 -> a 60% chance), so totals stay right and small councils still sometimes appear.
The random seed is fixed, so rerunning gives the same dots.

Uses only the Python standard library. Run from the repo root (after make_lga_cartogram_csv.py):
  python3 Charts/scripts/make_lga_dots_csv.py
"""
import csv
import json
import random
from pathlib import Path

PEOPLE_PER_DOT = 5000
OUT = Path('Charts/Data/LGA_Dots.csv')
random.seed(3179)

councils = {r['LGA_CODE25']: r for r in csv.DictReader(open('Charts/Data/LGA_Cartogram.csv')) if r['View'] == 'all'}

topo = json.loads(Path('Charts/Raw_Data/Shape_Files/LGA_2025_AUST_GDA2020.json').read_text())
(sx, sy), (tx, ty) = topo['transform']['scale'], topo['transform']['translate']
arcs = []
for arc in topo['arcs']:  # TopoJSON arcs store quantised steps; turn each into lon/lat points
    x = y = 0
    arcs.append([])
    for dx, dy in arc:
        x, y = x + dx, y + dy
        arcs[-1].append((x * sx + tx, y * sy + ty))


def ring(ids):
    return [pt for i in ids for pt in (arcs[i] if i >= 0 else arcs[~i][::-1])]


def inside(pt, poly):
    """Ray casting: is the point inside this ring?"""
    x, y, hit = pt[0], pt[1], False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


rows = []
for g in next(iter(topo['objects'].values()))['geometries']:
    c = councils.get(g['properties']['LGA_CODE25'])
    if c is None or not g.get('arcs'):
        continue
    polygons = [[ring(r) for r in p] for p in (g['arcs'] if g['type'] == 'MultiPolygon' else [g['arcs']])]
    xs = [pt[0] for p in polygons for pt in p[0]]; ys = [pt[1] for p in polygons for pt in p[0]]
    exact = int(c['Population']) / PEOPLE_PER_DOT
    n = int(exact) + (random.random() < exact - int(exact))
    placed = 0
    while placed < n:  # random point in the bounding box, kept if it falls inside the council (and not in a hole)
        pt = (random.uniform(min(xs), max(xs)), random.uniform(min(ys), max(ys)))
        if any(inside(pt, p[0]) and not any(inside(pt, h) for h in p[1:]) for p in polygons):
            rows.append([round(pt[0], 4), round(pt[1], 4), c['LGA_CODE25'][0], c['LGA'], c['Gap from national average']])
            placed += 1

with open(OUT, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Longitude', 'Latitude', 'State', 'LGA', 'Gap from national average'])
    writer.writerows(rows)
print(f'Wrote {len(rows)} dots ({PEOPLE_PER_DOT:,} people each) to {OUT}')
