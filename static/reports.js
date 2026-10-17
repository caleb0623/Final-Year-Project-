const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
const toast = document.querySelector("#toast");
const reportForm = document.querySelector("#report-form");
const startInput = document.querySelector("#report-start");
const endInput = document.querySelector("#report-end");
const rowsBody = document.querySelector("#report-rows");
let toastTimeout;

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("visible");
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => toast.classList.remove("visible"), 4500);
}

function reportParams() {
  return new URLSearchParams({
    start: startInput.value,
    end: endInput.value,
    faculty: document.querySelector("#report-faculty").value,
  });
}

function message(text) {
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = 6;
  cell.className = "table-message";
  cell.textContent = text;
  row.append(cell);
  rowsBody.replaceChildren(row);
}

async function loadReport() {
  message("Loading…");
  const response = await fetch(`/api/admin/reports?${reportParams()}`);
  const data = await response.json();
  if (!response.ok) {
    message(data.error || "Could not load the report.");
    return;
  }
  document.querySelector("#report-summary").textContent = `${data.rows.length} blocked record(s)`;
  if (!data.rows.length) {
    message("No blocked students in this range.");
    return;
  }
  rowsBody.replaceChildren();
  for (const record of data.rows) {
    const row = document.createElement("tr");
    for (const value of [record.blockedID, record.timestamp, record.studentName, record.studentID, record.faculty, record.guardID]) {
      const cell = document.createElement("td");
      cell.textContent = value || "—";
      row.append(cell);
    }
    rowsBody.append(row);
  }
}

// The end date can't be before the start date (as the Tkinter calendar enforced).
startInput.addEventListener("change", () => {
  endInput.min = startInput.value;
  if (endInput.value < startInput.value) endInput.value = startInput.value;
});

reportForm.addEventListener("submit", (event) => {
  event.preventDefault();
  loadReport();
});

document.querySelector("#download-report").addEventListener("click", (event) => {
  event.preventDefault();
  if (!reportForm.reportValidity()) return;
  window.location.assign(`/admin/reports/download?${reportParams()}`);
});

document.querySelector("#email-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button");
  button.disabled = true;
  try {
    const response = await fetch("/api/admin/reports/email", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
      body: JSON.stringify({
        ...Object.fromEntries(reportParams()),
        email: document.querySelector("#report-email").value.trim(),
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not send the report.");
    showToast(data.message);
  } catch (error) {
    showToast(error.message, true);
  } finally {
    button.disabled = false;
  }
});

loadReport();
