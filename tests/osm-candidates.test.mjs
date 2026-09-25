import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';

test('OSM candidate extraction keeps access unknown and never invents doors or graph links', () => {
  const directory = mkdtempSync(join(tmpdir(), 'gapwise-osm-'));
  try {
    const input = join(directory, 'source.osm');
    const output = join(directory, 'candidate.json');
    writeFileSync(input, `<osm version="0.6">
      <node id="1" lon="-79.38" lat="43.66"><tag k="entrance" v="yes"/></node>
      <node id="2" lon="-79.379" lat="43.66"/>
      <node id="3" lon="-79.379" lat="43.661"/>
      <node id="4" lon="-79.38" lat="43.661"/>
      <way id="10"><nd ref="1"/><nd ref="2"/><nd ref="3"/><nd ref="4"/><nd ref="1"/><tag k="building" v="yes"/><tag k="name" v="Sample Hall"/></way>
      <way id="11"><nd ref="1"/><nd ref="2"/><tag k="highway" v="footway"/></way>
      <way id="12"><nd ref="3"/><nd ref="4"/><tag k="highway" v="steps"/></way>
    </osm>`);
    const result = spawnSync('python3', ['scripts/osm-candidates.py', 'example', '--bbox=-79.39,43.65,-79.37,43.67', '--input', input, '--output', output], { encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    const candidate = JSON.parse(readFileSync(output));
    assert.equal(candidate.reviewStatus, 'unreviewed');
    assert.equal(candidate.buildings.length, 1);
    assert.equal(candidate.entrances.length, 1);
    assert.equal(candidate.entrances[0].buildingId, null);
    assert.equal(candidate.entrances[0].access, 'unknown');
    assert.deepEqual(candidate.pedestrianWays.map((way) => way.osmId), ['way/11']);
    assert.match(candidate.sources[0].attribution, /OpenStreetMap contributors/);
  } finally { rmSync(directory, { recursive: true, force: true }); }
});
