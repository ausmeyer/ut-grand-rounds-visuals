#!/usr/bin/env python3
"""Build the linked scenario minima from slide 25's frozen manuscript draws."""

import hashlib
import json
import math
from pathlib import Path

from build_slide_25 import protection, week_index

ROOT = Path(__file__).resolve().parents[1]


def build():
    config = json.loads((ROOT / 'data/slide-30/inputs.json').read_text())
    source = ROOT / config['source']['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == config['source']['sha256']
    original = json.loads(source.read_text())
    assert original['n_draws'] == 5000
    assert config['decision_rule_validated'] is False
    assert config['forecast_evaluation_performed'] is False
    assert [row['draw'] for row in original['scenarios']] == config['scenario_draws']
    scenarios, max_error = [], 0
    for row in original['scenarios']:
        params = row['parameters']
        elapsed = [week_index(w, row['max_week']) for w in row['weeks']]
        candidates = [week_index(w, row['max_week']) for w in original['candidate_weeks']]
        for vaccination, saved in zip(candidates, row['remaining']):
            remaining = math.fsum(b * (1-protection(t-vaccination, params))
                                 for b, t in zip(row['burden'], elapsed))
            max_error = max(max_error, abs(remaining-saved))
        best = min(range(len(candidates)), key=row['remaining'].__getitem__)
        best_week = original['candidate_weeks'][best]
        dose_time = candidates[best]
        regret = [value-row['remaining'][best] for value in row['remaining']]
        assert regret[best] == 0 and all(value >= 0 for value in regret)
        assert sum(value < 1e-12 for value in regret) == 1
        assert best_week in row['weeks']
        protection_points = [[-.5, 0]]
        for i in range(159):
            t = i/4
            if t == dose_time+params['immune_lag_weeks']:
                protection_points.append([t, 0])
            protection_points.append([t, protection(t-dose_time, params)])
        assert protection(0, params) == 0
        assert all(0 <= point[1] <= .8 for point in protection_points)
        scenarios.append({
            'draw': row['draw'], 'season': row['season'], 'max_week': row['max_week'],
            'burden_points': list(map(list, zip(elapsed, row['burden']))),
            'protection_points': protection_points,
            'decision_points': list(map(list, zip(candidates, regret))),
            'best_index': best, 'best_week': best_week, 'dose_time': dose_time,
            'epidemic_at_dose': row['burden'][row['weeks'].index(best_week)],
            'protection_at_dose': 0, 'immune_lag_weeks': params['immune_lag_weeks'],
        })
    assert len(scenarios) == 10 and max_error < 1e-12
    data = {**config, 'n_draws': original['n_draws'], 'scenarios': scenarios,
            'burden_y_max': math.ceil(max(max(r['burden']) for r in original['scenarios'])*100)/100,
            'protection_y_max': .8,
            'regret_y_max': math.ceil(max(max(p[1] for p in s['decision_points']) for s in scenarios)*10)/10,
            'validation': {'candidate_totals_checked': 290, 'max_absolute_error': max_error}}
    (ROOT / 'data/slide-30/slide-30.json').write_text(json.dumps(data, indent=2)+'\n')
    html = (ROOT / 'src/slide-30.html').read_text()
    assert html.count('/*__SLIDE_DATA__*/') == 1
    (ROOT / 'docs/slide-30.html').write_text(html.replace('/*__SLIDE_DATA__*/', json.dumps(data, separators=(',', ':'))))
    print(f'Built slide 30: 10 matched minima, 290 candidate totals checked; maximum error {max_error:.3g}.')


if __name__ == '__main__':
    build()
