#!/usr/bin/env python3
"""Build current ILINet curves with the frozen, exploratory August threshold."""
import csv
import datetime as dt
import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT/'data/slide-32/current-ilinet'
FIT = ROOT/'data/august-baseline/threshold-fit.json'
FIT_SHA256 = '97b6e6d4c614d693c6aedf601a7ee60118b8220e9c5607caa9685dda000e2dd7'
STATES = ['Texas', 'California', 'Minnesota', 'New York']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(name):
    return list(csv.DictReader((FOLDER/name).read_text(encoding='utf-8-sig').splitlines()[1:]))


def number(value):
    return None if value in ('X', 'NA', '') else float(value)


def build():
    provenance = json.loads((FOLDER/'provenance.json').read_text())
    for name, digest in provenance['source_sha256'].items():
        assert sha(FOLDER/name) == digest, name
    assert sha(FIT) == FIT_SHA256
    fit = json.loads(FIT.read_text())
    assert fit['threshold_multiplier'] == 2.3 and fit['baseline_weeks'] == [32,33,34,35]
    metadata = json.loads((FOLDER/'metadata.json').read_text())
    dates = {(r['year'],r['weeknumber']):r for r in metadata['mmwr']}
    national_raw, states_raw = read_csv('national.csv'), read_csv('states.csv')
    latest = max((int(r['YEAR']),int(r['WEEK'])) for r in national_raw if number(r['% WEIGHTED ILI']) is not None)
    year, latest_week = latest
    first_week = 26
    assert latest_week >= max(fit['baseline_weeks'])
    last_end = dates[latest]['weekend']
    assert dt.date.fromisoformat(last_end) <= dt.date.fromisoformat(provenance['retrieved_utc'][:10])
    first_end = dates[year, first_week]['weekend']

    def location(name, rows, column, label=None):
        selected = sorted((r for r in rows if int(r['YEAR']) == year and first_week <= int(r['WEEK']) <= latest_week), key=lambda r:int(r['WEEK']))
        assert [int(r['WEEK']) for r in selected] == list(range(first_week, latest_week+1))
        points = [{'week':int(r['WEEK']), 'week_ending':dates[year,int(r['WEEK'])]['weekend'],
                   'value':number(r[column])} for r in selected]
        baseline_points = [r for r in points if r['week'] in fit['baseline_weeks']]
        assert len(baseline_points) == 4 and all(r['value'] is not None for r in baseline_points)
        baseline = statistics.mean(r['value'] for r in baseline_points)
        threshold = fit['threshold_multiplier']*baseline
        crossing = next((r['week'] for r in points if r['week'] >= fit['first_trigger_week'] and r['value'] is not None and r['value'] >= threshold), None)
        assert baseline > 0 and all(r['value'] is None or 0 <= r['value'] <= 100 for r in points)
        return {'name':name, 'label':label or name, 'source_column':column, 'points':points,
                'baseline_percentage':baseline, 'threshold_percentage':threshold,
                'latest_percentage':points[-1]['value'], 'first_crossing_week':crossing}

    national = location('United States', national_raw, '% WEIGHTED ILI')
    states = [location(name, [r for r in states_raw if r['REGION'] == name], '%UNWEIGHTED ILI',
                       'New York (excl. NYC)' if name == 'New York' else name) for name in STATES]
    # NYC is a separate jurisdiction. Do not combine absent counts as zero.
    nyc = [r for r in states_raw if r['REGION'] == 'New York City' and int(r['YEAR']) == year and first_week <= int(r['WEEK']) <= latest_week]
    assert len(nyc) == latest_week-first_week+1 and all(number(r['%UNWEIGHTED ILI']) is None for r in nyc)
    maxima = lambda rows: max([r['threshold_percentage'] for r in rows]+[p['value'] for r in rows for p in r['points'] if p['value'] is not None])
    ticks = [{'week':w, 'label':dt.date.fromisoformat(dates[year,w]['weekend']).strftime('%b %-d')}
             for w in [first_week,30,35,latest_week]]
    payload = {'slide':32, 'year':year, 'first_week':first_week, 'latest_week':latest_week,
               'first_week_ending':first_end, 'latest_week_ending':last_end,
               'latest_label':dt.date.fromisoformat(last_end).strftime('%b %-d, %Y'),
               'retrieved_utc':provenance['retrieved_utc'], 'source_page':provenance['source_page'],
               'source_sha256':provenance['source_sha256'], 'threshold_fit_sha256':FIT_SHA256,
               'threshold_multiplier':fit['threshold_multiplier'], 'baseline_weeks':fit['baseline_weeks'],
               'first_trigger_week':fit['first_trigger_week'], 'national':national, 'states':states,
               'national_y_max':math.ceil(maxima([national])*1.12*2)/2,
               'ticks':ticks,
               'method':'Arithmetic mean of reported ILINet percentages in weeks 32–35, multiplied by the existing 2.3. National uses CDC weighted ILI; states use published unweighted ILI. No fitting, smoothing, projection, or resampling.',
               'scope':'Current surveillance illustration of an exploratory rule, not a validated vaccination recommendation. The rule was calibrated on latent curves; this overlay applies it to reported values. NYC is unavailable and excluded from the New York panel.'}
    (FOLDER/'slide.json').write_text(json.dumps(payload, indent=2)+'\n')
    source = (ROOT/'src/slide-32.html').read_text()
    assert source.count('/*__SLIDE_DATA__*/') == 1
    (ROOT/'docs/slide-32.html').write_text(source.replace('/*__SLIDE_DATA__*/', json.dumps(payload, separators=(',', ':'))))
    print(f'Built slide 32: current ILINet through {last_end}, with the frozen {fit["threshold_multiplier"]}× rule.')
    for row in [national]+states:
        print(f'{row["label"]}: latest {row["latest_percentage"]:.6f}%; baseline {row["baseline_percentage"]:.6f}%; threshold {row["threshold_percentage"]:.6f}%; first crossing {row["first_crossing_week"]}')


if __name__ == '__main__':
    build()
