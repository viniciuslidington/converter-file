const { contextBridge, ipcRenderer } = require("electron");

function createJobId() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `job-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

contextBridge.exposeInMainWorld("converterFile", {
  pickFiles: () => ipcRenderer.invoke("files:pick"),
  pickFolder: () => ipcRenderer.invoke("folders:pick"),
  inspect: (payload) => ipcRenderer.invoke("api:inspect", payload),
  targets: (payload) => ipcRenderer.invoke("api:targets", payload),
  estimate: (payload) => ipcRenderer.invoke("api:estimate", payload),
  validate: (payload) => ipcRenderer.invoke("api:validate", payload),
  convert: (payload) => ipcRenderer.invoke("api:convert", payload),
  convertWithProgress: (payload, onProgress, providedJobId) => {
    const jobId = providedJobId || createJobId();
    const channel = `conversion:progress:${jobId}`;
    const listener = (_event, progress) => {
      if (typeof onProgress === "function") {
        onProgress(progress);
      }
    };

    ipcRenderer.on(channel, listener);
    return ipcRenderer
      .invoke("api:convert-progress", { jobId, payload })
      .finally(() => ipcRenderer.removeListener(channel, listener));
  },
  cancelConversion: (jobId) => ipcRenderer.invoke("api:cancel-conversion", jobId),
  checkDependencies: () => ipcRenderer.invoke("deps:check"),
  updateDependencies: () => ipcRenderer.invoke("deps:update"),
  loadStore: () => ipcRenderer.invoke("store:load"),
  writeStore: (name, value) => ipcRenderer.invoke("store:write", { name, value }),
  updateSettings: (patch) => ipcRenderer.invoke("settings:update", patch),
  addHistory: (entry) => ipcRenderer.invoke("history:add", entry),
  addPreset: (preset) => ipcRenderer.invoke("presets:add", preset),
  updatePreset: (id, patch) => ipcRenderer.invoke("presets:update", { id, patch }),
  deletePreset: (presetId) => ipcRenderer.invoke("presets:delete", presetId),
  saveQueue: (queue) => ipcRenderer.invoke("queue:save", queue),
  showItemInFolder: (filePath) => ipcRenderer.invoke("shell:show-item", filePath),
  openPath: (filePath) => ipcRenderer.invoke("shell:open-path", filePath),
});
