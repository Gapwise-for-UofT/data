import { readFileSync, readdirSync, existsSync } from 'node:fs';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';

const read = (file) => JSON.parse(readFileSync(new URL(`../${file}`, import.meta.url), 'utf8'));
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
const unique = (values, label, errors) => {
  if (new Set(values).size !== values.length) errors.push(`${label} must be unique`);
};
const coordinatesEqual = (a, b) => a[0] === b[0] && a[1] === b[1];
function validPolygon(rings) {
  return Array.isArray(rings) && rings.length > 0 && rings.every((ring) =>
    Array.isArray(ring) && ring.length >= 4 &&
    ring.every((point) => Array.isArray(point) && point.length === 2 &&
      typeof point[0] === 'number' && point[0] >= -180 && point[0] <= 180 &&
      typeof point[1] === 'number' && point[1] >= -90 && point[1] <= 90) &&
    coordinatesEqual(ring[0], ring[ring.length - 1]));
}

export function validateCampus(campus) {
  const errors = [];
  const schema = read('schemas/universities/campus.schema.json');
  const check = ajv.compile(schema);
  if (!check(campus)) return check.errors.map((e) => `${e.instancePath} ${e.message}`);
  const sourceIds = new Set(campus.sources.filter((s) => s.redistribution === 'permitted').map((s) => s.id));
  const ids = new Set(campus.buildings.map((b) => b.id));
  const nodes = new Map(campus.pathNodes.map((n) => [n.id, n]));
  unique(campus.sources.map((s) => s.id), 'source IDs', errors);
  unique([...campus.buildings, ...campus.entrances, ...campus.pathNodes, ...campus.pathEdges].map((r) => r.id), 'record IDs', errors);
  unique(campus.buildings.flatMap((b) => b.nativeCodes.map((c) => c.toUpperCase())), 'native building codes', errors);
  for (const record of [...campus.buildings, ...campus.entrances, ...campus.pathNodes, ...campus.pathEdges]) {
    for (const provenance of record.provenance) if (!sourceIds.has(provenance.sourceId)) errors.push(`${record.id}: source ${provenance.sourceId} is absent or not redistributable`);
  }
  for (const building of campus.buildings) if (building.geometry) {
    const valid = building.geometry.type === 'Polygon'
      ? validPolygon(building.geometry.coordinates)
      : building.geometry.coordinates.every(validPolygon);
    if (!valid) errors.push(`${building.id}: invalid closed GeoJSON polygon geometry`);
  }
  for (const entrance of campus.entrances) {
    if (!ids.has(entrance.buildingId)) errors.push(`${entrance.id}: unknown building`);
    if (!nodes.has(entrance.pathNodeId)) errors.push(`${entrance.id}: unknown path node`);
    else if (!coordinatesEqual(entrance.coordinate, nodes.get(entrance.pathNodeId).coordinate)) errors.push(`${entrance.id}: entrance and graph node coordinates differ`);
  }
  for (const edge of campus.pathEdges) {
    if (!nodes.has(edge.from) || !nodes.has(edge.to) || edge.from === edge.to) errors.push(`${edge.id}: invalid endpoints`);
    for (const provenance of edge.provenance) {
      if (provenance.sourceId === 'osm-carleton-2026-09' &&
          (provenance.verification !== 'source-backed' || !/^way\/\d+$/.test(provenance.nativeId ?? ''))) {
        errors.push(`${edge.id}: OSM path edge must cite a mapped OSM way; inferred nearest-node links are not paths`);
      }
    }
  }
  if (campus.campus.bounds && (campus.campus.bounds[0][0] >= campus.campus.bounds[1][0] || campus.campus.bounds[0][1] >= campus.campus.bounds[1][1])) errors.push('campus bounds must run southwest to northeast');
  return errors;
}

export function validateAcademic(academic) {
  const errors = [];
  const check = ajv.compile(read('schemas/universities/academic.schema.json'));
  if (!check(academic)) return check.errors.map((e) => `${e.instancePath} ${e.message}`);
  const sources = new Set(academic.sources.filter((s) => s.redistribution === 'permitted').map((s) => s.id));
  const terms = new Set(academic.terms.map((t) => t.id));
  unique(academic.sources.map((s) => s.id), 'source IDs', errors);
  unique(academic.terms.map((t) => t.id), 'term IDs', errors);
  unique(academic.courses.map((c) => `${c.termId}:${c.code}`), 'course keys', errors);
  for (const term of academic.terms) if (!sources.has(term.sourceId)) errors.push(`${term.id}: source absent or not redistributable`);
  for (const course of academic.courses) {
    if (!terms.has(course.termId)) errors.push(`${course.code}: unknown term`);
    if (!sources.has(course.sourceId)) errors.push(`${course.code}: source absent or not redistributable`);
    unique(course.sections.map((s) => s.nativeSection), `${course.code} section IDs`, errors);
    const sectionIds = new Set(course.sections.map((s) => s.nativeSection));
    for (const section of course.sections) {
      if (!sources.has(section.sourceId)) errors.push(`${course.code} ${section.nativeSection}: source absent or not redistributable`);
      for (const id of section.linkedSectionIds) if (!sectionIds.has(id)) errors.push(`${course.code} ${section.nativeSection}: unknown linked section ${id}`);
      for (const meeting of section.meetings) if (meeting.endTime <= meeting.startTime || meeting.endDate < meeting.startDate) errors.push(`${course.code} ${section.nativeSection}: invalid meeting interval`);
    }
  }
  return errors;
}

if (process.argv[1] && new URL(`file://${process.argv[1]}`).href === import.meta.url) {
  const requested = process.argv[2];
  const ids = requested ? [requested] : readdirSync(new URL('../universities/', import.meta.url), { withFileTypes: true })
    .filter((entry) => entry.isDirectory()).map((entry) => entry.name);
  const errors = [];
  for (const id of ids) {
    if (!/^[a-z][a-z0-9-]*$/.test(id)) { errors.push(`invalid university ID: ${id}`); continue; }
    const campusPath = `universities/${id}/campus.json`;
    const academicPath = `universities/${id}/academic.json`;
    if (!existsSync(new URL(`../${campusPath}`, import.meta.url))) { errors.push(`${id}: campus snapshot missing`); continue; }
    const campus = read(campusPath);
    if (campus.institution !== id) errors.push(`${id}: campus institution ID differs from path`);
    errors.push(...validateCampus(campus).map((error) => `${id}: ${error}`));
    if (existsSync(new URL(`../${academicPath}`, import.meta.url))) {
      const academic = read(academicPath);
      if (academic.institution !== id) errors.push(`${id}: academic institution ID differs from path`);
      errors.push(...validateAcademic(academic).map((error) => `${id}: ${error}`));
    }
  }
  if (errors.length) { console.error(errors.join('\n')); process.exitCode = 1; }
  else console.log(`University snapshots valid: ${ids.join(', ')}`);
}
