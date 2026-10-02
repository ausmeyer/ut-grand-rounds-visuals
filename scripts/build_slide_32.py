#!/usr/bin/env python3
"""Describe timing and weekly slopes in the existing pre-pandemic paired draws."""
import gzip
import hashlib
import json
import math
import statistics
from pathlib import Path

from build_slide_30 import curve_at

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/august-baseline'
PINS = {
    'training-draws.json.gz': '91a5921c4d8cfec5f27cb395953395c097375d38ec949e74a1e48107f6a25b03',
    'alignment.json': 'b1c27a8d8860998ac52d4fd0fbfca1034ad7bd2a93867a4a49b2be5797a5427e',
}


def week_time(week, max_week):
    return week-36 if week >= 32 else max_week-36+week


def interval(values):
    q1, _, q3 = statistics.quantiles(values, n=4, method='inclusive')
    return {'median': statistics.median(values), 'q1': q1, 'q3': q3}


def describe(row, candidates):
    times = [week_time(w, row['max_week']) for w in row['weeks']]
    values = [100*v for v in row['burden']]
    assert all(b-a == 1 for a, b in zip(times, times[1:]))
    # Centered two-week secant, at each interior week. No extra smoothing.
    slope = [[times[i], (values[i+1]-values[i-1])/2]
             for i in range(1, len(times)-1) if times[i] >= 0]
    best = max(range(len(candidates)), key=row['utility'].__getitem__)
    assert sum(u == row['utility'][best] for u in row['utility']) == 1
    dose = week_time(candidates[best], row['max_week'])
    onset = dose+row['parameters']['immune_lag_weeks']
    fastest = max(slope, key=lambda point: point[1])
    assert fastest[1] > 0 and slope[0][0] <= dose <= onset <= slope[-1][0]
    # An additive constant cancels, without estimating its value.
    assert all(abs((values[i+1]+10-values[i-1]-10)/2-(values[i+1]-values[i-1])/2) < 1e-12
               for i in range(1, len(times)-1))
    return {'draw': row['draw'], 'season': row['season'], 'max_week': row['max_week'],
            'activity': [[t, v] for t, v in zip(times, values) if t >= 0],
            'slope': slope, 'dose_week': candidates[best], 'dose': dose, 'onset': onset,
            'immune_lag_weeks': row['parameters']['immune_lag_weeks'],
            'fastest': fastest[0], 'dose_offset': dose-fastest[0], 'onset_offset': onset-fastest[0]}


def build():
    for name, digest in PINS.items():
        assert hashlib.sha256((INPUT/name).read_bytes()).hexdigest() == digest, name
    raw = json.loads(gzip.decompress((INPUT/'training-draws.json.gz').read_bytes()))
    alignment = json.loads((INPUT/'alignment.json').read_text())['alignment']
    rows = [describe(row, raw['candidate_weeks']) for row in raw['scenarios']]
    shown = rows[:50]
    assert len(rows) == 5000 and len(alignment['profiles']) == len(shown)
    origin = min(p['shift'] for p in alignment['profiles'])
    for row, profile in zip(shown, alignment['profiles']):
        assert row['draw'] == profile['draw']
        # Reuse horizontal shifts only. No August baseline or scaled heights.
        row['shift'] = profile['shift']-origin
        assert abs(row['dose']+profile['shift']-alignment['mean_peak_before_recentering']
                   -profile['optimal_time_after']) < 1e-10
    shifted_activity = [[[t+r['shift'], v] for t, v in r['activity']] for r in shown]
    shifted_slope = [[[t+r['shift'], v] for t, v in r['slope']] for r in shown]
    left = max(c[0][0] for c in shifted_activity)
    right = min(c[-1][0] for c in shifted_activity)
    activity = [[k/4, statistics.mean(curve_at(c, k/4) for c in shifted_activity)]
                for k in range(math.ceil(left*4), math.floor(right*4)+1)]
    slope = [[k/4, statistics.mean(curve_at(c, k/4) for c in shifted_slope)]
             for k in range(math.ceil((left+1)*4), math.floor((right-1)*4)+1)]
    # Differencing and averaging commute on the common interior support.
    assert max(abs(v-(curve_at(activity, t+1)-curve_at(activity, t-1))/2)
               for t, v in slope) < 1e-12
    mean = {'activity': activity, 'slope': slope,
            'dose': statistics.median(r['dose']+r['shift'] for r in shown),
            'onset': statistics.median(r['onset']+r['shift'] for r in shown),
            'fastest': max(slope, key=lambda p: p[1])[0]}
    summaries = []
    for season in sorted({r['season'] for r in rows}):
        selected = [r for r in rows if r['season'] == season]
        summaries.append({'season': season, 'n': len(selected),
                          'display_n': sum(r['season'] == season for r in shown),
                          'dose': interval([r['dose_offset'] for r in selected]),
                          'onset': interval([r['onset_offset'] for r in selected])})
    payload = {
        'slide': 32, 'sources_sha256': PINS, 'n': len(rows), 'display_n': len(shown),
        'selection': 'First 50 saved paired draws, in original order; no new draws or fit.',
        'derivative': '(ILI[t+1] - ILI[t-1]) / 2; percentage points per week; weekly grid',
        'reference': 'Each draw\u2019s maximum positive centered slope from week 36 through week 21; earliest exact tie.',
        'alignment': 'Existing AUC-overlap horizontal shifts only; earliest displayed start is aligned week zero.',
        'scope': 'Retrospective smoothed latent ILI curves. Conditional draws from eight seasons, not 5,000 independent seasons. No prospective trigger is fitted or tested.',
        'scenarios': shown, 'mean': mean, 'seasons': summaries,
        'pooled_onset': interval([r['onset_offset'] for r in rows]),
        'pooled_onset_within_two_weeks': statistics.mean(abs(r['onset_offset']) <= 2 for r in rows),
        'bounds': {'aligned_x': [0, math.ceil(max(c[-1][0] for c in shifted_activity)/2)*2],
                   'activity_max': math.ceil(max(v for c in shifted_activity for _, v in c)),
                   'slope_max': math.ceil(max(abs(v) for c in shifted_slope for _, v in c)*5)/5,
                   'mean_activity_max': math.ceil(max(v for _, v in activity)),
                   'mean_slope_max': math.ceil(max(abs(v) for _, v in slope)*10)/10},
    }
    folder = ROOT/'data/slide-32'
    folder.mkdir(exist_ok=True)
    (folder/'diagnostic.json').write_text(json.dumps(payload, indent=2)+'\n')
    source = (ROOT/'src/slide-32.html').read_text()
    assert source.count('/*__SLIDE_DATA__*/') == 1
    (ROOT/'docs/slide-32.html').write_text(source.replace('/*__SLIDE_DATA__*/', json.dumps(payload, separators=(',', ':'))))
    print(f'Built slide 32: {len(shown)} existing pairs displayed; {len(rows)} pairs across {len(summaries)} seasons summarized.')
    print(json.dumps({'aligned_mean': {k: mean[k] for k in ['dose', 'onset', 'fastest']},
                      'pooled_onset': payload['pooled_onset'], 'seasons': summaries}, indent=2))


if __name__ == '__main__':
    build()
