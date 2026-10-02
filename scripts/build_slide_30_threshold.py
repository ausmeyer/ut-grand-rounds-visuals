#!/usr/bin/env python3
"""Freeze a pre-pandemic activity rule, then evaluate it on 50 later pairs."""

import gzip
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

from build_slide_25 import protection, week_index

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'data/slide-30/threshold-example'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_draws(mode):
    data = json.loads(gzip.decompress((FOLDER / f'{mode}-draws.json.gz').read_bytes()))
    design_path = FOLDER / 'design.json'
    design = json.loads(design_path.read_text())
    if mode in ['expanded', 'early']:
        design_path = FOLDER / 'extended-evaluation.json'
        design.update(json.loads(design_path.read_text()))
        assert design['threshold_fit_sha256'] == sha(FOLDER / 'threshold-fit.json')
    if mode == 'early':
        assert data['early_model_manifest_sha256'] == sha(FOLDER / 'early-model-manifest.json')
    assert data['design_sha256'] == sha(design_path)
    assert data['n_draws'] == len(data['scenarios']) == design[f'{mode}_draws']
    error = 0
    for row in data['scenarios']:
        assert int(row['season'][:4]) in design[f'{mode}_season_start_years']
        assert int(row['parameters']['ve_source_season'][:4]) in design['ve_source_season_start_years']
        assert row['weeks'][-1] == 22 and all(b > 0 for b in row['burden'])
        times = [week_index(w, row['max_week']) for w in row['weeks']]
        for week, saved in zip(data['candidate_weeks'], row['utility']):
            date = week_index(week, row['max_week'])
            calculated = math.fsum(b * protection(t-date, row['parameters'])
                                  for t, b in zip(times, row['burden']))
            error = max(error, abs(calculated-saved))
    assert error < 1e-12
    data['validation'] = {'candidate_totals_checked': len(data['scenarios'])*len(data['candidate_weeks']),
                          'max_absolute_error': error}
    return data, design


def baseline(row, design):
    return statistics.mean(row['burden'][row['weeks'].index(w)] for w in design['baseline_weeks'])


def optimal_indices(row):
    best = max(row['utility'])
    return [i for i, value in enumerate(row['utility']) if abs(value-best) < 1e-12]


def freeze_fit():
    data, design = read_draws('training')
    candidates = data['candidate_weeks']
    ratios = []
    for row in data['scenarios']:
        if max(row['utility']) > 1e-12:
            ratios.append(statistics.median(row['burden'][row['weeks'].index(candidates[i])]
                          / baseline(row, design) for i in optimal_indices(row)))
    median = statistics.median(ratios)
    mean_utility = [statistics.mean(row['utility'][i] for row in data['scenarios'])
                    for i in range(len(candidates))]
    fixed_index = max(range(len(candidates)), key=mean_utility.__getitem__)
    fit = {'training_draws_sha256': sha(FOLDER / 'training-draws.json.gz'),
           'design_sha256': sha(FOLDER / 'design.json'),
           'analysis_plan_sha256': sha(FOLDER / 'analysis-plan.json'),
           'training_n': len(data['scenarios']), 'informative_n': len(ratios),
           'optimal_activity_ratio_median': median,
           'threshold_multiplier': math.floor(median*10+.5)/10,
           'fixed_week': candidates[fixed_index], 'fixed_index': fixed_index,
           'candidate_weeks': candidates, 'training_mean_utility': mean_utility,
           'validation': data['validation']}
    path = FOLDER / 'threshold-fit.json'
    if path.exists():
        assert json.loads(path.read_text()) == fit, 'Frozen fit differs; do not tune against evaluation.'
    else:
        assert not (FOLDER / 'evaluation-draws.json.gz').exists()
        path.write_text(json.dumps(fit, indent=2)+'\n')
    return fit


def summary(rows, policy):
    timing = [r[f'{policy}_timing_error'] for r in rows if r[f'{policy}_timing_error'] is not None]
    loss = [r[f'{policy}_relative_loss'] for r in rows if r[f'{policy}_relative_loss'] is not None]
    utility = sum(r[f'{policy}_utility'] for r in rows)
    return {'n': len(rows), 'n_timing': len(timing), 'non_crossings': len(rows)-len(timing),
            'median_signed_weeks': statistics.median(timing),
            'median_absolute_weeks': statistics.median(abs(x) for x in timing),
            'mean_absolute_weeks': statistics.mean(abs(x) for x in timing),
            'within_2_weeks': sum(abs(x) <= 2 for x in timing),
            'median_relative_loss': statistics.median(loss),
            'mean_relative_loss': statistics.mean(loss),
            'total_utility': utility,
            'pooled_relative_loss': 1-utility/sum(r['optimal_utility'] for r in rows)}


def build_threshold_example(mode="evaluation"):
    fit = json.loads((FOLDER / 'threshold-fit.json').read_text())
    assert fit['design_sha256'] == sha(FOLDER / 'design.json')
    assert fit['training_draws_sha256'] == sha(FOLDER / 'training-draws.json.gz')
    assert fit['analysis_plan_sha256'] == sha(FOLDER / 'analysis-plan.json')
    data, design = read_draws(mode)
    assert data['threshold_fit_sha256'] == sha(FOLDER / 'threshold-fit.json')
    candidates = data['candidate_weeks']
    rows = []
    for row in data['scenarios']:
        base = baseline(row, design)
        times = [week_index(w, row['max_week']) for w in candidates]
        opt = optimal_indices(row)
        first = next((i for i, w in enumerate(candidates)
                      if times[i] > max(week_index(b, row['max_week']) for b in design['baseline_weeks'])
                      and row['burden'][row['weeks'].index(w)] >= fit['threshold_multiplier']*base), None)
        result = {'draw': row['draw'], 'season': row['season'], 'baseline': base,
                  'burden_points': [[week_index(w, row['max_week']), b/base]
                                    for w, b in zip(row['weeks'], row['burden'])],
                  'optimal_weeks': [candidates[i] for i in opt],
                  'optimal_times': [times[i] for i in opt],
                  'optimal_heights': [row['burden'][row['weeks'].index(candidates[i])]/base for i in opt],
                  'optimal_utility': max(row['utility'])}
        for policy, index in [('threshold', first), ('fixed', fit['fixed_index'])]:
            result[f'{policy}_week'] = candidates[index] if index is not None else None
            result[f'{policy}_time'] = times[index] if index is not None else None
            result[f'{policy}_height'] = row['burden'][row['weeks'].index(candidates[index])]/base if index is not None else None
            result[f'{policy}_utility'] = row['utility'][index] if index is not None else 0
            result[f'{policy}_timing_error'] = min((times[index]-times[i] for i in opt), key=abs) if index is not None else None
            result[f'{policy}_relative_loss'] = (max(row['utility'])-result[f'{policy}_utility'])/max(row['utility']) if max(row['utility']) > 1e-12 else None
            assert result[f'{policy}_relative_loss'] is None or result[f'{policy}_relative_loss'] >= -1e-12
        rows.append(result)
    result = {'fit': fit, 'scenarios': rows, 'season_counts': data['season_counts'],
              'summary': {policy: summary(rows, policy) for policy in ['threshold', 'fixed']},
              'by_season': {s: {p: summary([r for r in rows if r['season'] == s], p)
                                for p in ['threshold', 'fixed']} for s in data['season_counts']},
              'y_max': math.ceil(max(v for r in rows for _, v in r['burden_points'])),
              'validation': data['validation']}
    if mode in ['expanded', 'early']:
        (FOLDER / f'{mode}-results.json.gz').write_bytes(gzip.compress(json.dumps(result, separators=(',', ':')).encode(), mtime=0))
        (FOLDER / f'{mode}-summary.json').write_text(json.dumps({k:v for k,v in result.items() if k != 'scenarios'}, indent=2)+'\n')
    else:
        (FOLDER / f'{mode}-results.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'fit':
        print(json.dumps(freeze_fit(), indent=2))
    else:
        print(json.dumps(build_threshold_example(sys.argv[1] if len(sys.argv) == 2 else 'evaluation')['summary'], indent=2))
