#!/usr/bin/env python3
"""Build the linked scenario minima from slide 25's frozen manuscript draws."""

import hashlib
import json
import math
import statistics
from bisect import bisect_right
from pathlib import Path

from build_slide_25 import protection, week_index

ROOT = Path(__file__).resolve().parents[1]


def curve_at(points, time):
    if time < points[0][0] or time > points[-1][0]:
        return 0.0
    index = min(len(points)-2, max(0, bisect_right([p[0] for p in points], time)-1))
    a, b = points[index:index+2]
    return a[1]+(b[1]-a[1])*(time-a[0])/(b[0]-a[0])


def overlap_area(a, b, shift):
    b = [[time+shift, value] for time, value in b]
    left, right = max(a[0][0], b[0][0]), min(a[-1][0], b[-1][0])
    if left >= right:
        return 0.0
    knots = sorted({left, right, *[t for t, _ in a if left < t < right],
                    *[t for t, _ in b if left < t < right]})
    av, bv = [curve_at(a, t) for t in knots], [curve_at(b, t) for t in knots]
    area = 0.0
    for k in range(len(knots)-1):
        width = knots[k+1]-knots[k]
        f0, f1, g0, g1 = av[k], av[k+1], bv[k], bv[k+1]
        d0, d1 = f0-g0, f1-g1
        if d0*d1 < 0:
            fraction = d0/(d0-d1)
            cross = f0+fraction*(f1-f0)
            area += width*(fraction*(min(f0, g0)+cross)
                           +(1-fraction)*(cross+min(f1, g1)))/2
        else:
            area += width*(min(f0, g0)+min(f1, g1))/2
    return area


def align_seasons(scenarios):
    curves = []
    for row in scenarios:
        points = row['burden_points']
        area = math.fsum(value for _, value in points)
        curve = [[points[0][0]-.5, points[0][1]/area]]
        curve += [[t, value/area] for t, value in points]
        curve += [[points[-1][0]+.5, points[-1][1]/area]]
        assert abs(overlap_area(curve, curve, 0)-1) < 1e-12
        curves.append(curve)
    # Select the most representative profile using epidemic curves only.
    fits = [[(1.0, 0.0) for _ in curves] for _ in curves]
    for i in range(len(curves)):
        for j in range(i+1, len(curves)):
            score, shift = max(((overlap_area(curves[i], curves[j], k/4), k/4)
                                for k in range(-80, 81)), key=lambda p: (p[0], -abs(p[1])))
            assert abs(shift) < 20
            fits[i][j], fits[j][i] = (score, shift), (score, -shift)
    reference = max(range(len(curves)), key=lambda i: sum(row[0] for row in fits[i]))
    shifts = [row[1] for row in fits[reference]]
    shifted = [[[t+shift, v] for t, v in curve] for curve, shift in zip(curves, shifts)]
    left, right = max(c[0][0] for c in shifted), min(c[-1][0] for c in shifted)
    mean = [[k/4, statistics.mean(curve_at(c, k/4) for c in shifted)]
            for k in range(math.ceil(left*4), math.floor(right*4)+1)]
    peak = max(mean, key=lambda p: p[1])[0]
    mean = [[t-peak, value] for t, value in mean]
    before = [s['dose_time']-peak for s in scenarios]
    after = [date+shift for date, shift in zip(before, shifts)]

    def summary(values):
        q1, _, q3 = statistics.quantiles(values, n=4, method='inclusive')
        return {'median': statistics.median(values), 'mean': statistics.mean(values),
                'sd': statistics.stdev(values), 'q1': q1, 'q3': q3,
                'iqr': q3-q1, 'range': max(values)-min(values)}

    profiles = [{'draw': row['draw'], 'points': [[t-peak, v] for t, v in curve],
                 'shift': shift, 'optimal_time_before': date, 'optimal_time_after': date+shift,
                 'optimal_height': curve_at(curve, row['dose_time'])}
                for row, curve, shift, date in zip(scenarios, curves, shifts, before)]
    all_times = [t+offset for profile in profiles for t, _ in profile['points']
                 for offset in (0, profile['shift'])]
    median = statistics.median(after)
    assert mean[0][0] <= median <= mean[-1][0]
    return {'method': 'Maximum pairwise shared area after normalizing each seasonal AUC to one; representative-profile alignment',
            'n_scenarios': len(curves), 'reference_draw': scenarios[reference]['draw'],
            'shift_grid_weeks': .25, 'search_limit_weeks': 20,
            'mean_peak_before_recentering': peak, 'mean_common_window': [left-peak, right-peak],
            'profiles': profiles, 'mean_points': mean,
            'before': summary(before), 'after': summary(after),
            'median_point': [median, curve_at(mean, median)],
            'overlap_before': statistics.mean(overlap_area(curves[reference], c, 0) for c in curves),
            'overlap_after': statistics.mean(row[0] for row in fits[reference]),
            'x_min': math.floor(min(all_times)/4)*4, 'x_max': math.ceil(max(all_times)/4)*4,
            'y_max': math.ceil(max(v for c in curves for _, v in c)*100)/100}


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
            'alignment': align_seasons(scenarios),
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
