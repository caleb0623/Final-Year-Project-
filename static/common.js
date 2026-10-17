// Shared helpers for the signed-in pages (toast + JSON requests with the CSRF token).
const csrfMeta = document.querySelector('meta[name="csrf-token"]');
let toastTimeout;

function showToast(message, isError = false) {
  const toast = document.querySelector("#toast");
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("visible");
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => toast.classList.remove("visible"), 4500);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(csrfMeta ? { "X-CSRF-Token": csrfMeta.content } : {}),
      ...options.headers,
    },
  });
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401 && csrfMeta) window.location.assign("/");
    throw new Error(data.error || "The request could not be completed.");
  }
  return data;
}

function tableMessage(tbody, columns, text) {
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = columns;
  cell.className = "table-message";
  cell.textContent = text;
  row.append(cell);
  tbody.replaceChildren(row);
}

function cell(text) {
  const element = document.createElement("td");
  element.textContent = text === undefined || text === null || text === "" ? "—" : text;
  return element;
}

function actionButton(label, className, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `button ${className}`;
  button.textContent = label;
  button.addEventListener("click", onClick);
  return button;
}
