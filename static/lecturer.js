// Lecturer pages (mobile app: Today's blocked list, Today's returns, History, Student detail).
const page = document.body.dataset.page;
const today = document.body.dataset.today;
const listRows = document.querySelector("#list-rows");

function photoCell(record) {
  const element = document.createElement("td");
  if (record.hasPhoto) {
    const image = document.createElement("img");
    image.className = "thumb";
    image.alt = "";
    image.loading = "lazy";
    image.src = `/api/blocked/${encodeURIComponent(record.blockedID)}/photo`;
    element.append(image);
  } else {
    element.innerHTML = '<span class="thumb thumb-empty">—</span>';
  }
  return element;
}

function showStudent(record) {
  document.querySelector("#student-title").textContent = record.studentName || record.studentID;
  const photo = document.querySelector("#student-photo");
  photo.hidden = !record.hasPhoto;
  document.querySelector("#student-no-photo").hidden = Boolean(record.hasPhoto);
  if (record.hasPhoto) photo.src = `/api/blocked/${encodeURIComponent(record.blockedID)}/photo`;
  const list = document.querySelector("#student-details");
  list.replaceChildren();
  for (const [label, value] of [["Student ID", record.studentID], ["Student name", record.studentName],
    ["Blocked date", record.date], ["Blocked time", record.time], ["Blocked by", record.guardID]]) {
    const term = document.createElement("dt");
    term.textContent = label;
    const detail = document.createElement("dd");
    detail.textContent = value || "—";
    list.append(term, detail);
  }
  document.querySelector("#student-modal").showModal();
}

function renderBlocked(rows) {
  if (!rows.length) {
    tableMessage(listRows, 5, "No students from your classes were blocked on this day.");
    return;
  }
  listRows.replaceChildren();
  for (const record of rows) {
    const row = document.createElement("tr");
    row.className = "clickable";
    row.append(photoCell(record), cell(record.studentID), cell(record.studentName), cell(record.time), cell(record.blockedID));
    row.addEventListener("click", () => showStudent(record));
    listRows.append(row);
  }
}

async function loadToday() {
  try {
    const [blocked, returned] = await Promise.all([
      requestJson(`/api/lecturer/blocked?date=${today}`),
      requestJson(`/api/lecturer/returns?date=${today}`),
    ]);
    document.querySelector("#blocked-count").textContent = blocked.rows.length;
    document.querySelector("#returned-count").textContent = returned.rows.length;
    document.querySelector("#list-summary").textContent = `${blocked.rows.length} blocked student(s)`;
    renderBlocked(blocked.rows);
  } catch (error) {
    tableMessage(listRows, 5, error.message);
  }
}

async function loadReturns() {
  const day = document.querySelector("#list-date").value || today;
  try {
    const data = await requestJson(`/api/lecturer/returns?date=${day}`);
    document.querySelector("#list-summary").textContent = `${data.rows.length} returned student(s) on ${day}`;
    if (!data.rows.length) {
      tableMessage(listRows, 5, "No students from your classes returned on this day.");
      return;
    }
    listRows.replaceChildren();
    for (const record of data.rows) {
      const row = document.createElement("tr");
      row.append(cell(record.returnID), cell(record.studentID), cell(record.studentName), cell(record.time), cell(record.guardID));
      listRows.append(row);
    }
  } catch (error) {
    tableMessage(listRows, 5, error.message);
  }
}

async function loadHistory() {
  const rows = document.querySelector("#history-rows");
  const params = new URLSearchParams({
    start: document.querySelector("#history-start").value,
    end: document.querySelector("#history-end").value,
  });
  try {
    const data = await requestJson(`/api/lecturer/history?${params}`);
    const total = data.rows.reduce((sum, row) => sum + (row.totalnum || 0), 0);
    document.querySelector("#history-summary").textContent = `${data.rows.length} day(s) · ${total} blocked in total`;
    if (!data.rows.length) {
      tableMessage(rows, 3, "No blocked students in this range.");
      return;
    }
    rows.replaceChildren();
    for (const record of data.rows) {
      const row = document.createElement("tr");
      const action = document.createElement("td");
      action.append(actionButton("View", "button-outline", () => openDay(record.date)));
      row.append(cell(record.date), cell(record.totalnum), action);
      rows.append(row);
    }
  } catch (error) {
    tableMessage(rows, 3, error.message);
  }
}

async function openDay(day) {
  document.querySelector("#day-title").textContent = day;
  tableMessage(listRows, 5, "Loading…");
  document.querySelector("#day-modal").showModal();
  try {
    renderBlocked((await requestJson(`/api/lecturer/blocked?date=${day}`)).rows);
  } catch (error) {
    tableMessage(listRows, 5, error.message);
  }
}

document.querySelector("#close-student").addEventListener("click", () => document.querySelector("#student-modal").close());

if (page === "today") {
  loadToday();
  setInterval(loadToday, 15000);
} else if (page === "returns") {
  document.querySelector("#date-form").addEventListener("submit", (event) => {
    event.preventDefault();
    loadReturns();
  });
  document.querySelector("#list-date").addEventListener("change", loadReturns);
  loadReturns();
} else {
  const start = document.querySelector("#history-start");
  const end = document.querySelector("#history-end");
  start.addEventListener("change", () => {
    end.min = start.value; // end date can't be before the start date (as in the app)
    if (end.value && end.value < start.value) end.value = start.value;
  });
  document.querySelector("#history-form").addEventListener("submit", (event) => {
    event.preventDefault();
    loadHistory();
  });
  document.querySelector("#close-day").addEventListener("click", () => document.querySelector("#day-modal").close());
  loadHistory();
}
