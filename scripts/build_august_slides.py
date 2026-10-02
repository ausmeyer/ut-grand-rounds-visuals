#!/usr/bin/env python3
"""Embed the frozen August-baseline results in standalone slides 30 and 31."""
import inspect
import json
import math

from analyze_august_baseline import FOLDER, ROOT, baseline, read_gzip, save, sha, week_time
from build_slide_25 import protection
from build_slide_30 import align_seasons


def training_visuals(design, fit):
    assert fit['training_draws_sha256'] == sha(FOLDER / 'training-draws.json.gz')
    data = read_gzip(FOLDER / 'training-draws.json.gz')
    scenarios = []
    for row in data['scenarios'][:design['display_n']]:
        params = row['parameters']
        candidates = [week_time(w, row['max_week']) for w in data['candidate_weeks']]
        best = max(range(len(candidates)), key=row['utility'].__getitem__)
        best_week = data['candidate_weeks'][best]
        dose_time = candidates[best]
        regret = [row['utility'][best]-value for value in row['utility']]
        protection_points = [[-.5, 0]]
        for i in range(159):
            t = i/4
            if t == dose_time+params['immune_lag_weeks']:
                protection_points.append([t, 0])
            protection_points.append([t, protection(t-dose_time, params)])
        assert sum(value < 1e-12 for value in regret) == 1
        assert all(0 <= p <= .8 for _, p in protection_points)
        scenarios.append({'draw': row['draw'], 'season': row['season'], 'max_week': row['max_week'],
                          'baseline': baseline(row, design),
                          'burden_points': [[week_time(w, row['max_week']), b]
                                            for w, b in zip(row['weeks'], row['burden']) if w >= 36 or w <= 22],
                          'protection_points': protection_points, 'decision_points': list(map(list, zip(candidates, regret))),
                          'best_index': best, 'best_week': best_week, 'dose_time': dose_time,
                          'epidemic_at_dose': row['burden'][row['weeks'].index(best_week)],
                          'protection_at_dose': 0, 'immune_lag_weeks': params['immune_lag_weeks']})
    import hashlib
    alignment_key = hashlib.sha256((json.dumps(scenarios, sort_keys=True)+inspect.getsource(align_seasons)).encode()).hexdigest()
    cached = FOLDER / 'alignment.json'
    if cached.exists() and json.loads(cached.read_text())['input_sha256'] == alignment_key:
        alignment = json.loads(cached.read_text())['alignment']
    else:
        alignment = align_seasons(scenarios)
        save('alignment.json', {'input_sha256': alignment_key, 'alignment': alignment})
    return scenarios, alignment


def build(slide=None):
    design = json.loads((FOLDER / 'design.json').read_text())
    fit = json.loads((FOLDER / 'threshold-fit.json').read_text())
    assert fit['design_sha256'] == sha(FOLDER / 'design.json')
    results = {mode: read_gzip(FOLDER / f'{mode}-results.json.gz') for mode in ['early', 'expanded']}
    for mode, result in results.items():
        assert result['draws_sha256'] == sha(FOLDER / f'{mode}-draws.json.gz') and result['fit'] == fit
    scenarios, alignment = training_visuals(design, fit)
    later = results['expanded']
    later['evaluation_n'] = len(later['scenarios'])
    later['scenarios'] = later['scenarios'][:design['display_n']]
    later['display_selection'] = 'First 50 seeded pairs; summaries use all 5,000.'
    later['y_max'] = math.ceil(max(v for r in later['scenarios'] for _, v in r['burden_points']))
    slide30 = {'slide': 30, 'design_sha256': fit['design_sha256'], 'threshold_fit_sha256': sha(FOLDER / 'threshold-fit.json'),
               'n_draws': design['n_draws'], 'scenarios': scenarios, 'alignment': alignment, 'threshold_example': later,
               'burden_y_max': math.ceil(max(v for s in scenarios for _, v in s['burden_points'])*100)/100,
               'protection_y_max': .8,
               'regret_y_max': math.ceil(max(v for s in scenarios for _, v in s['decision_points'])*10)/10,
               'validation': fit['validation']}
    state_results = read_gzip(FOLDER / 'states-results.json.gz')
    assert state_results['threshold_fit_sha256'] == sha(FOLDER / 'threshold-fit.json')
    assert state_results['state_draws_sha256'] == sha(FOLDER / 'states-draws.json.gz')
    locations = [{'name': name, 'scenarios': state_results['states'][name]['scenarios'][:design['display_n']],
                  'summary': state_results['states'][name]['summary']} for name in design['states']]
    national = {'name': 'United States', 'scenarios': results['early']['scenarios'][:design['display_n']],
                'summary': results['early']['summary']}
    slide31 = {'slide': 31, 'season': '2022/23', 'evaluation_n': design['n_draws'], 'display_n': design['display_n'],
               'fit': fit, 'national': national, 'states': locations,
               'national_y_max': max(alignment['y_max'], later['y_max'],
                                     math.ceil(max(v for r in national['scenarios'] for _, v in r['burden_points']))),
               'states_y_max': math.ceil(max(v for loc in locations for r in loc['scenarios'] for _, v in r['burden_points'])),
               'validation': {'national': results['early']['validation'],
                              'states': {name: state_results['states'][name]['validation'] for name in design['states']}}}
    for number, payload in [(30, slide30), (31, slide31)]:
        if slide is not None and number != slide:
            continue
        save(f'slide-{number}.json', payload)
        source = (ROOT / f'src/slide-{number}.html').read_text()
        assert source.count('/*__SLIDE_DATA__*/') == 1
        (ROOT / f'docs/slide-{number}.html').write_text(source.replace('/*__SLIDE_DATA__*/', json.dumps(payload, separators=(',', ':'))))
        print(f'Built slide {number}: {fit["threshold_multiplier"]}x August baseline; first 50 pairs plotted, all 5,000 summarized.')


if __name__ == '__main__':
    build()
