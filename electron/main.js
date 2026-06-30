const { app, BrowserWindow, dialog, ipcMain, shell } = require("electron");
const { spawn, spawnSync } = require("node:child_process");
const path = require("node:path");

const projectRoot = path.join(__dirname, "..");
const pythonExecutable = process.env.CONVERTER_FILE_PYTHON || "python3.11";

function createWindow() {
  const win = new BrowserWindow({
    width: 1180,
    height: 760,
    minWidth: 980,
    minHeight: 640,
    title: "Converter File",
    backgroundColor: "#f6f7f9",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.loadFile(path.join(__dirname, "renderer", "index.html"));
}

app.whenReady().then(() => {
  registerIpcHandlers();
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

function registerIpcHandlers() {
  ipcMain.handle("files:pick", async () => {
    const result = await dialog.showOpenDialog({
      properties: ["openFile", "multiSelections"],
      title: "Escolha arquivo(s) para converter",
    });
    return result.canceled ? [] : result.filePaths;
  });

  ipcMain.handle("api:inspect", (_event, payload) => runApi("inspect", payload));
  ipcMain.handle("api:targets", (_event, payload) => runApi("targets", payload));
  ipcMain.handle("api:estimate", (_event, payload) => runApi("estimate", payload));
  ipcMain.handle("api:validate", (_event, payload) => runApi("validate", payload));
  ipcMain.handle("api:convert", (_event, payload) => runApi("convert", payload));
  ipcMain.handle("deps:check", () => checkDependencies());
  ipcMain.handle("deps:update", () => updateDependencies());
  ipcMain.handle("shell:show-item", (_event, filePath) => shell.showItemInFolder(filePath));
  ipcMain.handle("shell:open-path", (_event, filePath) => shell.openPath(filePath));
}

function runApi(command, payload) {
  return new Promise((resolve) => {
    const child = spawn(
      pythonExecutable,
      ["-m", "converter_file.api", command],
      {
        cwd: projectRoot,
        stdio: ["pipe", "pipe", "pipe"],
      }
    );

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", (error) => {
      resolve({
        ok: false,
        error: `Não foi possível iniciar ${pythonExecutable}: ${error.message}`,
      });
    });
    child.on("close", () => {
      try {
        const parsed = JSON.parse(stdout || "{}");
        if (!parsed.ok && stderr.trim()) {
          parsed.stderr = stderr.trim();
        }
        resolve(parsed);
      } catch (error) {
        resolve({
          ok: false,
          error: "Resposta inválida do backend Python.",
          stdout,
          stderr,
        });
      }
    });

    child.stdin.end(JSON.stringify(payload || {}));
  });
}

function checkDependencies() {
  const dependencies = [
    { id: "python", command: pythonExecutable, label: "Python 3.11" },
    { id: "ffmpeg", command: "ffmpeg", label: "ffmpeg" },
    { id: "ffprobe", command: "ffprobe", label: "ffprobe" },
    { id: "pandoc", command: "pandoc", label: "pandoc" },
    { id: "pdftotext", command: "pdftotext", label: "pdftotext" },
    { id: "pdftoppm", command: "pdftoppm", label: "pdftoppm" },
    { id: "pdftohtml", command: "pdftohtml", label: "pdftohtml" },
    { id: "qpdf", command: "qpdf", label: "qpdf" },
    { id: "ocrmypdf", command: "ocrmypdf", label: "ocrmypdf" },
  ];

  return dependencies.map((dependency) => {
    const result = spawnSync(dependency.command, ["--version"], {
      encoding: "utf8",
      timeout: 3000,
    });

    return {
      ...dependency,
      installed: result.status === 0 || Boolean(result.stdout || result.stderr),
      version: firstLine(result.stdout || result.stderr),
    };
  });
}

function updateDependencies() {
  return new Promise((resolve) => {
    const isWindows = process.platform === "win32";
    const script = path.join(projectRoot, isWindows ? "install.ps1" : "install.sh");
    const command = isWindows ? "powershell.exe" : "bash";
    const args = isWindows
      ? ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script]
      : [script];
    const child = spawn(command, args, {
      cwd: projectRoot,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", (error) => {
      resolve({
        ok: false,
        error: `Não foi possível iniciar o script de atualização: ${error.message}`,
      });
    });
    child.on("close", (code) => {
      resolve({
        ok: code === 0,
        code,
        stdout,
        stderr,
        error: code === 0 ? undefined : "O script de atualização terminou com erro.",
      });
    });
  });
}

function firstLine(value) {
  return String(value || "").split(/\r?\n/).find(Boolean) || "";
}
