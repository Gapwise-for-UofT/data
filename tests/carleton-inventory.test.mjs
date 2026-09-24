import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");

async function readJson(path) {
  return JSON.parse(await readFile(resolve(root, path), "utf8"));
}

test("Carleton official campus inventory is normalized and internally consistent", async () => {
  const inventory = await readJson("data/carleton/sources/official-buildings.json");
  const aliases = await readJson("data/carleton/sources/reconciliation-aliases.json");

  assert.equal(inventory.sourceId, "carleton-campus-map-2025");
  assert.equal(inventory.records.length, 51);

  const codes = inventory.records.map((record) => record.code);
  assert.equal(new Set(codes).size, codes.length, "current Carleton building codes must be unique");

  const knownCodes = new Set(codes);
  for (const record of inventory.records) {
    assert.match(record.code, /^[A-Z]{2}$/);
    assert.ok(record.name && typeof record.name === "string");
    assert.ok(["academic", "facility", "residence"].includes(record.category));
    assert.equal(record.status, "active");
    assert.equal(
      record.timetableCode,
      record.code,
      `${record.code} must use the current official map code as its timetable identity`,
    );
    assert.ok(Array.isArray(record.aliases));
  }

  for (const [name, target] of Object.entries(aliases.names ?? {})) {
    assert.ok(name.trim(), "alias names must not be blank");
    assert.ok(knownCodes.has(target), `alias ${name} targets unknown current code ${target}`);
  }

  for (const [legacyCode, target] of Object.entries(aliases.legacyCodes ?? {})) {
    assert.match(legacyCode, /^[A-Z]{2}$/);
    assert.ok(knownCodes.has(target), `legacy code ${legacyCode} targets unknown code ${target}`);
    assert.notEqual(
      legacyCode,
      target,
      `legacy code ${legacyCode} should not duplicate the current code`,
    );
  }

  assert.ok(aliases.legacyCodeEvidence?.sourceId);
  assert.ok(aliases.legacyCodeEvidence?.sourceUrl);
  assert.match(
    aliases.legacyCodeEvidence?.note ?? "",
    /not treated as current timetable codes/i,
  );
});

test("Carleton residence classification covers the current residence buildings", async () => {
  const inventory = await readJson("data/carleton/sources/official-buildings.json");
  const residences = new Set(
    inventory.records
      .filter((record) => record.category === "residence")
      .map((record) => record.code),
  );

  for (const code of ["DH", "FR", "GH", "GR", "LE", "LH", "LX", "PH", "RH", "RI", "RU", "SH"]) {
    assert.ok(residences.has(code), `${code} should be classified as a Carleton residence`);
  }
});
