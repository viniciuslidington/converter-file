const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const {
  configureStorage,
  getAppData,
  readStore,
  updateStore,
  writeStore,
} = require("./storage");

function configureTempStorage() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "converter-file-storage-"));
  configureStorage(dir);
  return dir;
}

test("storage returns defaults when files do not exist", () => {
  configureTempStorage();

  const data = getAppData();

  assert.equal(data.settings.maxConcurrentJobs, 1);
  assert.equal(data.settings.showDependencyWarnings, true);
  assert.deepEqual(data.history, []);
  assert.deepEqual(data.presets, []);
  assert.deepEqual(data.queue, []);
});

test("storage persists and reloads store data", () => {
  configureTempStorage();

  writeStore("presets", [{ id: "preset-1", name: "Audio" }]);

  assert.deepEqual(readStore("presets"), [{ id: "preset-1", name: "Audio" }]);
});

test("settings are merged with new defaults", () => {
  const dir = configureTempStorage();
  fs.writeFileSync(path.join(dir, "settings.json"), JSON.stringify({ theme: "dark" }));

  const settings = readStore("settings");

  assert.equal(settings.theme, "dark");
  assert.equal(settings.overwriteExistingFiles, false);
  assert.equal(settings.maxConcurrentJobs, 1);
});

test("updateStore writes derived value", () => {
  configureTempStorage();

  const history = updateStore("history", (entries) => [{ id: "entry-1" }, ...entries]);

  assert.deepEqual(history, [{ id: "entry-1" }]);
  assert.deepEqual(readStore("history"), [{ id: "entry-1" }]);
});

test("invalid stores are rejected", () => {
  configureTempStorage();

  assert.throws(() => readStore("../outside"), /Store inválida/);
  assert.throws(() => writeStore("unknown", []), /Store inválida/);
});
