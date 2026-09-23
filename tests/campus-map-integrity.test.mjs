import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const readJson = async (path) => JSON.parse(await readFile(path, "utf8"));

test("Robarts Common has one current source-backed canonical footprint", async () => {
  const [registry, footprints, aliases] = await Promise.all([
    readJson("data/utsg/buildings.json"),
    readJson("data/utsg/buildings.geojson"),
    readJson("data/utsg/sources/reconciliation-aliases.json"),
  ]);

  const records = registry.buildings.filter(
    (building) => building.code === "006C" || building.name === "Robarts Common",
  );
  assert.equal(records.length, 1);
  assert.equal(records[0].campus, "utsg");
  assert.deepEqual(records[0].aliases, ["Robarts Common", "Robarts Commons"]);
  assert.equal(aliases.geometryRefs["006C"].ref, "way/1540353363");

  const commonFootprints = footprints.features.filter(
    (feature) => feature.properties?.buildingCode === "006C",
  );
  assert.equal(commonFootprints.length, 1);
  assert.equal(commonFootprints[0].properties.name, "Robarts Common");
  assert.equal(commonFootprints[0].properties.geometrySourceRef, "way/1540353363");

  const library = footprints.features.find(
    (feature) => feature.properties?.buildingId === "utsg:facility:006",
  );
  assert.ok(library, "Robarts Library footprint must remain present");
  assert.notDeepEqual(commonFootprints[0].geometry, library.geometry);
});

test("IB north emergency door stays exact but is not an ordinary routing endpoint", async () => {
  const [entrances, audit, nodes, edges] = await Promise.all([
    readJson("data/utm/entrances.geojson"),
    readJson("data/utm/generated/entrance-audit.geojson"),
    readJson("data/utm/outdoor-nodes.geojson"),
    readJson("data/utm/outdoor-edges.json"),
  ]);

  const entrance = entrances.features.find((feature) => feature.id === "ib-2383651237");
  assert.ok(entrance);
  assert.deepEqual(entrance.geometry.coordinates, [-79.664056, 43.5518062]);
  assert.equal(entrance.properties.osmNodeId, 2383651237);
  assert.equal(entrance.properties.access, "emergency_only");
  assert.notEqual(entrance.properties.preferredForRouting, true);

  const auditRecord = audit.features.find((feature) => feature.id === entrance.id);
  assert.equal(auditRecord?.properties.routability, "non_routable");
  assert.equal(auditRecord?.properties.publicAccess, "restricted");

  const nodeId = "osm-node-2383651237";
  const node = nodes.features.find((feature) => feature.id === nodeId);
  assert.ok(node);
  assert.deepEqual(node.geometry.coordinates, entrance.geometry.coordinates);
  assert.ok(
    edges.edges.some((edge) => edge.from === nodeId || edge.to === nodeId),
    "the physical door must retain its reviewed pedestrian-graph connection",
  );

  const ibEntrances = entrances.features.filter(
    (feature) => feature.properties.buildingCode === "IB",
  );
  assert.equal(
    ibEntrances.filter((feature) => feature.id === entrance.id).length,
    1,
  );
  assert.ok(
    ibEntrances.some(
      (feature) =>
        feature.id !== entrance.id &&
        feature.properties.access !== "restricted" &&
        feature.properties.access !== "emergency_only",
    ),
    "IB must retain at least one ordinary entrance",
  );
});
