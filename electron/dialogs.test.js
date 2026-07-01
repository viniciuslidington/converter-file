const assert = require("node:assert/strict");
const test = require("node:test");

const { dialogParent, pickFiles, pickFolder } = require("./dialogs");

function dialogDeps(result) {
  const parent = {
    focused: false,
    restored: false,
    isMinimized: () => true,
    restore() {
      this.restored = true;
    },
    focus() {
      this.focused = true;
    },
  };
  const calls = [];
  return {
    parent,
    calls,
    deps: {
      app: {
        focused: false,
        focus(options) {
          this.focused = options;
        },
      },
      BrowserWindow: {
        fromWebContents(sender) {
          return sender === "web-contents" ? parent : null;
        },
      },
      dialog: {
        async showOpenDialog(...args) {
          calls.push(args);
          return result;
        },
      },
    },
  };
}

test("dialogParent resolves the window that sent the IPC event", () => {
  const { parent, deps } = dialogDeps({ canceled: true, filePaths: [] });

  assert.equal(dialogParent(deps.BrowserWindow, { sender: "web-contents" }), parent);
  assert.equal(dialogParent(deps.BrowserWindow, { sender: "other" }), null);
  assert.equal(dialogParent(deps.BrowserWindow, null), null);
});

test("pickFiles focuses the sender window and opens a modal file picker", async () => {
  const context = dialogDeps({ canceled: false, filePaths: ["/tmp/a.mp4", "/tmp/b.wav"] });

  const paths = await pickFiles(context.deps, { sender: "web-contents" });

  assert.deepEqual(paths, ["/tmp/a.mp4", "/tmp/b.wav"]);
  assert.equal(context.parent.restored, true);
  assert.equal(context.parent.focused, true);
  assert.deepEqual(context.deps.app.focused, { steal: true });
  assert.equal(context.calls.length, 1);
  assert.equal(context.calls[0][0], context.parent);
  assert.deepEqual(context.calls[0][1], {
    properties: ["openFile", "multiSelections"],
    title: "Escolha arquivo(s) para converter",
  });
});

test("pickFolder returns an empty string when the picker is canceled", async () => {
  const context = dialogDeps({ canceled: true, filePaths: [] });

  const folder = await pickFolder(context.deps, { sender: "web-contents" });

  assert.equal(folder, "");
});

test("pickFolder falls back to a non-modal dialog when no parent is available", async () => {
  const context = dialogDeps({ canceled: false, filePaths: ["/tmp/output"] });

  const folder = await pickFolder(context.deps, { sender: "other" });

  assert.equal(folder, "/tmp/output");
  assert.equal(context.calls.length, 1);
  assert.deepEqual(context.calls[0], [{
    properties: ["openDirectory"],
    title: "Escolha a pasta padrão de saída",
  }]);
});
