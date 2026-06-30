const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("converterFile", {
  pickFiles: () => ipcRenderer.invoke("files:pick"),
  inspect: (payload) => ipcRenderer.invoke("api:inspect", payload),
  targets: (payload) => ipcRenderer.invoke("api:targets", payload),
  estimate: (payload) => ipcRenderer.invoke("api:estimate", payload),
  validate: (payload) => ipcRenderer.invoke("api:validate", payload),
  convert: (payload) => ipcRenderer.invoke("api:convert", payload),
  checkDependencies: () => ipcRenderer.invoke("deps:check"),
  updateDependencies: () => ipcRenderer.invoke("deps:update"),
  showItemInFolder: (filePath) => ipcRenderer.invoke("shell:show-item", filePath),
  openPath: (filePath) => ipcRenderer.invoke("shell:open-path", filePath),
});
