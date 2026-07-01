function dialogParent(BrowserWindow, event) {
  if (!event?.sender || !BrowserWindow?.fromWebContents) {
    return null;
  }
  return BrowserWindow.fromWebContents(event.sender) || null;
}

function focusDialogParent(app, parent) {
  if (parent?.isMinimized?.()) {
    parent.restore();
  }
  parent?.focus?.();
  app?.focus?.({ steal: true });
}

async function pickFiles({ app, BrowserWindow, dialog }, event) {
  const parent = dialogParent(BrowserWindow, event);
  focusDialogParent(app, parent);
  const options = {
    properties: ["openFile", "multiSelections"],
    title: "Escolha arquivo(s) para converter",
  };
  const result = parent
    ? await dialog.showOpenDialog(parent, options)
    : await dialog.showOpenDialog(options);
  return result.canceled ? [] : result.filePaths;
}

async function pickFolder({ app, BrowserWindow, dialog }, event) {
  const parent = dialogParent(BrowserWindow, event);
  focusDialogParent(app, parent);
  const options = {
    properties: ["openDirectory"],
    title: "Escolha a pasta padrão de saída",
  };
  const result = parent
    ? await dialog.showOpenDialog(parent, options)
    : await dialog.showOpenDialog(options);
  return result.canceled ? "" : result.filePaths[0];
}

module.exports = {
  dialogParent,
  pickFiles,
  pickFolder,
};
