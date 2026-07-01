const { app, BrowserWindow, dialog, ipcMain, shell } = require("electron");
const { spawn, spawnSync } = require("node:child_process");
const path = require("node:path");
const {
  configureStorage,
  getAppData,
  readStore,
  updateStore,
  writeStore,
} = require("./storage");

const projectRoot = path.join(__dirname, "..");
const pythonExecutable = process.env.CONVERTER_FILE_PYTHON || "python3.11";
const activeConversions = new Map();
const toolEnv = {
  ...process.env,
  PATH: [
    "/opt/homebrew/bin",
    "/usr/local/bin",
    "/usr/bin",
    "/bin",
    "/usr/sbin",
    "/sbin",
    process.env.PATH || "",
  ].join(":"),
};

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
  configureStorage(path.join(app.getPath("userData"), "data"));
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
  ipcMain.handle("folders:pick", async () => {
    const result = await dialog.showOpenDialog({
      properties: ["openDirectory"],
      title: "Escolha a pasta padrão de saída",
    });
    return result.canceled ? "" : result.filePaths[0];
  });

  ipcMain.handle("api:inspect", (_event, payload) => runApi("inspect", payload));
  ipcMain.handle("api:targets", (_event, payload) => runApi("targets", payload));
  ipcMain.handle("api:estimate", (_event, payload) => runApi("estimate", payload));
  ipcMain.handle("api:validate", (_event, payload) => runApi("validate", payload));
  ipcMain.handle("api:convert", (_event, payload) => runApi("convert", payload));
  ipcMain.handle("api:convert-progress", (event, payload) => runApiWithProgress(event, payload));
  ipcMain.handle("api:cancel-conversion", (_event, jobId) => cancelConversion(jobId));
  ipcMain.handle("deps:check", () => checkDependencies());
  ipcMain.handle("deps:update", () => updateDependencies());
  ipcMain.handle("store:load", () => getAppData());
  ipcMain.handle("store:write", (_event, payload) => {
    const { name, value } = payload || {};
    return writeStore(name, value);
  });
  ipcMain.handle("settings:update", (_event, patch) => {
    return updateStore("settings", (settings) => ({ ...settings, ...(patch || {}) }));
  });
  ipcMain.handle("history:add", (_event, entry) => {
    return updateStore("history", (history) => [entry, ...history].slice(0, 500));
  });
  ipcMain.handle("presets:add", (_event, preset) => {
    return updateStore("presets", (presets) => [preset, ...presets]);
  });
  ipcMain.handle("presets:update", (_event, payload) => {
    const { id, patch } = payload || {};
    return updateStore("presets", (presets) => presets.map((preset) => {
      if (preset.id !== id) {
        return preset;
      }
      return { ...preset, ...(patch || {}), updatedAt: new Date().toISOString() };
    }));
  });
  ipcMain.handle("presets:delete", (_event, presetId) => {
    return updateStore("presets", (presets) => presets.filter((preset) => preset.id !== presetId));
  });
  ipcMain.handle("queue:save", (_event, queue) => writeStore("queue", queue || []));
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
        env: toolEnv,
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

function runApiWithProgress(event, payload) {
  const jobId = payload?.jobId;
  const jobPayload = payload?.payload || {};
  const progressChannel = `conversion:progress:${jobId}`;
  const conversion = { child: null, cancelled: false };

  return new Promise((resolve) => {
    const child = spawn(
      pythonExecutable,
      ["-m", "converter_file.api", "convert", "--progress"],
      {
        cwd: projectRoot,
        detached: process.platform !== "win32",
        env: toolEnv,
        stdio: ["pipe", "pipe", "pipe"],
      }
    );
    conversion.child = child;
    if (jobId) {
      activeConversions.set(jobId, conversion);
    }

    let stdout = "";
    let stderr = "";
    let stderrBuffer = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderrBuffer += chunk.toString();
      const lines = stderrBuffer.split(/\r?\n/);
      stderrBuffer = lines.pop() || "";

      for (const line of lines) {
        const eventPayload = parseProgressLine(line);
        if (eventPayload && jobId) {
          event.sender.send(progressChannel, eventPayload);
        } else if (line.trim()) {
          stderr += `${line}\n`;
        }
      }
    });
    child.on("error", (error) => {
      resolve({
        ok: false,
        error: `Não foi possível iniciar ${pythonExecutable}: ${error.message}`,
      });
    });
    child.on("close", () => {
      if (jobId) {
        activeConversions.delete(jobId);
      }
      if (stderrBuffer.trim()) {
        const eventPayload = parseProgressLine(stderrBuffer);
        if (eventPayload && jobId) {
          event.sender.send(progressChannel, eventPayload);
        } else {
          stderr += stderrBuffer;
        }
      }

      try {
        if (conversion.cancelled) {
          resolve({
            ok: false,
            cancelled: true,
            error: "Conversão cancelada.",
          });
          return;
        }
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

    child.stdin.end(JSON.stringify(jobPayload));
  });
}

function cancelConversion(jobId) {
  const conversion = activeConversions.get(jobId);
  if (!conversion || !conversion.child) {
    return { ok: false, error: "Conversão não encontrada ou já finalizada." };
  }
  conversion.cancelled = true;
  terminateProcessTree(conversion.child);
  return { ok: true };
}

function terminateProcessTree(child) {
  if (process.platform === "win32") {
    spawn("taskkill", ["/pid", String(child.pid), "/t", "/f"]);
    return;
  }

  try {
    process.kill(-child.pid, "SIGTERM");
  } catch (_error) {
    child.kill("SIGTERM");
  }
}

function parseProgressLine(line) {
  if (!line.startsWith("__PROGRESS__")) {
    return null;
  }
  try {
    return JSON.parse(line.slice("__PROGRESS__".length));
  } catch (_error) {
    return null;
  }
}

function checkDependencies() {
  const dependencies = [
    { id: "python", command: pythonExecutable, label: "Python 3.11" },
    { id: "ffmpeg", command: "ffmpeg", args: ["-version"], label: "ffmpeg" },
    { id: "ffprobe", command: "ffprobe", args: ["-version"], label: "ffprobe" },
    { id: "pandoc", command: "pandoc", label: "pandoc" },
    { id: "pdftotext", command: "pdftotext", args: ["-v"], label: "pdftotext" },
    { id: "pdftoppm", command: "pdftoppm", args: ["-v"], label: "pdftoppm" },
    { id: "pdftohtml", command: "pdftohtml", args: ["-v"], label: "pdftohtml" },
    { id: "qpdf", command: "qpdf", label: "qpdf" },
    { id: "ocrmypdf", command: "ocrmypdf", label: "ocrmypdf" },
    { id: "weasyprint", command: pythonExecutable, args: ["-m", "weasyprint", "--version"], label: "WeasyPrint" },
  ];

  return dependencies.map((dependency) => {
    const result = spawnSync(dependency.command, dependency.args || ["--version"], {
      encoding: "utf8",
      env: toolEnv,
      timeout: 3000,
    });

    return {
      ...dependency,
      installed: result.status === 0,
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
      env: toolEnv,
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
