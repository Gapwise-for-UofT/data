import {
  buildings as utmBuildings,
  entranceFeatures as utmEntranceFeatures,
  footprintFeatures as utmFootprintFeatures,
  geometryCoordinates,
  metersBetween,
  todayLocalDate,
} from './entrance-map-data.js';
import utsgRegistry from '../data/utsg/buildings.json';
import utsgFootprintsJson from '../data/utsg/buildings.geojson?raw';
import utscRegistry from '../data/utsc/buildings.json';
import utscFootprintsJson from '../data/utsc/buildings.geojson?raw';
import carletonCampus from '../universities/carleton/campus.json';
import tmuCampus from '../universities/tmu/campus.json';
import queensCampus from '../universities/queens/campus.json';
import laurierCampus from '../universities/laurier/campus.json';
import yorkCampus from '../universities/york/campus.json';
import mcmasterCampus from '../universities/mcmaster/campus.json';

const utsgFootprints = JSON.parse(utsgFootprintsJson);
const utscFootprints = JSON.parse(utscFootprintsJson);

export const MAP_WIDTH = 1200;
export const MAP_HEIGHT = 840;
const MAP_PADDING = 26;

function boundsFromFeatures(features, fallback) {
  const coordinates = features.flatMap((feature) => geometryCoordinates(feature.geometry));
  if (!coordinates.length) return fallback;
  const lons = coordinates.map(([lon]) => lon);
  const lats = coordinates.map(([, lat]) => lat);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const lonPad = Math.max((maxLon - minLon) * 0.09, 0.0007);
  const latPad = Math.max((maxLat - minLat) * 0.09, 0.0005);
  return {
    minLon: minLon - lonPad,
    maxLon: maxLon + lonPad,
    minLat: minLat - latPad,
    maxLat: maxLat + latPad,
  };
}

const UTM_FALLBACK = {
  minLon: -79.6755,
  maxLon: -79.6542,
  minLat: 43.5421,
  maxLat: 43.5577,
};

const UTSG_FALLBACK = {
  minLon: -79.4215,
  maxLon: -79.3650,
  minLat: 43.6450,
  maxLat: 43.6825,
};

const UTSC_FALLBACK = {
  minLon: -79.2050,
  maxLon: -79.1650,
  minLat: 43.7720,
  maxLat: 43.7995,
};

const CARLETON_FALLBACK = {
  minLon: -75.705,
  maxLon: -75.688,
  minLat: 45.38,
  maxLat: 45.394,
};

const TMU_FALLBACK = {
  minLon: -79.385,
  maxLon: -79.373,
  minLat: 43.654,
  maxLat: 43.662,
};

const QUEENS_FALLBACK = {
  minLon: -76.502,
  maxLon: -76.49,
  minLat: 44.221,
  maxLat: 44.232,
};

const LAURIER_FALLBACK = {
  minLon: -80.536,
  maxLon: -80.523,
  minLat: 43.47,
  maxLat: 43.479,
};

const YORK_FALLBACK = {
  minLon: -79.515,
  maxLon: -79.493,
  minLat: 43.766,
  maxLat: 43.782,
};

const MCMASTER_FALLBACK = {
  minLon: -79.932,
  maxLon: -79.910,
  minLat: 43.256,
  maxLat: 43.268,
};

const TRI_CAMPUS_REGISTRIES = {
  utsg: utsgRegistry,
  utsc: utscRegistry,
};

const TRI_CAMPUS_FOOTPRINTS = {
  utsg: Array.isArray(utsgFootprints?.features) ? utsgFootprints.features : [],
  utsc: Array.isArray(utscFootprints?.features) ? utscFootprints.features : [],
};

function universityFootprints(dataset) {
  return (dataset?.buildings || [])
    .filter((b) => b.geometry)
    .map((b) => ({
      type: 'Feature',
      id: b.id,
      properties: {
        buildingId: b.id,
        code: b.nativeCodes?.[0] || b.id,
        name: b.name,
      },
      geometry: b.geometry,
    }));
}

function universityBuildings(dataset, campusId) {
  return (dataset?.buildings || []).map((building) => {
    const feature = building.geometry
      ? {
          type: 'Feature',
          id: building.id,
          properties: {
            buildingId: building.id,
            code: building.nativeCodes?.[0] || building.id,
            name: building.name,
          },
          geometry: building.geometry,
        }
      : null;
    const features = feature ? [feature] : [];
    const code = building.nativeCodes?.[0] || building.id.toUpperCase();
    const entrances = (dataset.entrances || []).filter((e) => e.buildingId === building.id);
    return {
      code,
      name: building.name,
      aliases: building.aliases ?? [],
      timetableCodes: building.nativeCodes ?? [],
      campus: campusId,
      source: 'canonical',
      canonicalId: building.id,
      features,
      entranceCount: entrances.length,
      geometryStatus: feature ? 'mapped' : 'unresolved',
    };
  });
}

function universityEntrances(dataset) {
  const buildingById = new Map((dataset?.buildings || []).map((b) => [b.id, b]));
  return (dataset?.entrances || []).map((entrance) => {
    const building = buildingById.get(entrance.buildingId);
    return {
      type: 'Feature',
      id: entrance.id,
      properties: {
        id: entrance.id,
        buildingId: entrance.buildingId,
        buildingCode: building?.nativeCodes?.[0] || entrance.buildingId,
        buildingName: building?.name || entrance.buildingId,
        access: entrance.access,
      },
      geometry: { type: 'Point', coordinates: entrance.coordinate },
    };
  });
}

const CARLETON_FOOTPRINTS = universityFootprints(carletonCampus);
const TMU_FOOTPRINTS = universityFootprints(tmuCampus);
const QUEENS_FOOTPRINTS = universityFootprints(queensCampus);
const LAURIER_FOOTPRINTS = universityFootprints(laurierCampus);
const YORK_FOOTPRINTS = universityFootprints(yorkCampus);
const MCMASTER_FOOTPRINTS = universityFootprints(mcmasterCampus);

function importedBuildingsForCampus(campusId) {
  const registry = TRI_CAMPUS_REGISTRIES[campusId];
  const footprints = TRI_CAMPUS_FOOTPRINTS[campusId] ?? [];
  if (!registry?.buildings) return [];

  const featuresByBuildingId = new Map();
  for (const feature of footprints) {
    const buildingId = feature?.properties?.buildingId ?? feature?.id;
    if (!buildingId) continue;
    const current = featuresByBuildingId.get(buildingId) ?? [];
    current.push(feature);
    featuresByBuildingId.set(buildingId, current);
  }

  return registry.buildings.map((building) => ({
    code: building.code,
    name: building.name,
    aliases: building.aliases ?? [],
    timetableCodes: building.timetableCodes ?? [],
    campus: campusId,
    source: 'canonical',
    canonicalId: building.id,
    features: featuresByBuildingId.get(building.id) ?? [],
    entranceCount: 0,
    geometryStatus: featuresByBuildingId.has(building.id) ? 'mapped' : 'unresolved',
  }));
}

export const UNIVERSITIES = [
  {
    id: 'uoft',
    name: 'University of Toronto',
    shortName: 'U of T',
    defaultCampus: 'utm',
    campuses: [
      { id: 'utm', name: 'Mississauga', shortName: 'UTM' },
      { id: 'utsg', name: 'St. George', shortName: 'UTSG' },
      { id: 'utsc', name: 'Scarborough', shortName: 'UTSC' },
    ],
  },
  {
    id: 'carleton',
    name: 'Carleton University',
    shortName: 'Carleton',
    defaultCampus: 'carleton',
    campuses: [
      { id: 'carleton', name: 'Carleton University', shortName: 'Carleton' },
    ],
  },
  {
    id: 'tmu',
    name: 'Toronto Metropolitan University',
    shortName: 'TMU',
    defaultCampus: 'tmu',
    campuses: [
      { id: 'tmu', name: 'Toronto Metropolitan University', shortName: 'TMU' },
    ],
  },
  {
    id: 'queens',
    name: "Queen's University",
    shortName: "Queen's",
    defaultCampus: 'queens',
    campuses: [
      { id: 'queens', name: "Queen's University", shortName: "Queen's" },
    ],
  },
  {
    id: 'laurier',
    name: 'Wilfrid Laurier University',
    shortName: 'Laurier',
    defaultCampus: 'laurier',
    campuses: [
      { id: 'laurier', name: 'Waterloo Campus', shortName: 'Laurier' },
    ],
  },
  {
    id: 'york',
    name: 'York University',
    shortName: 'York',
    defaultCampus: 'york',
    campuses: [
      { id: 'york', name: 'Keele Campus', shortName: 'York' },
    ],
  },
  {
    id: 'mcmaster',
    name: 'McMaster University',
    shortName: 'McMaster',
    defaultCampus: 'mcmaster',
    campuses: [
      { id: 'mcmaster', name: 'Main Campus', shortName: 'McMaster' },
    ],
  },
];

export const CAMPUSES = {
  utm: {
    id: 'utm',
    universityId: 'uoft',
    shortName: 'UTM',
    name: 'University of Toronto Mississauga',
    bounds: boundsFromFeatures(utmFootprintFeatures, UTM_FALLBACK),
    tileZoom: 17,
  },
  utsg: {
    id: 'utsg',
    universityId: 'uoft',
    shortName: 'UTSG',
    name: 'University of Toronto St. George',
    bounds: boundsFromFeatures(TRI_CAMPUS_FOOTPRINTS.utsg, UTSG_FALLBACK),
    tileZoom: 16,
  },
  utsc: {
    id: 'utsc',
    universityId: 'uoft',
    shortName: 'UTSC',
    name: 'University of Toronto Scarborough',
    bounds: boundsFromFeatures(TRI_CAMPUS_FOOTPRINTS.utsc, UTSC_FALLBACK),
    tileZoom: 16,
  },
  carleton: {
    id: 'carleton',
    universityId: 'carleton',
    shortName: 'Carleton',
    name: 'Carleton University',
    bounds: boundsFromFeatures(CARLETON_FOOTPRINTS, CARLETON_FALLBACK),
    tileZoom: 16,
  },
  tmu: {
    id: 'tmu',
    universityId: 'tmu',
    shortName: 'TMU',
    name: 'Toronto Metropolitan University',
    bounds: boundsFromFeatures(TMU_FOOTPRINTS, TMU_FALLBACK),
    tileZoom: 17,
  },
  queens: {
    id: 'queens',
    universityId: 'queens',
    shortName: "Queen's",
    name: "Queen's University",
    bounds: boundsFromFeatures(QUEENS_FOOTPRINTS, QUEENS_FALLBACK),
    tileZoom: 16,
  },
  laurier: {
    id: 'laurier',
    universityId: 'laurier',
    shortName: 'Laurier',
    name: 'Wilfrid Laurier University',
    bounds: boundsFromFeatures(LAURIER_FOOTPRINTS, LAURIER_FALLBACK),
    tileZoom: 17,
  },
  york: {
    id: 'york',
    universityId: 'york',
    shortName: 'York',
    name: 'York University (Keele Campus)',
    bounds: boundsFromFeatures(YORK_FOOTPRINTS, YORK_FALLBACK),
    tileZoom: 16,
  },
  mcmaster: {
    id: 'mcmaster',
    universityId: 'mcmaster',
    shortName: 'McMaster',
    name: 'McMaster University',
    bounds: boundsFromFeatures(MCMASTER_FOOTPRINTS, MCMASTER_FALLBACK),
    tileZoom: 16,
  },
};

export const CAMPUS_IDS = Object.keys(CAMPUSES);

export function campusFromQuery() {
  const params = new URLSearchParams(window.location.search);
  const requestedCampus = params.get('campus')?.toLowerCase();
  if (requestedCampus && CAMPUSES[requestedCampus]) {
    return requestedCampus;
  }
  const requestedUni = params.get('university')?.toLowerCase();
  if (requestedUni) {
    const uni = UNIVERSITIES.find((u) => u.id === requestedUni);
    if (uni) return uni.defaultCampus;
  }
  return 'utm';
}

export function universityForCampus(campusId) {
  return CAMPUSES[campusId]?.universityId || 'uoft';
}

export function canonicalBuildingsForCampus(campusId) {
  if (campusId === 'utm') {
    return utmBuildings.map((building) => ({ ...building, source: 'canonical', campus: 'utm' }));
  }
  if (campusId === 'utsg' || campusId === 'utsc') {
    return importedBuildingsForCampus(campusId);
  }
  if (campusId === 'carleton') return universityBuildings(carletonCampus, 'carleton');
  if (campusId === 'tmu') return universityBuildings(tmuCampus, 'tmu');
  if (campusId === 'queens') return universityBuildings(queensCampus, 'queens');
  if (campusId === 'laurier') return universityBuildings(laurierCampus, 'laurier');
  if (campusId === 'york' || campusId === 'keele') return universityBuildings(yorkCampus, 'york');
  if (campusId === 'mcmaster') return universityBuildings(mcmasterCampus, 'mcmaster');
  return [];
}

export function canonicalFootprintsForCampus(campusId) {
  if (campusId === 'utm') return utmFootprintFeatures;
  if (campusId === 'utsg' || campusId === 'utsc') return TRI_CAMPUS_FOOTPRINTS[campusId] ?? [];
  if (campusId === 'carleton') return CARLETON_FOOTPRINTS;
  if (campusId === 'tmu') return TMU_FOOTPRINTS;
  if (campusId === 'queens') return QUEENS_FOOTPRINTS;
  if (campusId === 'laurier') return LAURIER_FOOTPRINTS;
  if (campusId === 'york' || campusId === 'keele') return YORK_FOOTPRINTS;
  if (campusId === 'mcmaster') return MCMASTER_FOOTPRINTS;
  return [];
}

export function canonicalEntrancesForCampus(campusId) {
  if (campusId === 'utm') return utmEntranceFeatures;
  if (campusId === 'carleton') return universityEntrances(carletonCampus);
  if (campusId === 'tmu') return universityEntrances(tmuCampus);
  if (campusId === 'queens') return universityEntrances(queensCampus);
  if (campusId === 'laurier') return universityEntrances(laurierCampus);
  if (campusId === 'york' || campusId === 'keele') return universityEntrances(yorkCampus);
  if (campusId === 'mcmaster') return universityEntrances(mcmasterCampus);
  return [];
}

export function createCampusProjection(campusId) {
  const campus = CAMPUSES[campusId] ?? CAMPUSES.utm;
  const { bounds } = campus;
  const middleLatitude = (bounds.minLat + bounds.maxLat) / 2;
  const longitudeScale = Math.cos((middleLatitude * Math.PI) / 180);
  const projectedWidth = (bounds.maxLon - bounds.minLon) * longitudeScale;
  const projectedHeight = bounds.maxLat - bounds.minLat;
  const canvasWidth = MAP_WIDTH - MAP_PADDING * 2;
  const canvasHeight = MAP_HEIGHT - MAP_PADDING * 2;
  const campusAspect = projectedWidth / projectedHeight;
  const canvasAspect = canvasWidth / canvasHeight;
  const contentWidth = campusAspect > canvasAspect ? canvasWidth : canvasHeight * campusAspect;
  const contentHeight = campusAspect > canvasAspect ? canvasWidth / campusAspect : canvasHeight;
  const originX = (MAP_WIDTH - contentWidth) / 2;
  const originY = (MAP_HEIGHT - contentHeight) / 2;

  function project([longitude, latitude]) {
    const xRatio = ((longitude - bounds.minLon) * longitudeScale) / projectedWidth;
    const yRatio = (bounds.maxLat - latitude) / projectedHeight;
    return [originX + xRatio * contentWidth, originY + yRatio * contentHeight];
  }

  function unproject([x, y]) {
    const xRatio = (x - originX) / contentWidth;
    const yRatio = (y - originY) / contentHeight;
    return [
      bounds.minLon + (xRatio * projectedWidth) / longitudeScale,
      bounds.maxLat - yRatio * projectedHeight,
    ];
  }

  return { campus, project, unproject, originX, originY, contentWidth, contentHeight };
}

function ringPath(ring, project) {
  return ring
    .map((coordinate, index) => {
      const [x, y] = project(coordinate);
      return `${index === 0 ? 'M' : 'L'}${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(' ') + ' Z';
}

export function geometryPath(geometry, project) {
  if (!geometry) return '';
  if (geometry.type === 'Polygon') return geometry.coordinates.map((ring) => ringPath(ring, project)).join(' ');
  if (geometry.type === 'MultiPolygon') {
    return geometry.coordinates.flatMap((polygon) => polygon.map((ring) => ringPath(ring, project))).join(' ');
  }
  if (geometry.type === 'LineString') {
    return geometry.coordinates
      .map((coordinate, index) => {
        const [x, y] = project(coordinate);
        return `${index === 0 ? 'M' : 'L'}${x.toFixed(2)} ${y.toFixed(2)}`;
      })
      .join(' ');
  }
  return '';
}

export function geometryBounds(geometry, project, paddingFactor = 0.75) {
  let coordinates = [];
  if (geometry?.type === 'Polygon') coordinates = geometry.coordinates.flat();
  if (geometry?.type === 'MultiPolygon') coordinates = geometry.coordinates.flat(2);
  if (geometry?.type === 'LineString') coordinates = geometry.coordinates;
  if (geometry?.type === 'Point') coordinates = [geometry.coordinates];
  if (!coordinates.length) return { x: 0, y: 0, width: MAP_WIDTH, height: MAP_HEIGHT };
  const points = coordinates.map(project);
  const xs = points.map(([x]) => x);
  const ys = points.map(([, y]) => y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const rawWidth = Math.max(80, maxX - minX);
  const rawHeight = Math.max(80, maxY - minY);
  const pad = Math.max(rawWidth, rawHeight) * paddingFactor;
  return {
    x: Math.max(0, minX - pad),
    y: Math.max(0, minY - pad),
    width: Math.min(MAP_WIDTH, rawWidth + pad * 2),
    height: Math.min(MAP_HEIGHT, rawHeight + pad * 2),
  };
}

export function featureCenter(feature) {
  const coordinates = geometryCoordinates(feature?.geometry);
  if (!coordinates.length) return null;
  const sum = coordinates.reduce(
    (acc, [lon, lat]) => [acc[0] + lon, acc[1] + lat],
    [0, 0],
  );
  return [sum[0] / coordinates.length, sum[1] / coordinates.length];
}

function lonToTileX(lon, zoom) {
  return ((lon + 180) / 360) * 2 ** zoom;
}

function latToTileY(lat, zoom) {
  const radians = (lat * Math.PI) / 180;
  return (
    (1 - Math.log(Math.tan(radians) + 1 / Math.cos(radians)) / Math.PI) / 2
  ) * 2 ** zoom;
}

function tileXToLon(x, zoom) {
  return (x / 2 ** zoom) * 360 - 180;
}

function tileYToLat(y, zoom) {
  const n = Math.PI - (2 * Math.PI * y) / 2 ** zoom;
  return (180 / Math.PI) * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)));
}

export function tilesForCampus(campusId, project) {
  const campus = CAMPUSES[campusId] ?? CAMPUSES.utm;
  const zoom = campus.tileZoom;
  const { minLon, maxLon, minLat, maxLat } = campus.bounds;
  const minX = Math.floor(lonToTileX(minLon, zoom));
  const maxX = Math.floor(lonToTileX(maxLon, zoom));
  const minY = Math.floor(latToTileY(maxLat, zoom));
  const maxY = Math.floor(latToTileY(minLat, zoom));
  const tiles = [];
  for (let x = minX; x <= maxX; x += 1) {
    for (let y = minY; y <= maxY; y += 1) {
      const west = tileXToLon(x, zoom);
      const east = tileXToLon(x + 1, zoom);
      const north = tileYToLat(y, zoom);
      const south = tileYToLat(y + 1, zoom);
      const [left, top] = project([west, north]);
      const [right, bottom] = project([east, south]);
      tiles.push({
        key: `${zoom}/${x}/${y}`,
        href: `https://tile.openstreetmap.org/${zoom}/${x}/${y}.png`,
        x: left,
        y: top,
        width: right - left,
        height: bottom - top,
      });
    }
  }
  return tiles;
}

export function makeId(prefix = 'draft') {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export { metersBetween, todayLocalDate };
