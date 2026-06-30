const api = window.converterFile;

const state = {
  files: [],
  selectedId: null,
  queue: [],
  dependencies: [],
  dependencyModalShown: false,
  updatingDependencies: false,
};

const groupLabels = {
  audio: "Áudio",
  video: "Vídeo",
  image: "Imagem",
  pdf: "PDF",
  document: "Documento",
};

const elements = {
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
  convertButton: document.querySelector("#convertButton"),
  queueList: document.querySelector("#queueList"),
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

elements.pickFilesButton.addEventListener("click", pickFiles);
elements.clearFilesButton.addEventListener("click", clearFiles);
elements.targetFormatSelect.addEventListener("change", () => {
  renderAdvancedOptions();
  updateEstimate();
  updateSummary();
});
elements.outputPathInput.addEventListener("input", updateSummary);
elements.validateButton.addEventListener("click", validateSelected);
elements.convertButton.addEventListener("click", convertSelected);
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

checkDependencies();

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
}

function clearFiles() {
  state.files = [];
  state.selectedId = null;
  renderFiles();
  renderDetails();
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
  const outputPath = elements.outputPathInput.value || `${file.stem}.${target}`;
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
  addQueueMessage(file.name, "running", "Convertendo...");
  const response = await api.convert(payload);
  if (!response.ok) {
    addQueueMessage(file.name, "failed", response.error);
    return;
  }
  addQueueMessage(response.result.outputPath, "done", `Concluído · ${formatBytes(response.result.sizeBytes || 0)}`);
}

function buildJobPayload(file) {
  const targetFormat = elements.targetFormatSelect.value;
  return {
    inputPath: file.path,
    sourceGroup: file.group,
    targetFormat,
    outputPath: elements.outputPathInput.value || undefined,
    options: file.options || {},
  };
}

async function checkDependencies() {
  const dependencies = await api.checkDependencies();
  state.dependencies = dependencies;
  renderDependencies();

  const missing = dependencies.filter((dependency) => !dependency.installed);
  if (missing.length > 0 && !state.dependencyModalShown) {
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

function addQueueMessage(name, status, message) {
  state.queue.unshift({ id: crypto.randomUUID(), name, status, message });
  renderQueue();
}

function renderQueue() {
  if (state.queue.length === 0) {
    elements.queueList.className = "queue-list empty";
    elements.queueList.textContent = "Nenhuma conversão iniciada.";
    return;
  }
  elements.queueList.className = "queue-list";
  elements.queueList.innerHTML = "";
  for (const item of state.queue) {
    const row = document.createElement("div");
    row.className = "queue-row";
    row.innerHTML = `
      <div>
        <div class="file-name">${escapeHtml(item.name)}</div>
        <div class="queue-meta">${escapeHtml(item.message)}</div>
      </div>
      <span class="queue-status ${item.status}">${statusLabel(item.status)}</span>
    `;
    elements.queueList.appendChild(row);
  }
}

function selectedFile() {
  return state.files.find((file) => file.id === state.selectedId);
}

function isVideoTarget(format) {
  return ["mov", "mp4", "avi", "mkv", "webm"].includes(format);
}

function statusLabel(status) {
  return {
    running: "Rodando",
    done: "OK",
    failed: "Erro",
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
