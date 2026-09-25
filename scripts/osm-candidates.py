#!/usr/bin/env python3
"""Extract review candidates from an explicit OSM bbox or local XML extract.

Output is not canonical campus data. A maintainer must review identity, graph
connectivity, access, attribution, and ODbL obligations before promotion.
"""
import argparse
import hashlib
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path


def tags(element):
    return {tag.attrib['k']: tag.attrib['v'] for tag in element.findall('tag')}


def candidates(xml_bytes, university_id, bbox, source_url):
    root = ET.fromstring(xml_bytes)
    nodes = {}
    for element in root.findall('node'):
        nodes[element.attrib['id']] = {
            'coordinate': [float(element.attrib['lon']), float(element.attrib['lat'])],
            'tags': tags(element),
        }
    buildings, paths, entrances = [], [], []
    for element in root.findall('way'):
        way_id = element.attrib['id']
        way_tags = tags(element)
        refs = [ref.attrib['ref'] for ref in element.findall('nd')]
        if way_tags.get('building') not in (None, 'no') and len(refs) >= 4 and refs[0] == refs[-1] and all(ref in nodes for ref in refs):
            buildings.append({
                'osmId': f'way/{way_id}',
                'name': way_tags.get('name'),
                'nativeCodeCandidate': way_tags.get('ref'),
                'geometry': {'type': 'Polygon', 'coordinates': [[nodes[ref]['coordinate'] for ref in refs]]},
                'sourceId': 'openstreetmap',
            })
        if way_tags.get('highway') not in {'footway', 'pedestrian', 'path', 'living_street'}:
            continue
        if way_tags.get('access') in {'private', 'no'} or way_tags.get('indoor') == 'yes' or way_tags.get('tunnel') == 'yes' or way_tags.get('construction'):
            continue
        if len(refs) < 2 or not all(ref in nodes for ref in refs):
            continue
        paths.append({
            'osmId': f'way/{way_id}', 'nodeIds': [f'node/{ref}' for ref in refs],
            'coordinates': [nodes[ref]['coordinate'] for ref in refs],
            'sourceId': 'openstreetmap',
        })
    for node_id, node in nodes.items():
        if 'entrance' not in node['tags']:
            continue
        access = node['tags'].get('access')
        entrances.append({
            'osmId': f'node/{node_id}', 'coordinate': node['coordinate'],
            'buildingId': None, 'access': 'restricted' if access in {'private', 'no'} else 'public' if access in {'yes', 'public'} else 'unknown',
            'sourceId': 'openstreetmap',
        })
    return {
        'candidateVersion': 1, 'university': university_id, 'reviewStatus': 'unreviewed',
        'bounds': bbox,
        'sources': [{
            'id': 'openstreetmap', 'title': 'OpenStreetMap contributors', 'url': source_url,
            'retrievedAt': date.today().isoformat(), 'licenseOrTerms': 'ODbL 1.0',
            'attribution': '© OpenStreetMap contributors',
            'redistribution': 'permitted', 'transformation': 'Unreviewed candidate extraction from OSM XML',
            'sha256': hashlib.sha256(xml_bytes).hexdigest(),
        }],
        'buildings': buildings, 'entrances': entrances, 'pedestrianWays': paths,
        'reviewNotes': [
            'Names and codes are OSM candidates; reconcile against permitted official sources.',
            'Entrance building association, access, accessibility, and connectivity require review.',
            'Do not publish this candidate as a routed campus without validation and rights review.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('university')
    parser.add_argument('--bbox', required=True, help='west,south,east,north')
    parser.add_argument('--input', help='Local OSM XML extract for reproducible offline use')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9-]*', args.university):
        parser.error('invalid university ID')
    try:
        west, south, east, north = map(float, args.bbox.split(','))
    except ValueError:
        parser.error('bbox must be west,south,east,north')
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        parser.error('invalid bbox coordinates')
    if (east - west) * (north - south) > 0.05:
        parser.error('bbox is too large for a campus candidate extract')
    bbox = [west, south, east, north]
    source_url = f'https://api.openstreetmap.org/api/0.6/map?bbox={args.bbox}'
    if args.input:
        xml_bytes = Path(args.input).read_bytes()
        source_url = f'local extract: {Path(args.input).name}'
    else:
        request = urllib.request.Request(source_url, headers={'User-Agent': 'Gapwise-Data/1.0 (contact: info@gapwise.ca)'})
        with urllib.request.urlopen(request, timeout=45) as response:
            xml_bytes = response.read(25_000_001)
        if len(xml_bytes) > 25_000_000:
            parser.error('OSM extract exceeds the 25 MB candidate limit')
    result = candidates(xml_bytes, args.university, bbox, source_url)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(f'Wrote {output}: {len(result["buildings"])} building candidates, {len(result["pedestrianWays"])} pedestrian ways, {len(result["entrances"])} tagged entrances. Human review required.')


if __name__ == '__main__':
    main()
