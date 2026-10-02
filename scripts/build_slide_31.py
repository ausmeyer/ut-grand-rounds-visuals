#!/usr/bin/env python3
"""Build the early-season national/state comparison from frozen paired draws."""
import gzip
import hashlib
import json
import math
import statistics
from pathlib import Path

from build_slide_25 import protection, week_index
from build_slide_30_threshold import summary

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'data/slide-31'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_gzip(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def build():
    config = json.loads((FOLDER / 'design.json').read_text())
    for name, sha in config['source_pins'].items():
        assert digest(ROOT / name) == sha, name
    base = ROOT / 'data/slide-30/threshold-example'
    fit = json.loads((base / 'threshold-fit.json').read_text())
    national = read_gzip(base / 'early-results.json.gz')
    pairs = read_gzip(base / 'early-draws.json.gz')['scenarios']
    source = read_gzip(FOLDER / 'states-draws.json.gz')
    assert source['design_sha256'] == digest(FOLDER / 'design.json')
    assert source['n_draws'] == len(pairs) == config['evaluation_n_per_location'] == 5000
    assert source['draw_ids'] == [r['draw'] for r in pairs] == list(range(1, 5001))
    assert list(source['states']) == config['states']
    assert fit['threshold_multiplier'] == 1.7 and fit['fixed_week'] == 47
    candidates = source['candidate_weeks']
    locations, full_results = [], {}
    max_error = 0
    for name in config['states']:
        state = source['states'][name]
        weeks = state['weeks']
        times = [week_index(w, state['max_week']) for w in weeks]
        candidate_times = [week_index(w, state['max_week']) for w in candidates]
        positions = [weeks.index(w) for w in candidates]
        baseline_positions = [weeks.index(w) for w in [36, 37, 38, 39]]
        assert len(state['burden']) == len(state['utility']) == len(pairs)
        rows = []
        for pair, burden, utility in zip(pairs, state['burden'], state['utility']):
            assert len(burden) == len(weeks) and all(b > 0 for b in burden)
            assert len(utility) == len(candidates) and max(utility) > 0
            for date, saved in zip(candidate_times, utility):
                calculated = math.fsum(b * protection(t-date, pair['parameters']) for b, t in zip(burden, times))
                max_error = max(max_error, abs(calculated-saved))
            baseline = statistics.mean(burden[i] for i in baseline_positions)
            opt = [i for i, u in enumerate(utility) if abs(u-max(utility)) < 1e-12]
            trigger = next((i for i, pos in enumerate(positions)
                            if candidate_times[i] > 3 and burden[pos] >= fit['threshold_multiplier']*baseline), None)
            row = {'draw': pair['draw'], 'season': config['season'], 'baseline': baseline,
                   'burden_points': [[t, b/baseline] for t, b in zip(times, burden)],
                   'optimal_weeks': [candidates[i] for i in opt],
                   'optimal_times': [candidate_times[i] for i in opt],
                   'optimal_heights': [burden[positions[i]]/baseline for i in opt],
                   'optimal_utility': max(utility)}
            for policy, index in [('fixed', fit['fixed_index']), ('threshold', trigger)]:
                row[f'{policy}_week'] = candidates[index] if index is not None else None
                row[f'{policy}_time'] = candidate_times[index] if index is not None else None
                row[f'{policy}_height'] = burden[positions[index]]/baseline if index is not None else None
                row[f'{policy}_utility'] = utility[index] if index is not None else 0
                row[f'{policy}_timing_error'] = min((candidate_times[index]-candidate_times[o] for o in opt), key=abs) if index is not None else None
                row[f'{policy}_relative_loss'] = (max(utility)-row[f'{policy}_utility'])/max(utility)
                assert -1e-12 <= row[f'{policy}_relative_loss'] <= 1
            rows.append(row)
        metrics = {policy: summary(rows, policy) for policy in ['fixed', 'threshold']}
        metrics['threshold_better_draws'] = sum(r['threshold_utility'] > r['fixed_utility']+1e-12 for r in rows)
        full_results[name] = {'scenarios': rows, 'summary': metrics}
        locations.append({'name': name, 'scenarios': rows[:config['display_n_per_location']], 'summary': metrics})
        print(name, json.dumps(metrics), flush=True)
    assert max_error < 1e-12
    validation = {'candidate_utilities_checked': len(pairs)*len(candidates)*len(locations),
                  'max_absolute_error': max_error, 'model_sha256': source['model_sha256'],
                  'state_draws_sha256': digest(FOLDER / 'states-draws.json.gz')}
    full = {'design_sha256': digest(FOLDER / 'design.json'), 'states': full_results, 'validation': validation}
    (FOLDER / 'states-results.json.gz').write_bytes(gzip.compress(json.dumps(full, separators=(',', ':')).encode(), mtime=0))
    (FOLDER / 'states-summary.json').write_text(json.dumps({'states': {k: v['summary'] for k, v in full_results.items()}, 'validation': validation}, indent=2)+'\n')
    national_view = {'name': 'United States', 'scenarios': national['scenarios'][:50], 'summary': national['summary']}
    previous = json.loads((ROOT / 'data/slide-30/slide-30.json').read_text())
    data = {'slide': 31, 'season': config['season'], 'evaluation_n': len(pairs), 'display_n': 50,
            'fit': {'threshold_multiplier': fit['threshold_multiplier'], 'fixed_week': fit['fixed_week']},
            'national': national_view, 'states': locations,
            'national_y_max': max(previous['alignment']['y_max'], math.ceil(max(v for r in national_view['scenarios'] for _, v in r['burden_points']))),
            'states_y_max': math.ceil(max(v for loc in locations for r in loc['scenarios'] for _, v in r['burden_points'])),
            'validation': validation}
    (FOLDER / 'slide-31.json').write_text(json.dumps(data, indent=2)+'\n')
    source_html = (ROOT / 'src/slide-31.html').read_text()
    assert source_html.count('/*__SLIDE_DATA__*/') == 1
    (ROOT / 'docs/slide-31.html').write_text(source_html.replace('/*__SLIDE_DATA__*/', json.dumps(data, separators=(',', ':'))))
    print(f'Built slide 31: {len(locations)} states, 5000 pairs each, 50 shown; maximum utility error {max_error:.3g}.')


if __name__ == '__main__':
    build()
