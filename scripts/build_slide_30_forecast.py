#!/usr/bin/env python3
"""Build the slide-30 rising-phase illustration from pinned FluSight archives."""

import csv
import gzip
import hashlib
import json
import math
from datetime import date, timedelta
from pathlib import Path

FOLDER = Path(__file__).resolve().parents[1] / 'data/slide-30/forecast-example'


def build_forecast_example():
    design = json.loads((FOLDER / 'design.json').read_text())
    sources = json.loads((FOLDER / 'sources.json').read_text())
    tables, metadata = {}, {}
    for source in sources:
        raw = gzip.decompress((FOLDER / source['file']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == source['sha256'], source['file']
        tables[source['name']] = list(csv.DictReader(raw.decode().splitlines()))
        metadata[source['name']] = source
    observed = {date.fromisoformat(r['date']): float(r['value'])
                for r in tables['observed'] if r['location'] == design['location']}
    selected = json.loads((FOLDER / 'selected.json').read_text())
    seasons = []
    for saved, label in zip(selected, design['seasons']):
        year = saved['year']
        november = date(year, 11, 1)
        baseline_date = november + timedelta(days=(5-november.weekday()) % 7+7)
        baseline_rows = [r for r in tables[f'baseline-{year}']
                         if r['location'] == design['location'] and r['date'] == baseline_date.isoformat()]
        assert len(baseline_rows) == 1
        baseline = float(baseline_rows[0]['value'])
        target_date = min(day for day, value in observed.items()
                          if baseline_date <= day < date(year+1, 7, 1)
                          and value >= design['rise_multiple']*baseline)
        reference = target_date-timedelta(weeks=design['hub_horizon_at_comparison'])
        assert saved == {'year': year, 'baseline_date': baseline_date.isoformat(), 'baseline': baseline,
                         'target_date': target_date.isoformat(), 'observed': observed[target_date],
                         'ratio': observed[target_date]/baseline, 'reference_date': reference.isoformat()}
        baseline_release = metadata[f'baseline-{year}']['released_at']
        forecast_release = metadata[f'forecast-{year}']['released_at']
        assert baseline_release <= f'{year}-11-19T23:59:59Z' < forecast_release
        assert forecast_release[:10] <= reference.isoformat() < target_date.isoformat()
        forecast_rows = [r for r in tables[f'forecast-{year}']
                         if r['location'] == design['location'] and r['target'] == 'wk inc flu hosp'
                         and r['output_type'] == 'quantile']
        forecast = []
        for horizon in range(3):
            rows = [r for r in forecast_rows if int(r['horizon']) == horizon]
            quantiles = {float(r['output_type_id']): float(r['value']) for r in rows}
            assert len(quantiles) == len(rows) == 23
            assert all(r['reference_date'] == reference.isoformat() for r in rows)
            end = reference+timedelta(weeks=horizon)
            assert all(r['target_end_date'] == end.isoformat() for r in rows)
            values = [v for _, v in sorted(quantiles.items())]
            assert all(math.isfinite(v) and v >= 0 for v in values)
            assert values == sorted(values)
            forecast.append({'week': horizon-2, 'date': end.isoformat(), 'horizon': horizon,
                             'lower': quantiles[.05]/baseline, 'median': quantiles[.5]/baseline,
                             'upper': quantiles[.95]/baseline,
                             'counts': {str(q): quantiles[q] for q in [.05, .5, .95]}})
        points = []
        for week in range(design['plot_week_range'][0], design['plot_week_range'][1]+1):
            day = target_date+timedelta(weeks=week)
            points.append([week, observed[day]/baseline])
        assert all(a[1] < b[1] for a, b in zip(points, points[1:]))
        assert points[-2][1] < design['rise_multiple'] <= points[-1][1]
        seasons.append({**saved, 'season': label, 'observed_points': points, 'forecast': forecast,
                        'forecast_released_at': forecast_release})
    assert len(seasons) == 3
    ymax = max(max(p[1] for p in s['observed_points']) for s in seasons)
    ymax = max(ymax, max(p['upper'] for s in seasons for p in s['forecast']))
    return {'design': design, 'seasons': seasons, 'y_max': math.ceil(ymax),
            'interval': .9, 'quantile_rows_checked': 207,
            'source_ledger': 'data/slide-30/forecast-example/sources.json'}


if __name__ == '__main__':
    result = build_forecast_example()
    print(json.dumps(result, indent=2))
