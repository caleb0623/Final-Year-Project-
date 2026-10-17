// Admin: security guard accounts (mobile app: Security home / Add / Edit / Detail / Delete).
const guardRows = document.querySelector("#guard-rows");
const guardModal = document.querySelector("#guard-modal");
const guardForm = document.querySelector("#guard-form");
let guards = [];
let editingGuard = null;

async function loadGuards() {
  const query = document.querySelector("#guard-query").value.trim();
  try {
    const data = await requestJson(`/api/admin/guards?${new URLSearchParams({ q: query })}`);
    guards = data.guards;
    renderGuards();
  } catch (error) {
    tableMessage(guardRows, 5, error.message);
  }
}

function renderGuards() {
  document.querySelector("#guard-summary").textContent = `${guards.length} guard(s)`;
  if (!guards.length) {
    tableMessage(guardRows, 5, "No security guards found.");
    return;
  }
  guardRows.replaceChildren();
  for (const guard of guards) {
    const row = document.createElement("tr");
    row.append(cell(guard.guardID), cell(guard.guardName), cell(guard.guardPhoneNo), cell(guard.adminID));
    const actions = document.createElement("td");
    const group = document.createElement("div");
    group.className = "enrollment-actions";
    group.append(
      actionButton("View", "button-outline", () => showGuard(guard)),
      actionButton("Edit", "button-outline", () => openGuardForm(guard)),
      actionButton("Delete", "button-danger-outline", () => deleteGuard(guard)),
    );
    actions.append(group);
    row.append(actions);
    guardRows.append(row);
  }
}

function showGuard(guard) {
  document.querySelector("#detail-title").textContent = guard.guardName;
  const list = document.querySelector("#detail-list");
  list.replaceChildren();
  for (const [label, value] of [["Guard ID", guard.guardID], ["Name", guard.guardName],
    ["Phone", guard.guardPhoneNo], ["Created by", guard.adminID]]) {
    const term = document.createElement("dt");
    term.textContent = label;
    const detail = document.createElement("dd");
    detail.textContent = value || "—";
    list.append(term, detail);
  }
  document.querySelector("#guard-detail").showModal();
}

function openGuardForm(guard = null) {
  editingGuard = guard;
  guardForm.reset();
  document.querySelector("#guard-modal-eyebrow").textContent = guard ? "EDIT GUARD" : "NEW GUARD";
  document.querySelector("#guard-modal-title").textContent = guard ? `Edit ${guard.guardID}` : "Add security guard";
  document.querySelector("#guard-modal-note").textContent = guard
    ? "Leave the password empty to keep the current one."
    : "The guard ID is assigned automatically.";
  document.querySelector("#guard-password-label").textContent = guard ? "New password (optional)" : "Password";
  document.querySelector("#guard-password").required = !guard;
  if (guard) {
    document.querySelector("#guard-name").value = guard.guardName || "";
    document.querySelector("#guard-phone").value = guard.guardPhoneNo || "";
  }
  guardModal.showModal();
  document.querySelector("#guard-name").focus();
}

async function deleteGuard(guard) {
  if (!window.confirm(`Delete security guard ${guard.guardID} ${guard.guardName}?`)) return;
  try {
    const data = await requestJson(`/api/admin/guards/${encodeURIComponent(guard.guardID)}`, { method: "DELETE" });
    showToast(data.message);
    loadGuards();
  } catch (error) {
    showToast(error.message, true);
  }
}

guardForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(guardForm).entries());
  const saveButton = document.querySelector("#save-guard");
  saveButton.disabled = true;
  try {
    const data = editingGuard
      ? await requestJson(`/api/admin/guards/${encodeURIComponent(editingGuard.guardID)}`, {
          method: "PUT", body: JSON.stringify(payload),
        })
      : await requestJson("/api/admin/guards", { method: "POST", body: JSON.stringify(payload) });
    guardModal.close();
    showToast(data.message);
    loadGuards();
  } catch (error) {
    showToast(error.message, true);
  } finally {
    saveButton.disabled = false;
  }
});

document.querySelector("#open-add-guard").addEventListener("click", () => openGuardForm());
document.querySelector("#close-detail").addEventListener("click", () => document.querySelector("#guard-detail").close());
document.querySelector("#guard-search").addEventListener("submit", (event) => {
  event.preventDefault();
  loadGuards();
});
document.querySelector("#guard-query").addEventListener("input", () => loadGuards());
loadGuards();
