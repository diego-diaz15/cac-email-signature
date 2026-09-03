const form = document.getElementById("form");
const preview = document.getElementById("preview");
const statusEl = document.getElementById("status");
const suffix = document.getElementById("email-suffix");

let lastBundle = { fragment: "", document: "", plain: "", template: "corporate" };
let timer = 0;
let previewSeq = 0;

function selectedTemplate() {
  const hidden = form.querySelector('input[name="template"]');
  return hidden && hidden.value ? hidden.value : "original";
}

function payload() {
  const data = Object.fromEntries(new FormData(form).entries());
  return {
    first_name: data.first_name || "",
    last_name: data.last_name || "",
    title: data.title || "",
    department: data.department || "",
    phone: data.phone || "",
    email_local: data.email_local || "",
    website: data.website || "",
    linkedin: data.linkedin || "",
    template: selectedTemplate(),
  };
}

function setStatus(message) {
  statusEl.textContent = message;
}

async function post(path) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload()),
  });
  if (!response.ok) {
    let detail = "No se pudo generar la firma.";
    try {
      const error = await response.json();
      detail = error.error || detail;
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
  return response;
}

async function refresh() {
  const seq = ++previewSeq;
  const response = await post("/api/preview");
  const bundle = await response.json();
  if (seq !== previewSeq) {
    return;
  }
  lastBundle = bundle;
  preview.srcdoc = lastBundle.document;
}

function scheduleRefresh() {
  window.clearTimeout(timer);
  timer = window.setTimeout(() => {
    refresh().catch((error) => setStatus(error.message));
  }, 180);
}

function refreshNow() {
  window.clearTimeout(timer);
  refresh().catch((error) => setStatus(error.message));
}

async function copySignature() {
  await refresh();
  const html = lastBundle.fragment;
  const plain = lastBundle.plain || " ";
  try {
    await navigator.clipboard.write([
      new ClipboardItem({
        "text/html": new Blob([html], { type: "text/html" }),
        "text/plain": new Blob([plain], { type: "text/plain" }),
      }),
    ]);
    setStatus("Firma copiada. Pegala en Gmail con Ctrl+V.");
    return;
  } catch {
    /* older browsers */
  }
  const helper = document.createElement("div");
  helper.setAttribute("contenteditable", "true");
  helper.style.position = "fixed";
  helper.style.left = "-9999px";
  helper.innerHTML = html;
  document.body.appendChild(helper);
  const range = document.createRange();
  range.selectNodeContents(helper);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  const ok = document.execCommand("copy");
  selection.removeAllRanges();
  helper.remove();
  setStatus(
    ok
      ? "Firma copiada. Pegala en Gmail con Ctrl+V."
      : "No se pudo copiar. Usá Ver en el navegador y copiá desde ahí."
  );
}

function openTab() {
  const blob = new Blob([lastBundle.document], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank", "noopener");
}

async function download(path, fallbackName) {
  const response = await post(path);
  const blob = await response.blob();
  const header = response.headers.get("Content-Disposition") || "";
  const match = header.match(/filename="([^"]+)"/);
  const name = match ? match[1] : fallbackName;
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = name;
  link.click();
  URL.revokeObjectURL(link.href);
  setStatus(`Se descargó ${name}.`);
}

async function boot() {
  const meta = await fetch("/api/meta").then((response) => response.json());
  document.title = `Signature Builder · ${meta.short_name}`;
  suffix.textContent = `@${meta.email_domain}`;
  form.website.value = meta.website;
  form.addEventListener("input", (event) => {
    if (event.target && event.target.name === "template") {
      return;
    }
    scheduleRefresh();
  });
  form.addEventListener("change", (event) => {
    if (event.target && event.target.name === "template") {
      refreshNow();
      return;
    }
    scheduleRefresh();
  });
  document.getElementById("copy").addEventListener("click", () => {
    copySignature().catch((error) => setStatus(error.message));
  });
  document.getElementById("open-tab").addEventListener("click", () => {
    refresh()
      .then(openTab)
      .catch((error) => setStatus(error.message));
  });
  document.getElementById("export-html").addEventListener("click", () => {
    download("/api/export.html", "firma.html").catch((error) => setStatus(error.message));
  });
  document.getElementById("export-zip").addEventListener("click", () => {
    download("/api/export.zip", "firma.zip").catch((error) => setStatus(error.message));
  });
  await refresh();
}

boot().catch((error) => setStatus(error.message));
