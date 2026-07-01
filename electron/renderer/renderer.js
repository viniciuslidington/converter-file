const api = window.converterFile;

const state = {
  activeView: "converter",
  files: [],
  selectedId: null,
  queue: [],
  history: [],
  presets: [],
  settings: {},
  dependencies: [],
  dependencyModalShown: false,
  updatingDependencies: false,
  runningQueue: false,
};

const groupLabels = {
  audio: "Áudio",
  video: "Vídeo",
  image: "Imagem",
  pdf: "PDF",
  document: "Documento",
};

const elements = {
  navItems: document.querySelectorAll(".nav-item[data-view]"),
  views: document.querySelectorAll(".app-view"),
  pickFilesButton: document.querySelector("#pickFilesButton"),
  clearFilesButton: document.querySelector("#clearFilesButton"),
  dropZone: document.querySelector("#dropZone"),
  fileList: document.querySelector("#fileList"),
  detailsEmpty: document.querySelector("#detailsEmpty"),
  detailsContent: document.querySelector("#detailsContent"),
  selectedFileName: document.querySelector("#selectedFileName"),
  selectedFileMeta: document.querySelector("#selectedFileMeta"),
  targetFormatSelect: document.querySelector("#targetFormatSelect"),
  estimateBox: document.querySelector("#estimateBox"),
  advancedOptions: document.querySelector("#advancedOptions"),
  outputPathInput: document.querySelector("#outputPathInput"),
  summaryBox: document.querySelector("#summaryBox"),
  validateButton: document.querySelector("#validateButton"),
  addToQueueButton: document.querySelector("#addToQueueButton"),
  convertButton: document.querySelector("#convertButton"),
  queueList: document.querySelector("#queueList"),
  queuePageList: document.querySelector("#queuePageList"),
  runQueueButton: document.querySelector("#runQueueButton"),
  clearDoneQueueButton: document.querySelector("#clearDoneQueueButton"),
  historySearchInput: document.querySelector("#historySearchInput"),
  historyStatusFilter: document.querySelector("#historyStatusFilter"),
  historyList: document.querySelector("#historyList"),
  savePresetButton: document.querySelector("#savePresetButton"),
  presetList: document.querySelector("#presetList"),
  defaultOutputDirectoryInput: document.querySelector("#defaultOutputDirectoryInput"),
  pickOutputDirectoryButton: document.querySelector("#pickOutputDirectoryButton"),
  overwriteExistingFilesInput: document.querySelector("#overwriteExistingFilesInput"),
  openOutputAfterConversionInput: document.querySelector("#openOutputAfterConversionInput"),
  showDependencyWarningsInput: document.querySelector("#showDependencyWarningsInput"),
  themeSelect: document.querySelector("#themeSelect"),
  maxConcurrentJobsInput: document.querySelector("#maxConcurrentJobsInput"),
  dependencyButton: document.querySelector("#dependencyButton"),
  dependencySummary: document.querySelector("#dependencySummary"),
  dependencyStatusDot: document.querySelector("#dependencyStatusDot"),
  dependencyPopover: document.querySelector("#dependencyPopover"),
  dependencyList: document.querySelector("#dependencyList"),
  closeDependencyPopover: document.querySelector("#closeDependencyPopover"),
  updateDependenciesButton: document.querySelector("#updateDependenciesButton"),
  dependencyModal: document.querySelector("#dependencyModal"),
  dependencyModalText: document.querySelector("#dependencyModalText"),
  dismissDependencyModal: document.querySelector("#dismissDependencyModal"),
  runDependencyUpdate: document.querySelector("#runDependencyUpdate"),
};

for (const navItem of elements.navItems) {
  navItem.addEventListener("click", () => setActiveView(navItem.dataset.view));
}
elements.pickFilesButton.addEventListener("click", pickFiles);
elements.clearFilesButton.addEventListener("click", clearFiles);
elements.targetFormatSelect.addEventListener("change", () => {
  renderAdvancedOptions();
  updateEstimate();
  updateSummary();
});
elements.outputPathInput.addEventListener("input", updateSummary);
elements.validateButton.addEventListener("click", validateSelected);
elements.addToQueueButton.addEventListener("click", addSelectedToQueue);
elements.convertButton.addEventListener("click", convertSelected);
elements.runQueueButton.addEventListener("click", runPendingQueue);
elements.clearDoneQueueButton.addEventListener("click", clearDoneQueue);
elements.historySearchInput.addEventListener("input", renderHistory);
elements.historyStatusFilter.addEventListener("change", renderHistory);
elements.savePresetButton.addEventListener("click", saveCurrentPreset);
elements.pickOutputDirectoryButton.addEventListener("click", pickOutputDirectory);
elements.defaultOutputDirectoryInput.addEventListener("input", () => updateSetting("defaultOutputDirectory", elements.defaultOutputDirectoryInput.value));
elements.overwriteExistingFilesInput.addEventListener("change", () => updateSetting("overwriteExistingFiles", elements.overwriteExistingFilesInput.checked));
elements.openOutputAfterConversionInput.addEventListener("change", () => updateSetting("openOutputAfterConversion", elements.openOutputAfterConversionInput.checked));
elements.showDependencyWarningsInput.addEventListener("change", () => updateSetting("showDependencyWarnings", elements.showDependencyWarningsInput.checked));
elements.themeSelect.addEventListener("change", () => updateSetting("theme", elements.themeSelect.value));
elements.dependencyButton.addEventListener("click", toggleDependencyPopover);
elements.closeDependencyPopover.addEventListener("click", hideDependencyPopover);
elements.updateDependenciesButton.addEventListener("click", updateDependencies);
elements.dismissDependencyModal.addEventListener("click", hideDependencyModal);
elements.runDependencyUpdate.addEventListener("click", updateDependencies);

elements.dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  elements.dropZone.classList.add("drag-over");
});
elements.dropZone.addEventListener("dragleave", () => {
  elements.dropZone.classList.remove("drag-over");
});
elements.dropZone.addEventListener("drop", async (event) => {
  event.preventDefault();
  elements.dropZone.classList.remove("drag-over");
  const paths = [...event.dataTransfer.files].map((file) => file.path).filter(Boolean);
  await addFiles(paths);
});

initializeApp();

async function initializeApp() {
  await loadAppData();
  renderAll();
  checkDependencies();
}

async function loadAppData() {
  const data = await api.loadStore();
  state.settings = data.settings || {};
  state.history = data.history || [];
  state.presets = data.presets || [];
  state.queue = (data.queue || []).map((job) => normalizeStoredJob(job));
}

function renderAll() {
  applyTheme();
  renderNavigation();
  renderFiles();
  renderDetails();
  renderQueue();
  renderHistory();
  renderPresets();
  renderSettings();
}

function setActiveView(view) {
  state.activeView = view;
  renderNavigation();
}

function renderNavigation() {
  for (const navItem of elements.navItems) {
    navItem.classList.toggle("active", navItem.dataset.view === state.activeView);
  }
  for (const view of elements.views) {
    view.classList.toggle("hidden", view.id !== `${state.activeView}View`);
  }
}

async function pickFiles() {
  const paths = await api.pickFiles();
  await addFiles(paths);
}

async function addFiles(paths) {
  for (const filePath of paths) {
    if (state.files.some((file) => file.path === filePath)) {
      continue;
    }

    const response = await api.inspect({ path: filePath });
    if (!response.ok) {
      addQueueMessage(filePath, "failed", response.error);
      continue;
    }

    state.files.push({
      id: crypto.randomUUID(),
      ...response.result,
      targetFormat: response.result.targetFormats[0],
      options: {},
    });
  }

  if (!state.selectedId && state.files.length > 0) {
    state.selectedId = state.files[0].id;
  }

  renderFiles();
  renderDetails();
  renderPresets();
}

function clearFiles() {
  state.files = [];
  state.selectedId = null;
  renderFiles();
  renderDetails();
  renderPresets();
}

function renderFiles() {
  if (state.files.length === 0) {
    elements.fileList.className = "file-list empty";
    elements.fileList.textContent = "Nenhum arquivo selecionado.";
    return;
  }

  elements.fileList.className = "file-list";
  elements.fileList.innerHTML = "";

  for (const file of state.files) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `file-row ${file.id === state.selectedId ? "active" : ""}`;
    button.innerHTML = `
      <div>
        <div class="file-name">${escapeHtml(file.name)}</div>
        <div class="file-meta">${groupLabels[file.group] || file.group} · .${file.extension} · ${formatBytes(file.sizeBytes)}</div>
      </div>
    `;
    button.addEventListener("click", () => {
      state.selectedId = file.id;
    renderFiles();
    renderDetails();
    renderPresets();
  });
    elements.fileList.appendChild(button);
  }
}

function renderDetails() {
  const file = selectedFile();
  if (!file) {
    elements.detailsEmpty.classList.remove("hidden");
    elements.detailsContent.classList.add("hidden");
    return;
  }

  elements.detailsEmpty.classList.add("hidden");
  elements.detailsContent.classList.remove("hidden");
  elements.selectedFileName.textContent = file.name;
  elements.selectedFileMeta.textContent = `${groupLabels[file.group] || file.group} · formato atual .${file.extension} · ${formatBytes(file.sizeBytes)}`;

  elements.targetFormatSelect.innerHTML = "";
  for (const format of file.targetFormats) {
    const option = document.createElement("option");
    option.value = format;
    option.textContent = `.${format}`;
    elements.targetFormatSelect.appendChild(option);
  }
  elements.targetFormatSelect.value = file.targetFormat;
  elements.targetFormatSelect.onchange = () => {
    file.targetFormat = elements.targetFormatSelect.value;
    file.options = {};
    renderAdvancedOptions();
    updateEstimate();
    updateSummary();
  };

  elements.outputPathInput.value = "";
  renderAdvancedOptions();
  updateEstimate();
  updateSummary();
  renderPresets();
}

function renderAdvancedOptions() {
  const file = selectedFile();
  if (!file) return;

  const target = elements.targetFormatSelect.value;
  elements.advancedOptions.innerHTML = "";
  file.options = file.options || {};

  if (file.group === "audio") {
    renderAudioOptions(file);
  } else if (file.group === "video" && isVideoTarget(target)) {
    renderVideoOptions(file);
  } else if (file.group === "pdf") {
    renderPdfOptions(file, target);
  } else if (file.group === "document") {
    renderDocumentOptions(file, target);
  } else {
    elements.advancedOptions.textContent = "Sem opções avançadas para esta combinação.";
  }
}

function renderAudioOptions(file) {
  const options = ensureOptions(file, "audio");
  addSelect("Compressão", options, "compressionPreset", [
    ["none", "Nenhuma"],
    ["small", "Arquivo menor"],
    ["balanced", "Equilibrado"],
    ["high_quality", "Alta qualidade"],
  ]);
  addSelect("Canais", options, "channels", [
    ["keep", "Manter original"],
    ["mono", "Mono"],
    ["stereo", "Stereo"],
  ]);
  addToggle("Normalizar volume", options, "normalizeVolume");
  addToggle("Remover metadados", options, "stripMetadata");
}

function renderVideoOptions(file) {
  const options = ensureOptions(file, "video");
  addSelect("Resolução", options, "resolution", [
    ["keep", "Manter original"],
    ["480p", "480p"],
    ["720p", "720p"],
    ["1080p", "1080p"],
    ["2160p", "4K"],
  ]);
  addSelect("Compressão", options, "compressionPreset", [
    ["none", "Nenhuma"],
    ["small", "Arquivo menor"],
    ["balanced", "Equilibrado"],
    ["high_quality", "Alta qualidade"],
  ]);
  addSelect("FPS", options, "fps", [
    ["keep", "Manter original"],
    [24, "24 FPS"],
    [30, "30 FPS"],
    [60, "60 FPS"],
  ]);
  addToggle("Remover áudio", options, "removeAudio");
  if (elements.targetFormatSelect.value === "mp4") {
    addToggle("Otimizar para web", options, "optimizeForWeb");
  }
  addToggle("Remover metadados", options, "stripMetadata");
}

function renderPdfOptions(file, target) {
  const options = ensureOptions(file, "pdf");
  if (target === "pdf") {
    addSelect("Compressão", options, "compressionPreset", [
      ["none", "Nenhuma"],
      ["small", "Arquivo menor"],
      ["balanced", "Equilibrado"],
      ["high_quality", "Alta qualidade"],
    ]);
  }
  if (["pdf", "txt", "md", "docx"].includes(target)) {
    addToggle("Aplicar OCR", options, "ocr");
    if (options.ocr) {
      addSelect("Idioma OCR", options, "ocrLanguage", [
        ["por", "Português"],
        ["eng", "Inglês"],
        ["spa", "Espanhol"],
        ["auto", "Detectar automaticamente"],
      ]);
      if (target === "pdf") {
        addToggle("PDF pesquisável", options, "searchablePdf");
      }
    }
  }
  if (["png", "jpg", "webp"].includes(target)) {
    addSelect("DPI", options, "dpi", [
      [72, "72 DPI"],
      [150, "150 DPI"],
      [300, "300 DPI"],
    ]);
  }
  if (target === "pdf") {
    addText("Senha do PDF", options, "password", "Opcional");
  }
  addToggle("Remover metadados", options, "stripMetadata");
}

function renderDocumentOptions(file, target) {
  const options = ensureOptions(file, "document");
  if (target === "pdf") {
    addSelect("Qualidade do PDF", options, "pdfQuality", [
      ["small", "Pequeno"],
      ["balanced", "Equilibrado"],
      ["print", "Impressão"],
    ]);
  }
  if (["pdf", "docx", "odt", "html"].includes(target)) {
    addToggle("Preservar layout", options, "preserveLayout", true);
  }
  if (["txt", "md", "html"].includes(target)) {
    addToggle("Extrair apenas texto", options, "extractTextOnly");
  }
  if (["md", "html"].includes(target)) {
    addToggle("Incluir imagens", options, "includeImages", true);
  }
  if (["html", "md", "png", "jpg", "webp"].includes(target)) {
    addSelect("Modo de saída", options, "outputMode", [
      ["single_file", "Arquivo único"],
      ["folder", "Pasta com arquivos auxiliares"],
    ]);
  }
  if (["txt", "md", "html"].includes(target)) {
    addSelect("Encoding", options, "encoding", [
      ["utf-8", "UTF-8"],
      ["latin1", "Latin1"],
    ]);
  }
  if (target === "md") {
    addSelect("Markdown flavor", options, "markdownFlavor", [
      ["github", "GitHub Flavored Markdown"],
      ["commonmark", "CommonMark"],
    ]);
  }
  if (["pdf", "md", "html"].includes(target)) {
    addToggle("Gerar sumário", options, "generateToc");
  }
  addToggle("Remover metadados", options, "stripMetadata");
}

function ensureOptions(file, key) {
  file.options[key] = file.options[key] || {};
  return file.options[key];
}

function addSelect(label, target, key, choices) {
  if (target[key] === undefined) {
    target[key] = choices[0][0];
  }
  const field = document.createElement("label");
  field.className = "field";
  field.innerHTML = `<span>${label}</span>`;
  const select = document.createElement("select");
  for (const [value, text] of choices) {
    const option = document.createElement("option");
    option.value = String(value);
    option.textContent = text;
    select.appendChild(option);
  }
  select.value = String(target[key]);
  select.addEventListener("change", () => {
    const choice = choices.find(([value]) => String(value) === select.value);
    target[key] = choice ? choice[0] : select.value;
    updateSummary();
  });
  field.appendChild(select);
  elements.advancedOptions.appendChild(field);
}

function addToggle(label, target, key, defaultValue = false) {
  if (target[key] === undefined) {
    target[key] = defaultValue;
  }
  const row = document.createElement("label");
  row.className = "toggle-row";
  row.innerHTML = `<span>${label}</span>`;
  const input = document.createElement("input");
  input.type = "checkbox";
  input.checked = Boolean(target[key]);
  input.addEventListener("change", () => {
    target[key] = input.checked;
    renderAdvancedOptions();
    updateSummary();
  });
  row.appendChild(input);
  elements.advancedOptions.appendChild(row);
}

function addText(label, target, key, placeholder) {
  const field = document.createElement("label");
  field.className = "field";
  field.innerHTML = `<span>${label}</span>`;
  const input = document.createElement("input");
  input.type = "password";
  input.placeholder = placeholder || "";
  input.value = target[key] || "";
  input.addEventListener("input", () => {
    target[key] = input.value || undefined;
    updateSummary();
  });
  field.appendChild(input);
  elements.advancedOptions.appendChild(field);
}

async function updateEstimate() {
  const file = selectedFile();
  if (!file) return;

  elements.estimateBox.textContent = "Calculando estimativa...";
  const response = await api.estimate({
    inputPath: file.path,
    sourceGroup: file.group,
    targetFormat: elements.targetFormatSelect.value,
  });

  if (!response.ok || response.result.estimatedSizeBytes === null) {
    elements.estimateBox.textContent = "Estimativa indisponível para esta conversão.";
    return;
  }

  elements.estimateBox.textContent = `Tamanho estimado: ${formatBytes(response.result.estimatedSizeBytes)}`;
}

function updateSummary() {
  const file = selectedFile();
  if (!file) return;
  const target = elements.targetFormatSelect.value;
  const outputPath = resolveOutputPath(file, target) || `${file.stem}.${target}`;
  elements.summaryBox.innerHTML = `
    <strong>Resumo</strong><br />
    Entrada: ${escapeHtml(file.path)}<br />
    Saída: ${escapeHtml(outputPath)}<br />
    Formato: .${target}<br />
    Tipo: ${groupLabels[file.group] || file.group}
  `;
}

async function validateSelected() {
  const file = selectedFile();
  if (!file) return;
  const payload = buildJobPayload(file);
  const response = await api.validate(payload);
  if (!response.ok) {
    addQueueMessage(file.name, "failed", response.error);
    return;
  }
  const result = response.result;
  addQueueMessage(
    file.name,
    result.valid ? "done" : "failed",
    result.valid ? "Configuração válida." : result.errors.join("; ")
  );
}

async function convertSelected() {
  const file = selectedFile();
  if (!file) return;
  const payload = buildJobPayload(file);
  const queueId = addConversionJob(file, payload, "running");
  await runQueueJob(queueId);
}

function addSelectedToQueue() {
  const file = selectedFile();
  if (!file) return;
  const payload = buildJobPayload(file);
  addConversionJob(file, payload, "pending");
  setActiveView("queue");
}

function buildJobPayload(file) {
  const targetFormat = elements.targetFormatSelect.value;
  const outputPath = resolveOutputPath(file, targetFormat);
  return {
    inputPath: file.path,
    sourceGroup: file.group,
    targetFormat,
    outputPath,
    overwriteExistingFiles: Boolean(state.settings.overwriteExistingFiles),
    options: file.options || {},
  };
}

function resolveOutputPath(file, targetFormat) {
  if (elements.outputPathInput.value) {
    return elements.outputPathInput.value;
  }
  if (state.settings.defaultOutputDirectory) {
    return `${state.settings.defaultOutputDirectory}/${file.stem}.${targetFormat}`;
  }
  return undefined;
}

async function checkDependencies() {
  const dependencies = await api.checkDependencies();
  state.dependencies = dependencies;
  renderDependencies();

  const missing = dependencies.filter((dependency) => !dependency.installed);
  if (missing.length > 0 && state.settings.showDependencyWarnings !== false && !state.dependencyModalShown) {
    state.dependencyModalShown = true;
    showDependencyModal(missing);
  }
}

function renderDependencies() {
  const missing = state.dependencies.filter((dependency) => !dependency.installed);
  const readyCount = state.dependencies.length - missing.length;
  const totalCount = state.dependencies.length;

  elements.dependencySummary.textContent = missing.length === 0
    ? "Tudo pronto"
    : `${missing.length} pendente${missing.length > 1 ? "s" : ""}`;
  elements.dependencyStatusDot.classList.toggle("ok", missing.length === 0);
  elements.updateDependenciesButton.disabled = state.updatingDependencies;
  elements.dependencyList.innerHTML = "";

  const summary = document.createElement("div");
  summary.className = "dependency-summary-row";
  summary.textContent = `${readyCount} de ${totalCount} dependências disponíveis.`;
  elements.dependencyList.appendChild(summary);

  for (const dependency of state.dependencies) {
    const item = document.createElement("div");
    item.className = "dependency-item";
    item.title = dependency.version || dependency.label;
    item.innerHTML = `
      <span><span class="status-dot ${dependency.installed ? "ok" : ""}"></span> ${dependency.label}</span>
      <span class="dependency-version">${dependency.installed ? "OK" : "Ausente"}</span>
    `;
    elements.dependencyList.appendChild(item);
  }
}

function toggleDependencyPopover() {
  const isHidden = elements.dependencyPopover.classList.toggle("hidden");
  elements.dependencyButton.setAttribute("aria-expanded", String(!isHidden));
}

function hideDependencyPopover() {
  elements.dependencyPopover.classList.add("hidden");
  elements.dependencyButton.setAttribute("aria-expanded", "false");
}

function showDependencyModal(missing) {
  const names = missing.map((dependency) => dependency.label).join(", ");
  elements.dependencyModalText.textContent =
    `Dependências ausentes ou não disponíveis no PATH: ${names}. Você pode rodar o script de atualização agora.`;
  elements.dependencyModal.classList.remove("hidden");
}

function hideDependencyModal() {
  elements.dependencyModal.classList.add("hidden");
}

async function updateDependencies() {
  if (state.updatingDependencies) return;
  state.updatingDependencies = true;
  elements.updateDependenciesButton.disabled = true;
  elements.runDependencyUpdate.disabled = true;
  elements.updateDependenciesButton.textContent = "Atualizando...";
  elements.runDependencyUpdate.textContent = "Atualizando...";
  addQueueMessage("Dependências", "running", "Rodando script de atualização...");

  const response = await api.updateDependencies();

  state.updatingDependencies = false;
  elements.updateDependenciesButton.disabled = false;
  elements.runDependencyUpdate.disabled = false;
  elements.updateDependenciesButton.textContent = "Atualizar dependências";
  elements.runDependencyUpdate.textContent = "Atualizar agora";

  if (!response.ok) {
    const details = [response.error, response.stderr].filter(Boolean).join(" ");
    addQueueMessage("Dependências", "failed", details || "Falha ao atualizar dependências.");
    return;
  }

  hideDependencyModal();
  addQueueMessage("Dependências", "done", "Script de atualização concluído.");
  await checkDependencies();
}

function addQueueMessage(name, status, message, progress = null) {
  const id = crypto.randomUUID();
  state.queue.unshift({
    id,
    kind: "message",
    name,
    status,
    message,
    progress,
    createdAt: new Date().toISOString(),
  });
  renderQueue();
  return id;
}

function updateQueueMessage(id, status, message, progress = null, name = null) {
  const item = state.queue.find((entry) => entry.id === id);
  if (!item) return;
  item.status = status;
  item.message = message;
  item.progress = progress;
  if (name !== null) {
    item.name = name;
  }
  renderQueue();
}

function addConversionJob(file, payload, status = "pending") {
  const id = crypto.randomUUID();
  const job = {
    id,
    kind: "conversion",
    name: file.name,
    inputPath: file.path,
    outputPath: payload.outputPath || "",
    sourceGroup: file.group,
    targetFormat: payload.targetFormat,
    options: structuredClone(payload.options || {}),
    payload,
    status,
    progress: status === "running" ? 0 : null,
    message: status === "running" ? "Iniciando conversão..." : "Aguardando na fila.",
    createdAt: new Date().toISOString(),
    startedAt: status === "running" ? new Date().toISOString() : "",
    finishedAt: "",
    error: "",
    sizeBytes: null,
  };
  state.queue.unshift(job);
  persistQueue();
  renderQueue();
  return id;
}

async function runPendingQueue() {
  if (state.runningQueue) return;
  state.runningQueue = true;
  renderQueue();
  try {
    const pending = [...state.queue]
      .reverse()
      .filter((job) => job.kind === "conversion" && job.status === "pending");
    for (const job of pending) {
      await runQueueJob(job.id);
    }
  } finally {
    state.runningQueue = false;
    renderQueue();
  }
}

async function runQueueJob(id) {
  const job = state.queue.find((entry) => entry.id === id);
  if (!job || job.kind !== "conversion") return;

  job.status = "running";
  job.progress = 0;
  job.message = "Iniciando conversão...";
  job.startedAt = new Date().toISOString();
  job.error = "";
  persistQueue();
  renderQueue();

  const response = await api.convertWithProgress(job.payload, (progress) => {
    updateQueueMessage(
      id,
      "running",
      progress.message || "Convertendo...",
      Number(progress.percent || 0)
    );
    persistQueue();
  }, id);

  if (response.cancelled) {
    job.status = "cancelled";
    job.progress = null;
    job.message = "Conversão cancelada.";
    job.error = "";
    job.finishedAt = new Date().toISOString();
    await persistFinishedJob(job);
    renderQueue();
    return;
  }

  if (!response.ok) {
    job.status = "failed";
    job.progress = null;
    job.message = response.error || "Falha na conversão.";
    job.error = job.message;
    job.finishedAt = new Date().toISOString();
    await persistFinishedJob(job);
    renderQueue();
    return;
  }

  job.status = "done";
  job.progress = 100;
  job.outputPath = response.result.outputPath;
  job.sizeBytes = response.result.sizeBytes || null;
  job.message = `Concluído · ${formatBytes(response.result.sizeBytes || 0)}`;
  job.finishedAt = new Date().toISOString();
  await persistFinishedJob(job);
  removeConvertedFile(job.inputPath);
  renderQueue();

  if (state.settings.openOutputAfterConversion && job.outputPath) {
    api.showItemInFolder(job.outputPath);
  }
}

function removeConvertedFile(inputPath) {
  const removedFile = state.files.find((file) => file.path === inputPath);
  if (!removedFile) return;

  state.files = state.files.filter((file) => file.path !== inputPath);
  if (state.selectedId === removedFile.id) {
    state.selectedId = state.files[0]?.id || null;
  }
  renderFiles();
  renderDetails();
  renderPresets();
}

async function persistFinishedJob(job) {
  persistQueue();
  const entry = {
    id: crypto.randomUUID(),
    jobId: job.id,
    inputPath: job.inputPath,
    outputPath: job.outputPath,
    sourceGroup: job.sourceGroup,
    targetFormat: job.targetFormat,
    status: job.status,
    sizeBytes: job.sizeBytes,
    error: job.error,
    createdAt: job.createdAt,
    finishedAt: job.finishedAt,
    options: job.options,
  };
  state.history = await api.addHistory(entry);
  renderHistory();
}

function clearDoneQueue() {
  state.queue = state.queue.filter((job) => !["done", "failed", "cancelled"].includes(job.status));
  persistQueue();
  renderQueue();
}

function persistQueue() {
  api.saveQueue(state.queue.filter((job) => job.kind === "conversion"));
}

function renderQueue() {
  renderQueueInto(elements.queueList, state.queue, "Nenhuma conversão iniciada.");
  renderQueueInto(
    elements.queuePageList,
    state.queue.filter((job) => job.kind === "conversion"),
    "Nenhum job na fila."
  );
  elements.runQueueButton.disabled = state.runningQueue || !state.queue.some((job) => job.kind === "conversion" && job.status === "pending");
}

function renderQueueInto(container, items, emptyMessage) {
  if (!container) return;
  if (items.length === 0) {
    container.className = "queue-list empty";
    container.textContent = emptyMessage;
    return;
  }
  container.className = "queue-list";
  container.innerHTML = "";
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "queue-row";
    row.innerHTML = `
      <div>
        <div class="file-name">${escapeHtml(item.name)}</div>
        <div class="queue-meta">${escapeHtml(item.message)}</div>
        ${item.progress === null || item.progress === undefined ? "" : progressMarkup(item.progress)}
      </div>
      <div class="row-actions">
        ${queueActionsMarkup(item)}
        <span class="queue-status ${item.status}">${statusLabel(item.status)}</span>
      </div>
    `;
    const removeButton = row.querySelector("[data-action='remove-job']");
    if (removeButton) {
      removeButton.addEventListener("click", () => removeQueueJob(item.id));
    }
    const retryButton = row.querySelector("[data-action='retry-job']");
    if (retryButton) {
      retryButton.addEventListener("click", () => retryQueueJob(item.id));
    }
    const cancelButton = row.querySelector("[data-action='cancel-job']");
    if (cancelButton) {
      cancelButton.addEventListener("click", () => cancelQueueJob(item.id));
    }
    container.appendChild(row);
  }
}

function queueActionsMarkup(item) {
  if (item.kind !== "conversion") return "";
  const canRemove = ["pending", "done", "failed", "cancelled"].includes(item.status);
  const canRetry = ["done", "failed", "cancelled"].includes(item.status);
  const canCancel = item.status === "running";
  return `
    ${canCancel ? "<button class=\"ghost-button compact-button\" type=\"button\" data-action=\"cancel-job\">Cancelar</button>" : ""}
    ${canRetry ? "<button class=\"ghost-button compact-button\" type=\"button\" data-action=\"retry-job\">Repetir</button>" : ""}
    ${canRemove ? "<button class=\"ghost-button compact-button\" type=\"button\" data-action=\"remove-job\">Remover</button>" : ""}
  `;
}

function removeQueueJob(id) {
  state.queue = state.queue.filter((job) => job.id !== id);
  persistQueue();
  renderQueue();
}

function retryQueueJob(id) {
  const job = state.queue.find((entry) => entry.id === id);
  if (!job) return;
  job.status = "pending";
  job.progress = null;
  job.message = "Aguardando na fila.";
  job.error = "";
  job.startedAt = "";
  job.finishedAt = "";
  persistQueue();
  renderQueue();
}

async function cancelQueueJob(id) {
  const job = state.queue.find((entry) => entry.id === id);
  if (!job || job.status !== "running") return;
  job.message = "Cancelando conversão...";
  renderQueue();
  await api.cancelConversion(id);
}

function renderHistory() {
  const query = (elements.historySearchInput.value || "").toLowerCase().trim();
  const statusFilter = elements.historyStatusFilter.value || "all";
  const entries = state.history.filter((entry) => {
    if (statusFilter !== "all" && entry.status !== statusFilter) {
      return false;
    }
    if (!query) return true;
    return [
      entry.inputPath,
      entry.outputPath,
      entry.sourceGroup,
      entry.targetFormat,
      entry.status,
      entry.error,
    ].some((value) => String(value || "").toLowerCase().includes(query));
  });

  if (entries.length === 0) {
    elements.historyList.className = "queue-list empty";
    elements.historyList.textContent = state.history.length === 0 ? "Nenhum histórico salvo." : "Nenhum resultado encontrado.";
    return;
  }

  elements.historyList.className = "queue-list";
  elements.historyList.innerHTML = "";
  for (const entry of entries) {
    const row = document.createElement("div");
    row.className = "queue-row";
    row.innerHTML = `
      <div>
        <div class="file-name">${escapeHtml(entry.outputPath || entry.inputPath)}</div>
        <div class="queue-meta">${escapeHtml(historyMeta(entry))}</div>
      </div>
      <div class="row-actions">
        ${entry.outputPath ? "<button class=\"ghost-button compact-button\" type=\"button\" data-action=\"show-output\">Finder</button>" : ""}
        <button class="ghost-button compact-button" type="button" data-action="repeat-history">Repetir</button>
        <span class="queue-status ${entry.status}">${statusLabel(entry.status)}</span>
      </div>
    `;
    const showButton = row.querySelector("[data-action='show-output']");
    if (showButton) {
      showButton.addEventListener("click", () => api.showItemInFolder(entry.outputPath));
    }
    row.querySelector("[data-action='repeat-history']").addEventListener("click", () => enqueueHistoryEntry(entry));
    elements.historyList.appendChild(row);
  }
}

function historyMeta(entry) {
  const finishedAt = entry.finishedAt ? new Date(entry.finishedAt).toLocaleString("pt-BR") : "sem data";
  const size = entry.sizeBytes ? ` · ${formatBytes(entry.sizeBytes)}` : "";
  const error = entry.error ? ` · ${entry.error}` : "";
  return `${entry.sourceGroup} para .${entry.targetFormat} · ${finishedAt}${size}${error}`;
}

function enqueueHistoryEntry(entry) {
  const id = crypto.randomUUID();
  state.queue.unshift({
    id,
    kind: "conversion",
    name: fileNameFromPath(entry.inputPath),
    inputPath: entry.inputPath,
    outputPath: "",
    sourceGroup: entry.sourceGroup,
    targetFormat: entry.targetFormat,
    options: structuredClone(entry.options || {}),
    payload: {
      inputPath: entry.inputPath,
      sourceGroup: entry.sourceGroup,
      targetFormat: entry.targetFormat,
      options: structuredClone(entry.options || {}),
    },
    status: "pending",
    progress: null,
    message: "Aguardando na fila.",
    createdAt: new Date().toISOString(),
    startedAt: "",
    finishedAt: "",
    error: "",
    sizeBytes: null,
  });
  persistQueue();
  renderQueue();
  setActiveView("queue");
}

async function saveCurrentPreset() {
  const file = selectedFile();
  if (!file) {
    addQueueMessage("Presets", "failed", "Selecione um arquivo antes de salvar um preset.");
    return;
  }
  const name = window.prompt("Nome do preset", `${groupLabels[file.group] || file.group} para .${elements.targetFormatSelect.value}`);
  if (!name) return;
  const now = new Date().toISOString();
  const preset = {
    id: crypto.randomUUID(),
    name,
    sourceGroup: file.group,
    targetFormat: elements.targetFormatSelect.value,
    options: structuredClone(file.options || {}),
    createdAt: now,
    updatedAt: now,
  };
  state.presets = await api.addPreset(preset);
  renderPresets();
}

function renderPresets() {
  if (state.presets.length === 0) {
    elements.presetList.className = "queue-list empty";
    elements.presetList.textContent = "Nenhum preset salvo.";
    return;
  }

  elements.presetList.className = "queue-list";
  elements.presetList.innerHTML = "";
  const file = selectedFile();
  for (const preset of state.presets) {
    const compatible = !file || preset.sourceGroup === file.group;
    const row = document.createElement("div");
    row.className = `queue-row ${compatible ? "" : "muted-row"}`;
    row.innerHTML = `
      <div>
        <div class="file-name">${escapeHtml(preset.name)}</div>
        <div class="queue-meta">${groupLabels[preset.sourceGroup] || preset.sourceGroup} para .${preset.targetFormat}</div>
      </div>
      <div class="row-actions">
        <button class="ghost-button compact-button" type="button" data-action="apply-preset" ${compatible ? "" : "disabled"}>Aplicar</button>
        <button class="ghost-button compact-button" type="button" data-action="rename-preset">Renomear</button>
        <button class="ghost-button compact-button" type="button" data-action="delete-preset">Excluir</button>
      </div>
    `;
    row.querySelector("[data-action='apply-preset']").addEventListener("click", () => applyPreset(preset));
    row.querySelector("[data-action='rename-preset']").addEventListener("click", () => renamePreset(preset));
    row.querySelector("[data-action='delete-preset']").addEventListener("click", () => deletePreset(preset.id));
    elements.presetList.appendChild(row);
  }
}

async function renamePreset(preset) {
  const name = window.prompt("Novo nome do preset", preset.name);
  if (!name || name === preset.name) return;
  state.presets = await api.updatePreset(preset.id, { name });
  renderPresets();
}

async function deletePreset(id) {
  state.presets = await api.deletePreset(id);
  renderPresets();
}

function applyPreset(preset) {
  const file = selectedFile();
  if (!file || file.group !== preset.sourceGroup || !file.targetFormats.includes(preset.targetFormat)) {
    addQueueMessage("Presets", "failed", "Preset incompatível com o arquivo selecionado.");
    return;
  }
  file.targetFormat = preset.targetFormat;
  file.options = structuredClone(preset.options || {});
  setActiveView("converter");
  renderDetails();
}

function renderSettings() {
  elements.defaultOutputDirectoryInput.value = state.settings.defaultOutputDirectory || "";
  elements.overwriteExistingFilesInput.checked = Boolean(state.settings.overwriteExistingFiles);
  elements.openOutputAfterConversionInput.checked = Boolean(state.settings.openOutputAfterConversion);
  elements.showDependencyWarningsInput.checked = state.settings.showDependencyWarnings !== false;
  elements.themeSelect.value = state.settings.theme || "system";
}

async function updateSetting(key, value) {
  state.settings = await api.updateSettings({ [key]: value });
  applyTheme();
  renderSettings();
}

function applyTheme() {
  document.documentElement.dataset.theme = state.settings.theme || "system";
}

async function pickOutputDirectory() {
  const folder = await api.pickFolder();
  if (!folder) return;
  await updateSetting("defaultOutputDirectory", folder);
}

function normalizeStoredJob(job) {
  return {
    ...job,
    kind: "conversion",
    status: job.status === "running" ? "pending" : (job.status || "pending"),
    progress: job.status === "running" ? null : job.progress,
    message: job.status === "running" ? "Aguardando na fila." : (job.message || "Aguardando na fila."),
  };
}

function fileNameFromPath(filePath) {
  return String(filePath || "").split(/[\\/]/).pop() || filePath;
}

function progressMarkup(progress) {
  const percent = Math.max(0, Math.min(100, Number(progress) || 0));
  return `
    <div class="progress-track" aria-label="Progresso da conversão" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${percent}" role="progressbar">
      <div class="progress-fill" style="width: ${percent}%"></div>
    </div>
  `;
}

function selectedFile() {
  return state.files.find((file) => file.id === state.selectedId);
}

function isVideoTarget(format) {
  return ["mov", "mp4", "avi", "mkv", "webm"].includes(format);
}

function statusLabel(status) {
  return {
    pending: "Pendente",
    running: "Rodando",
    done: "OK",
    failed: "Erro",
    cancelled: "Cancelado",
  }[status] || status;
}

function formatBytes(value) {
  if (value === null || value === undefined) return "indisponível";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = Number(value);
  for (const unit of units) {
    if (size < 1024 || unit === units[units.length - 1]) {
      return unit === "B" ? `${Math.round(size)} ${unit}` : `${size.toFixed(1)} ${unit}`;
    }
    size /= 1024;
  }
  return `${value} B`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
