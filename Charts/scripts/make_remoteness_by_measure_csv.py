"""Build Charts/Data/RemotenessByMeasure.csv for the Section 5 sub-index small-multiple maps.

Reshapes the remoteness rows of Charts/Data/GroupsByMeasure.csv to one row per ABS remoteness area,
with one column per sub-index (Access, Affordability, Digital Ability) holding the score.
A map joins this to the remoteness boundary file on RA_NAME21 (one lookup brings in all three scores).
The last row holds the national averages, which the map uses to work out each area's gap.

Uses only the Python standard library.
Run from the repo root (after make_groups_by_measure_csv.py):  python3 Charts/scripts/make_remoteness_by_measure_csv.py
"""
import csv
from pathlib import Path

SOURCE = Path('Charts/Data/GroupsByMeasure.csv')
OUT = Path('Charts/Data/RemotenessByMeasure.csv')
MEASURES = ['Access', 'Affordability', 'Digital Ability']

areas, national = {}, {}
for row in csv.DictReader(open(SOURCE)):
    if row['Measure'] not in MEASURES:
        continue
    national[row['Measure']] = row['National']
    if row['Dimension'] == 'Remoteness':
        areas.setdefault(row['Group'], {'RA_NAME21': row['Group']})[row['Measure']] = row['Score']

out_rows = list(areas.values()) + [{'RA_NAME21': 'National average', **national}]

with open(OUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['RA_NAME21'] + MEASURES)
    writer.writeheader()
    writer.writerows(out_rows)
print(f'Wrote {len(out_rows)} rows to {OUT}')
