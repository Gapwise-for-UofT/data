import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const CAMPUS = "carleton";
const OVERPASS_URLS = [
  "https://overpass.kumi.systems/api/interpreter",
  "https://overpass-api.de/api/interpreter",
  "https://overpass.private.coffee/api/interpreter",
];
const NOMINATIM_SEARCH = "https://nominatim.openstreetmap.org/search";
const OTTAWA_BUILDINGS =
  "https://maps.ottawa.ca/arcgis/rest/services/TopographicMapping/MapServer/3/query";

function normalize(value) {
  return String(value ?? "")
    .normalize("NFKD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/\bcenter\b/g, " centre ")
    .replace(/\blaboratories\b/g, " labs ")
    .replace(/\blaboratory\b/g, " lab ")
    .replace(/\bbuilding\b/g, " ")
    .replace(/\bthe\b/g, " ")
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function stableUnique(values) {
  return [...new Set(values.filter(Boolean))].sort((a, b) => String(a).localeCompare(String(b)));
}

async function readJson(path) {
  return JSON.parse(await readFile(resolve(root, path), "utf8"));
}

async function writeJson(path, value) {
  const absolute = resolve(root, path);
  await mkdir(dirname(absolute), { recursive: true });
  await writeFile(absolute, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

async function fetchWithRetry(url, init = {}, label = url) {
  let lastError = null;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      const response = await fetch(url, {
        ...init,
        signal: init.signal ?? AbortSignal.timeout(45_000),
        headers: {
          accept: "application/json",
          "user-agent": "Gapwise-Data/carleton-refresh (+https://data.gapwise.ca)",
          ...(init.headers ?? {}),
        },
      });
      if (!response.ok) {
        throw new Error(`${label} returned HTTP ${response.status}: ${(await response.text()).slice(0, 500)}`);
      }
      return response;
    } catch (error) {
      lastError = error;
      if (attempt < 3) await new Promise((resolveDelay) => setTimeout(resolveDelay, 1200 * attempt));
    }
  }
  throw lastError;
}

async function fetchJson(url, init = {}, label = url) {
  return (await fetchWithRetry(url, init, label)).json();
}

function canonicalizeInventory(inventory) {
  return inventory.records
    .filter((record) => record.status !== "demolished")
    .map((record) => {
      const code = String(record.code ?? "").trim().toUpperCase();
      if (!code || !record.name) throw new Error(`Carleton source record is missing code/name: ${JSON.stringify(record)}`);
      return {
        id: `${CAMPUS}:${code}`,
        campus: CAMPUS,
        code,
        name: String(record.name).trim(),
        category: record.category ?? "facility",
        aliases: stableUnique(record.aliases ?? []),
        timetableCodes: [String(record.timetableCode ?? code).trim().toUpperCase()],
        facilityCodes: [],
        mapUrls: [`https://carleton.ca/campus-map/#${code}`],
        geometryAddresses: [],
        geometryRefs: [],
        geometryPoints: [],
        hostBuildingCode: null,
        hostEvidence: null,
        identityEvidence: stableUnique([inventory.sourceId, record.sourceId]),
        sourceNames: [String(record.name).trim()],
        displayNameEvidence: null,
        status: "active",
      };
    })
    .sort((a, b) => a.code.localeCompare(b.code));
}

function recordNames(record) {
  return stableUnique([record.name, ...(record.aliases ?? []), ...(record.sourceNames ?? [])]);
}

function bboxString(bounds) {
  return `${bounds.minLat},${bounds.minLon},${bounds.maxLat},${bounds.maxLon}`;
}

async function fetchOsmCampus(bounds) {
  const bbox = bboxString(bounds);
  const query = `[out:json][timeout:120];
(
  nwr["building"](${bbox});
  node["entrance"](${bbox});
  way["highway"~"^(footway|path|pedestrian|steps|living_street|corridor)$"](${bbox});
);
out body center geom;`;
  let lastError = null;
  for (const endpoint of OVERPASS_URLS) {
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          accept: "application/json",
          "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
          "user-agent": "Gapwise-Data/carleton-refresh (+https://data.gapwise.ca)",
        },
        body: new URLSearchParams({ data: query }),
        signal: AbortSignal.timeout(60_000),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${(await response.text()).slice(0, 500)}`);
      return response.json();
    } catch (error) {
      lastError = error;
      console.warn(`Overpass endpoint ${endpoint} failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  throw new Error(`All Overpass endpoints failed: ${lastError instanceof Error ? lastError.message : String(lastError)}`);
}

async function fetchOttawaFootprints(bounds) {
  const features = [];
  for (let offset = 0; offset < 5000; offset += 1000) {
    const params = new URLSearchParams({
      where: "1=1",
      geometry: `${bounds.minLon},${bounds.minLat},${bounds.maxLon},${bounds.maxLat}`,
      geometryType: "esriGeometryEnvelope",
      inSR: "4326",
      spatialRel: "esriSpatialRelIntersects",
      outFields: "OBJECTID,GlobalID",
      returnGeometry: "true",
      outSR: "4326",
      f: "geojson",
      resultOffset: String(offset),
      resultRecordCount: "1000",
    });
    const page = await fetchJson(`${OTTAWA_BUILDINGS}?${params}`, {}, "Ottawa building footprints");
    const batch = page.features ?? [];
    features.push(...batch);
    if (batch.length < 1000 || !page.exceededTransferLimit) return features;
  }
  throw new Error("Ottawa building footprint pagination exceeded 5,000 features inside Carleton bounds.");
}

function sameCoordinate(a, b) {
  return Boolean(a && b && a[0] === b[0] && a[1] === b[1]);
}

function wayPolygon(element) {
  if (element.type !== "way") return null;
  const points = (element.geometry ?? []).map((point) => [point.lon, point.lat]);
  if (points.length < 4) return null;
  if (!sameCoordinate(points[0], points.at(-1))) points.push([...points[0]]);
  return { type: "Polygon", coordinates: [points] };
}

function stitchOuterSegments(segments) {
  const remaining = segments.filter((segment) => segment.length >= 2).map((segment) => segment.map((point) => [...point]));
  const rings = [];
  while (remaining.length) {
    let ring = remaining.shift();
    let changed = true;
    while (changed && !sameCoordinate(ring[0], ring.at(-1))) {
      changed = false;
      for (let index = 0; index < remaining.length; index += 1) {
        const segment = remaining[index];
        if (sameCoordinate(ring.at(-1), segment[0])) ring = [...ring, ...segment.slice(1)];
        else if (sameCoordinate(ring.at(-1), segment.at(-1))) ring = [...ring, ...segment.slice(0, -1).reverse()];
        else if (sameCoordinate(ring[0], segment.at(-1))) ring = [...segment.slice(0, -1), ...ring];
        else if (sameCoordinate(ring[0], segment[0])) ring = [...segment.slice(1).reverse(), ...ring];
        else continue;
        remaining.splice(index, 1);
        changed = true;
        break;
      }
    }
    if (ring.length >= 4 && sameCoordinate(ring[0], ring.at(-1))) rings.push(ring);
  }
  return rings;
}

function relationPolygon(element) {
  if (element.type !== "relation") return null;
  const outerSegments = (element.members ?? [])
    .filter((member) => member.type === "way" && member.role === "outer")
    .map((member) => (member.geometry ?? []).map((point) => [point.lon, point.lat]));
  const rings = stitchOuterSegments(outerSegments);
  if (!rings.length) return null;
  if (rings.length === 1) return { type: "Polygon", coordinates: [rings[0]] };
  return { type: "MultiPolygon", coordinates: rings.map((ring) => [ring]) };
}

function osmCenter(element) {
  if (element.center && Number.isFinite(element.center.lon) && Number.isFinite(element.center.lat)) return [element.center.lon, element.center.lat];
  if (Number.isFinite(element.lon) && Number.isFinite(element.lat)) return [element.lon, element.lat];
  const points = element.geometry ?? [];
  if (!points.length) return null;
  return [
    points.reduce((sum, point) => sum + point.lon, 0) / points.length,
    points.reduce((sum, point) => sum + point.lat, 0) / points.length,
  ];
}

function osmIdentityTokens(element) {
  const tags = element.tags ?? {};
  return stableUnique([tags.name, tags.official_name, tags.alt_name, tags.short_name, tags.ref]).map(normalize);
}

function buildOsmMatches(buildings, elements) {
  const buildingElements = elements.filter((element) => element.tags?.building);
  const matches = new Map();
  for (const building of buildings) {
    const names = recordNames(building).map(normalize);
    const code = normalize(building.code);
    const candidates = buildingElements.filter((element) => {
      const tokens = osmIdentityTokens(element);
      return tokens.some((token) => names.includes(token) || token === code);
    });
    const unique = [...new Map(candidates.map((element) => [`${element.type}/${element.id}`, element])).values()];
    if (unique.length === 1) matches.set(building.id, unique[0]);
    else if (unique.length > 1) {
      const exactName = unique.filter((element) => {
        const tags = element.tags ?? {};
        return [tags.name, tags.official_name, tags.alt_name].filter(Boolean).map(normalize).some((token) => names.includes(token));
      });
      if (exactName.length === 1) matches.set(building.id, exactName[0]);
    }
  }
  return matches;
}

function pointInRing(point, ring) {
  const [x, y] = point;
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    const intersects = yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi || Number.EPSILON) + xi;
    if (intersects) inside = !inside;
  }
  return inside;
}

function pointInGeometry(point, geometry) {
  if (!geometry) return false;
  if (geometry.type === "Polygon") {
    if (!pointInRing(point, geometry.coordinates[0] ?? [])) return false;
    return geometry.coordinates.slice(1).every((hole) => !pointInRing(point, hole));
  }
  if (geometry.type === "MultiPolygon") {
    return geometry.coordinates.some((polygon) => pointInGeometry(point, { type: "Polygon", coordinates: polygon }));
  }
  return false;
}

function geometryCoordinates(geometry) {
  if (!geometry) return [];
  if (geometry.type === "Polygon") return geometry.coordinates.flat();
  if (geometry.type === "MultiPolygon") return geometry.coordinates.flat(2);
  return [];
}

function cityGeometryForPoint(point, cityFeatures) {
  const containing = cityFeatures.filter((feature) => pointInGeometry(point, feature.geometry));
  if (containing.length !== 1) return null;
  const feature = containing[0];
  return {
    geometry: feature.geometry,
    source: "ottawa-building-footprints",
    sourceRef: String(feature.properties?.OBJECTID ?? feature.properties?.GlobalID ?? feature.id ?? ""),
    method: "ottawa_polygon_containing_source_backed_point",
  };
}

async function geometryForCanonicalName(building, bounds, cityFeatures) {
  const params = new URLSearchParams({
    format: "jsonv2",
    q: `${building.name}, Carleton University, Ottawa, Ontario, Canada`,
    limit: "6",
    addressdetails: "1",
    namedetails: "1",
    polygon_geojson: "1",
    bounded: "1",
    viewbox: `${bounds.minLon},${bounds.maxLat},${bounds.maxLon},${bounds.minLat}`,
  });
  let results;
  try {
    results = await fetchJson(`${NOMINATIM_SEARCH}?${params}`, { headers: { "accept-language": "en" } }, `Nominatim ${building.name}`);
  } catch (error) {
    console.warn(`Nominatim failed for ${building.code} ${building.name}: ${error instanceof Error ? error.message : String(error)}`);
    return null;
  }
  const acceptedNames = new Set(recordNames(building).map(normalize));
  const candidates = (Array.isArray(results) ? results : [])
    .map((result) => ({
      result,
      point: [Number(result.lon), Number(result.lat)],
      names: stableUnique([result.name, result.namedetails?.name, result.namedetails?.["name:en"], result.display_name?.split(",")[0]]).map(normalize),
    }))
    .filter(({ point, names }) =>
      Number.isFinite(point[0]) && Number.isFinite(point[1]) &&
      point[0] >= bounds.minLon && point[0] <= bounds.maxLon && point[1] >= bounds.minLat && point[1] <= bounds.maxLat &&
      names.some((name) => acceptedNames.has(name))
    );
  const unique = [...new Map(candidates.map((candidate) => [`${candidate.result.osm_type}:${candidate.result.osm_id ?? candidate.result.place_id}`, candidate])).values()];
  if (unique.length !== 1) return null;
  const { result, point } = unique[0];
  if (result.geojson && ["Polygon", "MultiPolygon"].includes(result.geojson.type)) {
    return {
      geometry: result.geojson,
      source: "openstreetmap",
      sourceRef: `${result.osm_type ?? "osm"}/${result.osm_id ?? ""}`,
      method: "exact_canonical_name_nominatim_polygon",
    };
  }
  return cityGeometryForPoint(point, cityFeatures);
}

function geometryForMatchedOsm(element, cityFeatures) {
  const geometry = wayPolygon(element) ?? relationPolygon(element);
  if (geometry) {
    return {
      geometry,
      source: "openstreetmap",
      sourceRef: `${element.type}/${element.id}`,
      method: "exact_identity_match",
    };
  }
  const center = osmCenter(element);
  return center ? cityGeometryForPoint(center, cityFeatures) : null;
}

function haversineMeters(a, b) {
  const R = 6371000;
  const rad = (value) => (value * Math.PI) / 180;
  const dLat = rad(b[1] - a[1]);
  const dLon = rad(b[0] - a[0]);
  const lat1 = rad(a[1]);
  const lat2 = rad(b[1]);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

function localXY(point, origin) {
  const latScale = 111_320;
  const lonScale = Math.cos((origin[1] * Math.PI) / 180) * 111_320;
  return [(point[0] - origin[0]) * lonScale, (point[1] - origin[1]) * latScale];
}

function distancePointToSegmentMeters(point, a, b) {
  const p = localXY(point, point);
  const av = localXY(a, point);
  const bv = localXY(b, point);
  const dx = bv[0] - av[0];
  const dy = bv[1] - av[1];
  const denom = dx * dx + dy * dy;
  const t = denom ? Math.max(0, Math.min(1, ((p[0] - av[0]) * dx + (p[1] - av[1]) * dy) / denom)) : 0;
  return Math.hypot(p[0] - (av[0] + t * dx), p[1] - (av[1] + t * dy));
}

function distanceToGeometryMeters(point, geometry) {
  const rings = geometry?.type === "Polygon"
    ? geometry.coordinates
    : geometry?.type === "MultiPolygon"
      ? geometry.coordinates.flat()
      : [];
  let best = Infinity;
  for (const ring of rings) {
    for (let index = 1; index < ring.length; index += 1) {
      best = Math.min(best, distancePointToSegmentMeters(point, ring[index - 1], ring[index]));
    }
  }
  return best;
}

function makePedestrianGraph(elements) {
  const nodeMap = new Map();
  const edges = [];
  const features = [];
  const keyFor = ([lon, lat]) => `${lon.toFixed(7)},${lat.toFixed(7)}`;
  for (const way of elements.filter((element) => element.type === "way" && element.tags?.highway)) {
    const tags = way.tags ?? {};
    if (tags.access === "private" || tags.access === "no") continue;
    const coordinates = (way.geometry ?? []).map((point) => [point.lon, point.lat]);
    if (coordinates.length < 2) continue;
    features.push({
      type: "Feature",
      id: `osm-way-${way.id}`,
      properties: {
        osmWayId: way.id,
        highway: tags.highway,
        indoor: tags.indoor ?? null,
        tunnel: tags.tunnel ?? null,
        level: tags.level ?? null,
        wheelchair: tags.wheelchair ?? null,
        surface: tags.surface ?? null,
        verificationStatus: "inferred",
        source: "OpenStreetMap",
      },
      geometry: { type: "LineString", coordinates },
    });
    for (const coordinate of coordinates) {
      const key = keyFor(coordinate);
      if (!nodeMap.has(key)) {
        nodeMap.set(key, {
          id: `osm-${key}`,
          longitude: coordinate[0], latitude: coordinate[1], kind: "path", verificationStatus: "inferred",
        });
      }
    }
    for (let index = 1; index < coordinates.length; index += 1) {
      const from = nodeMap.get(keyFor(coordinates[index - 1]));
      const to = nodeMap.get(keyFor(coordinates[index]));
      if (!from || !to || from.id === to.id) continue;
      edges.push({
        id: `osm-way-${way.id}-${index - 1}`,
        from: from.id, to: to.id,
        distanceMeters: Math.round(haversineMeters(coordinates[index - 1], coordinates[index]) * 100) / 100,
        bidirectional: tags.oneway !== "yes",
        kind: tags.highway,
        indoor: tags.indoor ?? null,
        tunnel: tags.tunnel ?? null,
        level: tags.level ?? null,
        wheelchair: tags.wheelchair ?? null,
        verificationStatus: "inferred",
      });
    }
  }
  return {
    nodes: [...nodeMap.values()].sort((a, b) => a.id.localeCompare(b.id)),
    edges: edges.sort((a, b) => a.id.localeCompare(b.id)),
    geojson: { type: "FeatureCollection", features },
  };
}

function nearestGraphNode(point, graph, maxMeters = 40) {
  let best = null;
  for (const node of graph.nodes) {
    const distanceMeters = haversineMeters(point, [node.longitude, node.latitude]);
    if (!best || distanceMeters < best.distanceMeters) best = { node, distanceMeters };
  }
  return best && best.distanceMeters <= maxMeters ? best : null;
}

function deriveEntrances(osmElements, footprintFeatures, graph) {
  const entrances = [];
  const entranceNodes = osmElements.filter((element) => element.type === "node" && element.tags?.entrance && Number.isFinite(element.lon) && Number.isFinite(element.lat));
  for (const node of entranceNodes) {
    const point = [node.lon, node.lat];
    const candidates = footprintFeatures
      .map((feature) => ({ feature, distance: distanceToGeometryMeters(point, feature.geometry), inside: pointInGeometry(point, feature.geometry) }))
      .filter((candidate) => candidate.inside || candidate.distance <= 6)
      .sort((a, b) => a.distance - b.distance);
    if (!candidates.length) continue;
    if (candidates.length > 1 && Math.abs(candidates[0].distance - candidates[1].distance) < 1.5) continue;
    const feature = candidates[0].feature;
    const nearest = nearestGraphNode(point, graph, 40);
    const code = feature.properties.buildingCode;
    entrances.push({
      type: "Feature",
      id: `${CAMPUS}:${code}:osm-entrance-${node.id}`,
      properties: {
        campus: CAMPUS,
        buildingId: feature.properties.buildingId,
        buildingCode: code,
        name: node.tags?.name ?? null,
        entrance: node.tags?.entrance ?? "yes",
        wheelchair: node.tags?.wheelchair ?? null,
        access: node.tags?.access ?? null,
        level: node.tags?.level ?? null,
        routingNodeId: nearest?.node.id ?? null,
        routingNodeDistanceMeters: nearest ? Math.round(nearest.distanceMeters * 10) / 10 : null,
        geometrySource: "openstreetmap",
        geometrySourceRef: `node/${node.id}`,
        verificationStatus: "inferred",
        note: "OpenStreetMap entrance associated geometrically with the source-backed Carleton building footprint; not field-verified by Gapwise.",
      },
      geometry: { type: "Point", coordinates: point },
    });
  }
  return entrances.sort((a, b) => String(a.id).localeCompare(String(b.id)));
}

function approachForBuilding(feature, buildingEntrances, graph) {
  const routedEntrance = buildingEntrances.find((entrance) => entrance.properties.routingNodeId);
  if (routedEntrance) {
    return {
      buildingId: feature.properties.buildingId,
      nodeId: routedEntrance.properties.routingNodeId,
      entranceId: routedEntrance.id,
      longitude: routedEntrance.geometry.coordinates[0],
      latitude: routedEntrance.geometry.coordinates[1],
      distanceFromFootprintMeters: 0,
      verificationStatus: "inferred",
      semantics: "osm-entrance-routing-approach",
      notes: "Uses an OpenStreetMap entrance geometrically associated with this building and the nearest pedestrian-network node. Not field-verified by Gapwise.",
    };
  }
  const outline = geometryCoordinates(feature.geometry);
  let best = null;
  for (const point of outline) {
    const nearest = nearestGraphNode(point, graph, 100);
    if (nearest && (!best || nearest.distanceMeters < best.distanceMeters)) best = { point, ...nearest };
  }
  if (!best) return null;
  return {
    buildingId: feature.properties.buildingId,
    nodeId: best.node.id,
    entranceId: null,
    longitude: best.node.longitude,
    latitude: best.node.latitude,
    distanceFromFootprintMeters: Math.round(best.distanceMeters * 10) / 10,
    verificationStatus: "inferred",
    semantics: "derived-routing-approach",
    notes: "Nearest pedestrian-network vertex to the building footprint. This is not a verified physical entrance.",
  };
}

function connectedComponents(graph) {
  const adjacent = new Map(graph.nodes.map((node) => [node.id, new Set()]));
  for (const edge of graph.edges) {
    adjacent.get(edge.from)?.add(edge.to);
    adjacent.get(edge.to)?.add(edge.from);
  }
  const seen = new Set();
  const sizes = [];
  for (const node of graph.nodes) {
    if (seen.has(node.id)) continue;
    let size = 0;
    const stack = [node.id];
    seen.add(node.id);
    while (stack.length) {
      const id = stack.pop();
      size += 1;
      for (const next of adjacent.get(id) ?? []) {
        if (!seen.has(next)) { seen.add(next); stack.push(next); }
      }
    }
    sizes.push(size);
  }
  return sizes.sort((a, b) => b - a);
}

async function main() {
  const source = await readJson("data/carleton/source.json");
  const inventory = await readJson("data/carleton/sources/official-buildings.json");
  const aliases = await readJson("data/carleton/sources/reconciliation-aliases.json");
  const buildings = canonicalizeInventory(inventory);

  for (const building of buildings) {
    const mappedNames = Object.entries(aliases.names ?? {}).filter(([, target]) => String(target).toUpperCase() === building.code).map(([name]) => name);
    building.aliases = stableUnique([...building.aliases, ...mappedNames]);
  }

  const [osm, cityFeatures] = await Promise.all([fetchOsmCampus(source.bounds), fetchOttawaFootprints(source.bounds)]);
  const osmElements = osm.elements ?? [];
  const osmMatches = buildOsmMatches(buildings, osmElements);
  const graph = makePedestrianGraph(osmElements);
  const footprintFeatures = [];
  const unresolvedGeometry = [];

  for (const building of buildings) {
    const match = osmMatches.get(building.id);
    let resolved = match ? geometryForMatchedOsm(match, cityFeatures) : null;
    if (!resolved) {
      resolved = await geometryForCanonicalName(building, source.bounds, cityFeatures);
      await new Promise((resolveDelay) => setTimeout(resolveDelay, 1100));
    }
    if (!resolved?.geometry) {
      unresolvedGeometry.push({
        id: building.id,
        code: building.code,
        name: building.name,
        reason: "No unique source-backed building polygon could be reconciled automatically.",
      });
      continue;
    }
    footprintFeatures.push({
      type: "Feature",
      id: building.id,
      properties: {
        campus: CAMPUS,
        buildingId: building.id,
        buildingCode: building.code,
        name: building.name,
        timetableCodes: building.timetableCodes,
        facilityCodes: [],
        geometrySource: resolved.source,
        geometrySourceRef: resolved.sourceRef,
        reconciliationMethod: resolved.method,
        verificationStatus: "inferred",
      },
      geometry: resolved.geometry,
    });
  }

  const entrances = deriveEntrances(osmElements, footprintFeatures, graph);
  const entrancesByBuilding = new Map();
  for (const entrance of entrances) {
    const id = entrance.properties.buildingId;
    const current = entrancesByBuilding.get(id) ?? [];
    current.push(entrance);
    entrancesByBuilding.set(id, current);
  }
  const approaches = footprintFeatures
    .map((feature) => approachForBuilding(feature, entrancesByBuilding.get(feature.properties.buildingId) ?? [], graph))
    .filter(Boolean);
  const components = connectedComponents(graph);
  const generatedAt = new Date().toISOString();
  const coverage = {
    campus: CAMPUS,
    generatedAt,
    identitySourceCount: inventory.records.filter((record) => record.status !== "demolished").length,
    canonicalBuildingCount: buildings.length,
    timetableBuildingCount: buildings.length,
    timetableCodeCount: stableUnique(buildings.flatMap((building) => building.timetableCodes)).length,
    geometryResolvedCount: footprintFeatures.length,
    geometryUnresolvedCount: unresolvedGeometry.length,
    mappedDestinationCount: footprintFeatures.length,
    mappedEntranceCount: entrances.length,
    routableEntranceCount: entrances.filter((entrance) => entrance.properties.routingNodeId).length,
    routingApproachCount: approaches.length,
    pedestrianNodeCount: graph.nodes.length,
    pedestrianEdgeCount: graph.edges.length,
    pedestrianComponentCount: components.length,
    largestPedestrianComponentNodes: components[0] ?? 0,
    unresolvedGeometry,
  };

  await writeJson("data/carleton/buildings.json", {
    campus: CAMPUS,
    generatedAt,
    sourceIds: source.identitySources.map((entry) => entry.id),
    buildings,
  });
  await writeJson("data/carleton/buildings.geojson", {
    type: "FeatureCollection",
    name: "Gapwise Carleton building footprints",
    features: footprintFeatures,
  });
  await writeJson("data/carleton/entrances.geojson", {
    type: "FeatureCollection",
    name: "Gapwise Carleton inferred OSM entrances",
    features: entrances,
  });
  await writeJson("data/carleton/generated/pedestrian-network.geojson", graph.geojson);
  await writeJson("data/carleton/generated/routing-graph.json", {
    campus: CAMPUS,
    generatedAt,
    source: "OpenStreetMap",
    verificationStatus: "inferred",
    nodes: graph.nodes,
    edges: graph.edges,
  });
  await writeJson("data/carleton/generated/routing-approaches.json", {
    campus: CAMPUS,
    generatedAt,
    semantics: "OSM entrance-backed route endpoints when available; otherwise derived footprint approaches. All remain inferred until independently verified.",
    approaches,
  });
  await writeJson("data/carleton/generated/coverage.json", coverage);
  console.log(
    `CARLETON: ${coverage.canonicalBuildingCount} identities; ${coverage.geometryResolvedCount} geometries; ` +
    `${coverage.mappedEntranceCount} inferred OSM entrances; ${coverage.routingApproachCount} routing approaches; ` +
    `${coverage.pedestrianNodeCount} pedestrian nodes / ${coverage.pedestrianEdgeCount} edges.`,
  );
}

await main();
