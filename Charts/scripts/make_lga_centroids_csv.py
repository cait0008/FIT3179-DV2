"""Build Charts/Data/LGA_Centroids.csv for the Section 3 spike map.

Works out one point per LGA (where its spike stands) from the ABS 2025 LGA boundary file.
For LGAs made of several pieces (islands), the point is the centre of the largest piece.
The spike map joins these points to Charts/Data/LGA_ADII.csv on LGA_CODE25.

Uses only the Python standard library.
Run from the repo root:  python3 Charts/scripts/make_lga_centroids_csv.py
"""
import csv
import json
from pathlib import Path

BOUNDARIES = Path('Charts/Raw_Data/Shape_Files/LGA_2025_AUST_GDA2020.json')
OUT = Path('Charts/Data/LGA_Centroids.csv')

topo = json.loads(BOUNDARIES.read_text())
(sx, sy), (tx, ty) = topo['transform']['scale'], topo['transform']['translate']


def decode(arc):
    """TopoJSON arcs store quantised steps; turn one into a list of [lon, lat] points."""
    x = y = 0
    points = []
    for dx, dy in arc:
        x, y = x + dx, y + dy
        points.append((x * sx + tx, y * sy + ty))
    return points


arcs = [decode(a) for a in topo['arcs']]


def ring_points(ring):
    points = []
    for i in ring:
        arc = arcs[i] if i >= 0 else arcs[~i][::-1]  # negative index = arc used backwards
        points.extend(arc if not points else arc[1:])
    return points


def area_and_centre(points):
    """Signed area and centre of a polygon ring (shoelace formula, in degrees)."""
    a = cx = cy = 0
    for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    return a / 2, (cx / (3 * a), cy / (3 * a)) if a else points[0]


out_rows = []
for geom in next(iter(topo['objects'].values()))['geometries']:
    if geom.get('type') is None:
        continue  # e.g. "No usual address" LGAs have no shape
    polygons = geom['arcs'] if geom['type'] == 'MultiPolygon' else [geom['arcs']]
    outer_rings = [area_and_centre(ring_points(p[0])) for p in polygons]  # p[0] = outer ring, the rest are holes
    _, (lon, lat) = max(outer_rings, key=lambda r: abs(r[0]))
    out_rows.append({'LGA_CODE25': geom['properties']['LGA_CODE25'], 'Longitude': round(lon, 4), 'Latitude': round(lat, 4)})

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
    writer.writeheader()
    writer.writerows(out_rows)
print(f'Wrote {len(out_rows)} LGA centre points to {OUT}')
