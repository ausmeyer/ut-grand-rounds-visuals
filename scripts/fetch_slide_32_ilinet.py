#!/usr/bin/env python3
"""Snapshot current CDC ILINet data for the US and the four slide 31 states."""
import datetime as dt
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'data/slide-32/current-ilinet'
BASE = 'https://gis.cdc.gov/flu2'
STATES = ['Texas', 'California', 'Minnesota', 'New York', 'New York City']


def download(url, path, request=None):
    command = ['/usr/bin/curl', '--fail', '--silent', '--show-error', '--location',
               '--max-time', '120', '-H', 'Referer: https://gis.cdc.gov/fluview/',
               '-H', 'Origin: https://gis.cdc.gov', '--output', str(path)]
    if request is not None:
        command += ['-H', 'Content-Type: application/json', '--data-binary', '@'+str(request)]
    subprocess.run(command+[url], check=True)


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    metadata_url = BASE+'/GetPhase02InitApp?appVersion=Public'
    download(metadata_url, OUT/'metadata.json')
    metadata = json.loads((OUT/'metadata.json').read_text())
    seasons = sorted((s for s in metadata['seasons'] if s['enabled']), key=lambda s:s['seasonid'])[-2:]
    state_ids = {s['statename']:s['stateid'] for s in metadata['states'] if s['statename'] in STATES}
    assert set(state_ids) == set(STATES)
    for level, region_id in [('national', 3), ('states', 5)]:
        subregions = [{'ID':0, 'Name':''}] if level == 'national' else [
            {'ID':state_ids[name], 'Name':str(state_ids[name])} for name in STATES]
        request = {'AppVersion':'Public', 'DatasourceDT':[{'ID':1, 'Name':'ILINet'}],
                   'RegionTypeId':region_id, 'SubRegionsDT':subregions,
                   'SeasonsDT':[{'ID':s['seasonid'], 'Name':str(s['seasonid'])} for s in seasons]}
        request_path = OUT/f'{level}-request.json'
        save(request_path, request)
        archive = OUT/f'{level}.zip'
        download(BASE+'/PostPhase02DataDownload', archive, request_path)
        with zipfile.ZipFile(archive) as z:
            members = [n for n in z.namelist() if n.lower().endswith('.csv')]
            assert len(members) == 1
            (OUT/f'{level}.csv').write_bytes(z.read(members[0]))
    source_files = ['metadata.json', 'national-request.json', 'states-request.json',
                    'national.zip', 'states.zip', 'national.csv', 'states.csv']
    save(OUT/'provenance.json', {
        'retrieved_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'metadata_url':metadata_url, 'download_url':BASE+'/PostPhase02DataDownload',
        'source_page':'https://gis.cdc.gov/grasp/fluview/fluportaldashboard.html',
        'seasons':[s['label'] for s in seasons], 'requested_states':STATES,
        'source_sha256':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in source_files},
        'status':'CDC preliminary surveillance snapshot; later releases can revise these values.'})
    print('Saved CDC ILINet snapshot:', OUT)


if __name__ == '__main__':
    main()
