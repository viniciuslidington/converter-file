const fs = require("node:fs");
const path = require("node:path");

const defaults = {
  settings: {
    defaultOutputDirectory: "",
    overwriteExistingFiles: false,
    openOutputAfterConversion: false,
    showDependencyWarnings: true,
    theme: "system",
    maxConcurrentJobs: 1,
  },
  history: [],
  presets: [],
  queue: [],
};

const allowedStores = new Set(Object.keys(defaults));

let storageDir = null;

function configureStorage(baseDir) {
  storageDir = baseDir;
  fs.mkdirSync(storageDir, { recursive: true });
}

function readStore(name) {
  ensureConfigured();
  ensureAllowedStore(name);
  const fallback = clone(defaults[name]);
  const filePath = storePath(name);
  if (!fs.existsSync(filePath)) {
    return fallback;
  }

  try {
    const parsed = JSON.parse(fs.readFileSync(filePath, "utf8"));
    return mergeDefault(name, parsed);
  } catch (_error) {
    return fallback;
  }
}

function writeStore(name, value) {
  ensureConfigured();
  ensureAllowedStore(name);
  const filePath = storePath(name);
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`);
  return value;
}

function getAppData() {
  return {
    settings: readStore("settings"),
    history: readStore("history"),
    presets: readStore("presets"),
    queue: readStore("queue"),
  };
}

function updateStore(name, updater) {
  const current = readStore(name);
  const next = updater(current);
  return writeStore(name, next);
}

function storePath(name) {
  ensureAllowedStore(name);
  return path.join(storageDir, `${name}.json`);
}

function ensureConfigured() {
  if (!storageDir) {
    throw new Error("Storage não configurado.");
  }
}

function mergeDefault(name, value) {
  if (name === "settings") {
    return { ...clone(defaults.settings), ...(value && typeof value === "object" ? value : {}) };
  }
  return Array.isArray(value) ? value : clone(defaults[name]);
}

function ensureAllowedStore(name) {
  if (!allowedStores.has(name)) {
    throw new Error(`Store inválida: ${name}`);
  }
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

module.exports = {
  configureStorage,
  getAppData,
  readStore,
  updateStore,
  writeStore,
};
