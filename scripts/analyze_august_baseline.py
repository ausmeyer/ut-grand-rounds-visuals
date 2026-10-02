#!/usr/bin/env python3
"""Calibrate on pre-pandemic pairs; evaluate the frozen August activity rule."""
import gzip
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

from build_slide_25 import protection

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'data/august-baseline'
POLICIES = ['guidance', 'fixed', 'threshold']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_gzip(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def save(name, value):
    path = FOLDER / name
    if name.endswith('.gz'):
        path.write_bytes(gzip.compress(json.dumps(value, separators=(',', ':')).encode(), mtime=0))
    else:
        path.write_text(json.dumps(value, indent=2)+'\n')


def week_time(week, max_week):
    return week-36 if week >= 32 else max_week-36+week


def baseline(row, design):
    return statistics.mean(row['burden'][row['weeks'].index(w)] for w in design['baseline_weeks'])


def optimal_indices(row):
    best = max(row['utility'])
    assert best > 1e-12
    return [i for i, value in enumerate(row['utility']) if abs(value-best) < 1e-12]


def check_utilities(rows, candidates):
    error = 0
    for row in rows:
        assert row['weeks'] == list(range(32, row['max_week']+1))+list(range(1, 23))
        assert len(row['weeks']) == len(row['burden']) and all(0 < b < 1 for b in row['burden'])
        points = [(week_time(w, row['max_week']), b) for w, b in zip(row['weeks'], row['burden'])
                  if w >= 36 or w <= 22]
        assert len(row['utility']) == len(candidates)
        for week, saved in zip(candidates, row['utility']):
            date = week_time(week, row['max_week'])
            calculated = math.fsum(b*protection(t-date, row['parameters']) for t, b in points)
            error = max(error, abs(calculated-saved))
    assert error < 1e-12, error
    return {'candidate_utilities_checked': len(rows)*len(candidates), 'max_absolute_error': error}


def read_draws(mode):
    design = json.loads((FOLDER / 'design.json').read_text())
    data = read_gzip(FOLDER / f'{mode}-draws.json.gz')
    manifest_path = FOLDER / f'{mode}-model-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    pin = design['paired_inputs'][mode]
    assert data['design_sha256'] == manifest['design_sha256'] == sha(FOLDER / 'design.json')
    assert data['model_manifest_sha256'] == sha(manifest_path)
    assert data['model_sha256'] == manifest['model_sha256']
    assert data['prior_pairs_sha256'] == pin['sha256'] == sha(ROOT / pin['path'])
    prior = read_gzip(ROOT / pin['path'])
    assert data['n_draws'] == len(data['scenarios']) == design['n_draws']
    assert data['candidate_weeks'] == design['candidate_weeks']
    for row, old in zip(data['scenarios'], prior['scenarios']):
        assert int(row['season'][:4]) in design[f'{mode}_seasons']
        assert int(row['parameters']['ve_source_season'][:4]) <= 2018
        assert row['draw'] == old['draw'] and row['season'] == old['season']
        assert abs(row['timing_shift_weeks']-old['timing_shift_weeks']) < 1e-14
        for key, value in row['parameters'].items():
            assert abs(value-old['parameters'][key]) < 1e-14 if isinstance(value, (int, float)) else value == old['parameters'][key]
    if mode != 'training':
        assert data['threshold_fit_sha256'] == sha(FOLDER / 'threshold-fit.json')
    data['validation'] = check_utilities(data['scenarios'], data['candidate_weeks'])
    return data, design


def freeze_fit():
    data, design = read_draws('training')
    candidates = data['candidate_weeks']
    ratios = [statistics.median(row['burden'][row['weeks'].index(candidates[i])]/baseline(row, design)
                               for i in optimal_indices(row)) for row in data['scenarios']]
    median = statistics.median(ratios)
    means = [statistics.mean(row['utility'][i] for row in data['scenarios']) for i in range(len(candidates))]
    fit = {'training_draws_sha256': sha(FOLDER / 'training-draws.json.gz'),
           'design_sha256': sha(FOLDER / 'design.json'), 'training_n': len(ratios),
           'optimal_activity_ratio_median': median, 'threshold_multiplier': math.floor(median*10+.5)/10,
           'baseline_weeks': design['baseline_weeks'], 'first_trigger_week': design['first_trigger_week'],
           'guidance_week': design['guidance_week'], 'fixed_week': design['fixed_week'],
           'fixed_index': candidates.index(design['fixed_week']),
           'refitted_training_optimal_fixed_week': candidates[max(range(len(candidates)), key=means.__getitem__)],
           'candidate_weeks': candidates, 'training_mean_utility': means, 'validation': data['validation']}
    path = FOLDER / 'threshold-fit.json'
    if path.exists():
        assert json.loads(path.read_text()) == fit, 'Frozen training fit changed.'
    else:
        assert not any((FOLDER / f'{mode}-draws.json.gz').exists() for mode in ['early', 'expanded'])
        save(path.name, fit)
    return fit


def summarize(rows, policy):
    timing = [r[f'{policy}_timing_error'] for r in rows if r[f'{policy}_timing_error'] is not None]
    loss = [r[f'{policy}_relative_loss'] for r in rows]
    utility = math.fsum(r[f'{policy}_utility'] for r in rows)
    return {'n': len(rows), 'n_timing': len(timing), 'non_crossings': len(rows)-len(timing),
            'median_signed_weeks': statistics.median(timing) if timing else None,
            'median_absolute_weeks': statistics.median(abs(x) for x in timing) if timing else None,
            'mean_absolute_weeks': statistics.mean(abs(x) for x in timing) if timing else None,
            'within_2_weeks': sum(abs(x) <= 2 for x in timing),
            'median_relative_loss': statistics.median(loss), 'mean_relative_loss': statistics.mean(loss),
            'total_utility': utility, 'pooled_relative_loss': 1-utility/math.fsum(r['optimal_utility'] for r in rows)}


def evaluate(rows, candidates, design, fit):
    results = []
    for row in rows:
        base = baseline(row, design)
        times = [week_time(w, row['max_week']) for w in candidates]
        positions = [row['weeks'].index(w) for w in candidates]
        opt = optimal_indices(row)
        first = next((i for i, pos in enumerate(positions)
                      if times[i] >= week_time(design['first_trigger_week'], row['max_week'])
                      and row['burden'][pos] >= fit['threshold_multiplier']*base), None)
        result = {'draw': row['draw'], 'season': row['season'], 'baseline': base,
                  'burden_points': [[week_time(w, row['max_week']), b/base]
                                    for w, b in zip(row['weeks'], row['burden']) if w >= 36 or w <= 22],
                  'optimal_weeks': [candidates[i] for i in opt], 'optimal_times': [times[i] for i in opt],
                  'optimal_heights': [row['burden'][positions[i]]/base for i in opt],
                  'optimal_utility': max(row['utility'])}
        for policy, index in [('guidance', candidates.index(fit['guidance_week'])),
                              ('fixed', fit['fixed_index']), ('threshold', first)]:
            result[f'{policy}_week'] = candidates[index] if index is not None else None
            result[f'{policy}_time'] = times[index] if index is not None else None
            result[f'{policy}_height'] = row['burden'][positions[index]]/base if index is not None else None
            result[f'{policy}_utility'] = row['utility'][index] if index is not None else 0
            result[f'{policy}_timing_error'] = min((times[index]-times[i] for i in opt), key=abs) if index is not None else None
            result[f'{policy}_relative_loss'] = 1-result[f'{policy}_utility']/result['optimal_utility']
            assert -1e-12 <= result[f'{policy}_relative_loss'] <= 1
        results.append(result)
    seasons = sorted({r['season'] for r in rows})
    return {'fit': fit, 'scenarios': results,
            'summary': {p: summarize(results, p) for p in POLICIES},
            'by_season': {s: {p: summarize([r for r in results if r['season'] == s], p) for p in POLICIES} for s in seasons},
            'season_counts': {s: sum(r['season'] == s for r in rows) for s in seasons}}


def evaluate_all():
    fit = json.loads((FOLDER / 'threshold-fit.json').read_text())
    assert fit['training_draws_sha256'] == sha(FOLDER / 'training-draws.json.gz')
    assert fit['design_sha256'] == sha(FOLDER / 'design.json')
    for mode in ['early', 'expanded']:
        data, design = read_draws(mode)
        result = evaluate(data['scenarios'], data['candidate_weeks'], design, fit)
        result['validation'] = data['validation']
        result['draws_sha256'] = sha(FOLDER / f'{mode}-draws.json.gz')
        save(f'{mode}-results.json.gz', result)
        save(f'{mode}-summary.json', {k: v for k, v in result.items() if k != 'scenarios'})
        print(mode, json.dumps(result['summary']), flush=True)
    source = read_gzip(FOLDER / 'states-draws.json.gz')
    national = read_gzip(FOLDER / 'early-draws.json.gz')
    assert source['design_sha256'] == fit['design_sha256']
    assert source['national_draws_sha256'] == sha(FOLDER / 'early-draws.json.gz')
    assert source['threshold_fit_sha256'] == sha(FOLDER / 'threshold-fit.json')
    assert source['n_draws'] == len(national['scenarios']) == design['n_draws']
    assert source['draw_ids'] == list(range(1, design['n_draws']+1))
    assert list(source['states']) == design['states']
    results = {}
    for name, state in source['states'].items():
        rows = [{**pair, 'weeks': state['weeks'], 'max_week': state['max_week'], 'burden': b, 'utility': u}
                for pair, b, u in zip(national['scenarios'], state['burden'], state['utility'])]
        assert len(rows) == design['n_draws']
        validation = check_utilities(rows, source['candidate_weeks'])
        results[name] = evaluate(rows, source['candidate_weeks'], design, fit)
        results[name]['validation'] = validation
        print(name, json.dumps(results[name]['summary']), flush=True)
    result = {'states': results, 'state_draws_sha256': sha(FOLDER / 'states-draws.json.gz'),
              'design_sha256': fit['design_sha256'], 'threshold_fit_sha256': sha(FOLDER / 'threshold-fit.json')}
    save('states-results.json.gz', result)
    save('states-summary.json', {**{k: v for k, v in result.items() if k != 'states'},
                               'states': {k: {x: y for x, y in v.items() if x != 'scenarios'} for k, v in results.items()}})


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ['fit', 'evaluate']
    if sys.argv[1] == 'fit':
        print(json.dumps(freeze_fit(), indent=2))
    else:
        evaluate_all()
