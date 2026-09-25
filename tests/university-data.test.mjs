import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateCampus, validateAcademic } from '../scripts/validate-university-data.mjs';
const read = (name) => JSON.parse(readFileSync(new URL(`../universities/carleton/${name}.json`, import.meta.url)));
test('populated campus and empty academic snapshots are valid', () => {
  assert.deepEqual(validateCampus(read('campus')), []);
  assert.deepEqual(validateAcademic(read('academic')), []);
});
test('rejects an invented nearest-node edge disguised as field reviewed OSM data', () => {
  const data = read('campus');
  data.pathEdges[0].provenance = [{sourceId:'osm-carleton-2026-09',nativeId:'link/node/123',verification:'field-reviewed'}];
  assert.match(validateCampus(data).join(' '), /inferred nearest-node links are not paths/);
});
test('uses the April 2025 official codes for the buildings previously mismatched', () => {
  const byId = new Map(read('campus').buildings.map((building) => [building.id, building]));
  for (const [id, code] of Object.entries({
    'arise-building': 'AB', 'tennis-centre': 'TD', 'dundas-house': 'DH',
    'stormont-house': 'SH', 'teraanga-commons': 'TC',
  })) assert.deepEqual(byId.get(id)?.nativeCodes, [code]);
});
test('a routable entrance must have a real node and redistributable source', () => {
  const data = read('campus');
  data.entrances.push({ id:'door', buildingId:'missing', coordinate:[-75,45], pathNodeId:'missing', access:'unknown', provenance:[{sourceId:'unknown',nativeId:null,verification:'inferred'}] });
  assert.ok(validateCampus(data).length >= 3);
});
test('academic sections retain linked native identifiers', () => {
  const data = read('academic');
  data.courses.push({code:'TEST 1000',title:'Synthetic fixture',termId:'missing',sourceId:'missing',sections:[{nativeSection:'A1',nativeComponentType:'TUT',crn:null,linkedSectionIds:['A'],sourceId:'missing',meetings:[]}]});
  assert.match(validateAcademic(data).join(' '), /unknown linked section A/);
});
test('rejects an unclosed building geometry', () => {
  const data = read('campus');
  data.sources.push({id:'synthetic',title:'Test only',url:'https://example.com',retrievedAt:'2026-09-24',licenseOrTerms:'Test fixture',redistribution:'permitted',transformation:'None'});
  data.buildings.push({id:'test',name:'Synthetic building',nativeCodes:['XX'],aliases:[],geometry:{type:'Polygon',coordinates:[[[0,0],[0,1],[1,1],[1,0]]]},provenance:[{sourceId:'synthetic',nativeId:'test',verification:'inferred'}]});
  assert.match(validateCampus(data).join(' '), /invalid closed GeoJSON polygon/);
});

test('validates a complete, valid campus fixture', () => {
  const data = read('campus');
  data.sources.push({id:'src-1',title:'Carleton Map Test',url:'https://example.com/map',retrievedAt:'2026-09-24',licenseOrTerms:'Permitted',redistribution:'permitted',transformation:'Direct'});
  data.buildings.push({id:'b1',name:'Building One',nativeCodes:['BO'],aliases:['One'],geometry:{type:'Polygon',coordinates:[[[0,0],[0,1],[1,1],[1,0],[0,0]]]},provenance:[{sourceId:'src-1',nativeId:'b1',verification:'source-backed'}]});
  data.pathNodes.push({id:'n1',coordinate:[0,0],provenance:[{sourceId:'src-1',nativeId:'n1',verification:'field-reviewed'}]});
  data.pathNodes.push({id:'n2',coordinate:[1,1],provenance:[{sourceId:'src-1',nativeId:'n2',verification:'field-reviewed'}]});
  data.pathEdges.push({id:'e1',from:'n1',to:'n2',mode:'outdoor-walk',provenance:[{sourceId:'src-1',nativeId:'e1',verification:'field-reviewed'}]});
  data.entrances.push({id:'ent1',buildingId:'b1',coordinate:[0,0],pathNodeId:'n1',access:'public',provenance:[{sourceId:'src-1',nativeId:'ent1',verification:'field-reviewed'}]});
  assert.deepEqual(validateCampus(data), []);
});

test('rejects duplicate native building codes case-insensitively', () => {
  const data = read('campus');
  data.sources.push({id:'src-1',title:'Test',url:'https://example.com',retrievedAt:'2026-09-24',licenseOrTerms:'Permitted',redistribution:'permitted',transformation:'None'});
  data.buildings.push({id:'b1',name:'Building One',nativeCodes:['BO'],aliases:[],geometry:null,provenance:[{sourceId:'src-1',nativeId:'1',verification:'inferred'}]});
  data.buildings.push({id:'b2',name:'Building Two',nativeCodes:['bo'],aliases:[],geometry:null,provenance:[{sourceId:'src-1',nativeId:'2',verification:'inferred'}]});
  assert.match(validateCampus(data).join(' '), /native building codes must be unique/);
});

test('rejects entrance with mismatched coordinate or unknown path node', () => {
  const data = read('campus');
  data.sources.push({id:'src-1',title:'Test',url:'https://example.com',retrievedAt:'2026-09-24',licenseOrTerms:'Permitted',redistribution:'permitted',transformation:'None'});
  data.buildings.push({id:'b1',name:'Building One',nativeCodes:['BO'],aliases:[],geometry:null,provenance:[{sourceId:'src-1',nativeId:'1',verification:'inferred'}]});
  data.pathNodes.push({id:'n1',coordinate:[0,0],provenance:[{sourceId:'src-1',nativeId:'n1',verification:'field-reviewed'}]});
  data.entrances.push({id:'ent1',buildingId:'b1',coordinate:[0,1],pathNodeId:'n1',access:'public',provenance:[{sourceId:'src-1',nativeId:'ent1',verification:'field-reviewed'}]});
  assert.match(validateCampus(data).join(' '), /entrance and graph node coordinates differ/);
});

test('rejects self-referential or nonexistent edge endpoints', () => {
  const data = read('campus');
  data.sources.push({id:'src-1',title:'Test',url:'https://example.com',retrievedAt:'2026-09-24',licenseOrTerms:'Permitted',redistribution:'permitted',transformation:'None'});
  data.pathNodes.push({id:'n1',coordinate:[0,0],provenance:[{sourceId:'src-1',nativeId:'n1',verification:'field-reviewed'}]});
  data.pathEdges.push({id:'e1',from:'n1',to:'n1',mode:'outdoor-walk',provenance:[{sourceId:'src-1',nativeId:'e1',verification:'field-reviewed'}]});
  assert.match(validateCampus(data).join(' '), /invalid endpoints/);
});

test('rejects inverted campus bounds', () => {
  const data = read('campus');
  data.campus.bounds = [[10, 20], [5, 25]];
  assert.match(validateCampus(data).join(' '), /campus bounds must run southwest to northeast/);
});

test('validates a complete, valid academic fixture', () => {
  const data = read('academic');
  data.sources.push({id:'src-acad',title:'Academic Schedule',url:'https://example.com/sched',retrievedAt:'2026-09-24',licenseOrTerms:'Permitted',redistribution:'permitted',transformation:'Direct'});
  data.terms.push({id:'F26',nativeName:'Fall 2026',startDate:'2026-09-09',endDate:'2026-12-09',sourceId:'src-acad'});
  data.courses.push({
    code:'BUSI 1004',
    title:'Financial Accounting',
    termId:'F26',
    sourceId:'src-acad',
    sections:[
      {
        nativeSection:'A',
        nativeComponentType:'LEC',
        crn:'10001',
        linkedSectionIds:[],
        sourceId:'src-acad',
        meetings:[{days:['MO','WE'],startTime:'08:35',endTime:'09:55',startDate:'2026-09-09',endDate:'2026-12-09',nativeLocation:'TB 101'}]
      },
      {
        nativeSection:'A1',
        nativeComponentType:'TUT',
        crn:'10002',
        linkedSectionIds:['A'],
        sourceId:'src-acad',
        meetings:[{days:['FR'],startTime:'11:35',endTime:'12:25',startDate:'2026-09-09',endDate:'2026-12-09',nativeLocation:'TB 202'}]
      }
    ]
  });
  assert.deepEqual(validateAcademic(data), []);
});

test('rejects academic meeting with invalid interval', () => {
  const data = read('academic');
  data.sources.push({id:'src-acad',title:'Academic Schedule',url:'https://example.com/sched',retrievedAt:'2026-09-24',licenseOrTerms:'Permitted',redistribution:'permitted',transformation:'Direct'});
  data.terms.push({id:'F26',nativeName:'Fall 2026',startDate:'2026-09-09',endDate:'2026-12-09',sourceId:'src-acad'});
  data.courses.push({
    code:'BUSI 1004',
    title:'Financial Accounting',
    termId:'F26',
    sourceId:'src-acad',
    sections:[{
      nativeSection:'A',
      nativeComponentType:'LEC',
      crn:'10001',
      linkedSectionIds:[],
      sourceId:'src-acad',
      meetings:[{days:['MO'],startTime:'10:00',endTime:'09:00',startDate:'2026-09-09',endDate:'2026-12-09',nativeLocation:null}]
    }]
  });
  assert.match(validateAcademic(data).join(' '), /invalid meeting interval/);
});

test('rejects unpermitted academic or campus source', () => {
  const data = read('academic');
  data.sources.push({id:'src-unclear',title:'Unclear source',url:'https://example.com',retrievedAt:'2026-09-24',licenseOrTerms:'Unknown',redistribution:'unclear',transformation:'None'});
  data.terms.push({id:'F26',nativeName:'Fall 2026',startDate:'2026-09-09',endDate:'2026-12-09',sourceId:'src-unclear'});
  assert.match(validateAcademic(data).join(' '), /source absent or not redistributable/);
});
