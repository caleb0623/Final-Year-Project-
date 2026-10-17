const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
const tableBody = document.querySelector("#record-rows");
const recordCount = document.querySelector("#record-count");
const tableSummary = document.querySelector("#table-summary");
const selectedButtons = ["#open-update", "#delete-record"].map((selector) =>
  document.querySelector(selector),
);
let selectedRow = null;
let currentQuery = "";
let toastTimeout;

function showToast(message, isError = false) {
  const toast = document.querySelector("#toast");
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("visible");
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => toast.classList.remove("visible"), 3500);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      "X-CSRF-Token": csrfToken,
      ...options.headers,
    },
  });
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401) window.location.assign("/");
    throw new Error(data.error || "The request could not be completed.");
  }
  return data;
}

function selectRow(rowElement, record) {
  document.querySelectorAll("#record-rows tr.selected").forEach((row) =>
    row.classList.remove("selected"),
  );
  rowElement.classList.add("selected");
  selectedRow = record;
  selectedButtons.forEach((button) => {
    button.disabled = false;
  });
}

function renderRows(rows) {
  selectedRow = null;
  selectedButtons.forEach((button) => {
    button.disabled = true;
  });
  recordCount.textContent = String(rows.length);
  tableSummary.textContent = `${rows.length} ${rows.length === 1 ? "record" : "records"}`;
  tableBody.replaceChildren();

  if (rows.length === 0) {
    const empty = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 5;
    cell.className = "table-message";
    cell.textContent = currentQuery
      ? "No blocked record found for this student today."
      : "There are no blocked records for today.";
    empty.append(cell);
    tableBody.append(empty);
    return;
  }

  for (const record of rows) {
    const row = document.createElement("tr");
    for (const value of [
      record.blockedID,
      record.time,
      record.studentName,
      record.studentID,
      record.guardID,
    ]) {
      const cell = document.createElement("td");
      cell.textContent = value || "";
      row.append(cell);
    }
    row.addEventListener("click", () => selectRow(row, record));
    tableBody.append(row);
  }
}

async function loadRows(query = "") {
  currentQuery = query.trim().toUpperCase();
  tableBody.innerHTML = '<tr><td colspan="5" class="table-message">Loading records…</td></tr>';
  const params = new URLSearchParams();
  if (currentQuery) params.set("student_id", currentQuery);
  try {
    const data = await requestJson(`/api/blocked?${params.toString()}`);
    renderRows(data.rows);
  } catch (error) {
    tableBody.replaceChildren();
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 5;
    cell.className = "table-message";
    cell.textContent = error.message;
    row.append(cell);
    tableBody.append(row);
    recordCount.textContent = "—";
    tableSummary.textContent = "Could not load records";
  }
}

function openRecordDialog(mode, record = null) {
  const dialog = document.querySelector("#record-modal");
  const input = document.querySelector("#modal-student-id");
  const update = mode === "update";
  document.querySelector("#modal-eyebrow").textContent = update ? "CORRECT RECORD" : "NEW RECORD";
  document.querySelector("#modal-title").textContent = update ? "Update student ID" : "Add blocked student";
  document.querySelector("#modal-description").textContent = update
    ? `Change the student associated with blocked record ${record.blockedID}.`
    : "Enter the student ID to add them to today's blocked list.";
  document.querySelector("#save-record").textContent = update ? "Save changes" : "Add record";
  input.value = update ? record.studentID : "";
  dialog.dataset.mode = mode;
  dialog.showModal();
  input.focus();
}

document.querySelector("#search-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await loadRows(document.querySelector("#search-student").value);
});
document.querySelector("#refresh-records").addEventListener("click", () => {
  document.querySelector("#search-student").value = "";
  loadRows();
});
document.querySelector("#open-add").addEventListener("click", () => openRecordDialog("add"));
document.querySelector("#open-update").addEventListener("click", () => {
  if (selectedRow) openRecordDialog("update", selectedRow);
});

document.querySelector("#record-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const mode = event.currentTarget.closest("dialog").dataset.mode;
  const studentId = document.querySelector("#modal-student-id").value.trim().toUpperCase();
  const saveButton = document.querySelector("#save-record");
  saveButton.disabled = true;
  try {
    const data = mode === "update"
      ? await requestJson(`/api/blocked/${encodeURIComponent(selectedRow.blockedID)}`, {
          method: "PATCH",
          body: JSON.stringify({ student_id: studentId }),
        })
      : await requestJson("/api/blocked", {
          method: "POST",
          body: JSON.stringify({ student_id: studentId }),
        });
    document.querySelector("#record-modal").close();
    document.querySelector("#search-student").value = "";
    currentQuery = "";
    renderRows(data.rows);
    showToast(data.message);
  } catch (error) {
    showToast(error.message, true);
  } finally {
    saveButton.disabled = false;
  }
});

document.querySelector("#delete-record").addEventListener("click", async () => {
  if (!selectedRow || !window.confirm(`Remove ${selectedRow.studentID} from today's blocked list?`)) return;
  try {
    const data = await requestJson(`/api/blocked/${encodeURIComponent(selectedRow.blockedID)}`, {
      method: "DELETE",
    });
    renderRows(data.rows);
    showToast(data.message);
  } catch (error) {
    showToast(error.message, true);
  }
});

// ---------------------------------------------------------------- monitoring (face + attire)
const cameraModal = document.querySelector("#camera-modal");
const cameraVideo = document.querySelector("#camera-video");
const cameraStatus = document.querySelector("#camera-status");
const cameraOverlay = document.querySelector("#camera-overlay");
const cameraOverlayContext = cameraOverlay.getContext("2d");
const violationModal = document.querySelector("#violation-modal");
const violationStudentId = document.querySelector("#violation-student-id");
const violationStudentName = document.querySelector("#violation-student-name");
const violationPhoto = document.querySelector("#violation-photo");
const alarm = document.querySelector("#alarm");
const SUPPRESS_REPEAT_MS = 60000;
const recentlyHandled = new Map(); // studentID -> when the guard acknowledged or revoked
let cameraStream = null;
let processingCameraFrames = false;
let pendingViolation = null; // { frame, faceBox }

// Label sits on a bar directly above the box (inside the top edge if the box touches the frame top).
function drawBox(box, label, colour) {
  const [left, top, right, bottom] = box;
  const fontSize = Math.max(12, Math.round(cameraOverlay.width / 40));
  const barHeight = Math.round(fontSize * 1.6);
  cameraOverlayContext.font = `600 ${fontSize}px Segoe UI, sans-serif`;
  cameraOverlayContext.lineWidth = Math.max(2, Math.round(cameraOverlay.width / 320));
  cameraOverlayContext.strokeStyle = colour;
  cameraOverlayContext.strokeRect(left, top, right - left, bottom - top);
  const barWidth = Math.max(right - left, cameraOverlayContext.measureText(label).width + fontSize);
  const barTop = top - barHeight >= 0 ? top - barHeight : top;
  cameraOverlayContext.fillStyle = colour;
  cameraOverlayContext.fillRect(left, barTop, barWidth, barHeight);
  cameraOverlayContext.fillStyle = "#ffffff";
  cameraOverlayContext.textBaseline = "middle";
  cameraOverlayContext.fillText(label, left + fontSize / 2, barTop + barHeight / 2);
}

function drawResult(result, frameWidth, frameHeight) {
  cameraOverlay.width = frameWidth;
  cameraOverlay.height = frameHeight;
  cameraOverlayContext.clearRect(0, 0, frameWidth, frameHeight);
  if (result.face_box) {
    const label = result.student_id
      ? `${result.student_name || result.student_id} ${Math.round(result.similarity * 100)}%`
      : result.similarity === null ? "Unknown face" : `Unknown face · closest ${Math.round(result.similarity * 100)}%`;
    drawBox(result.face_box, label, result.student_id ? "#22a06b" : "#7d8797");
  }
  for (const detection of result.detections) {
    drawBox(detection.bbox, `${detection.class} ${(detection.confidence * 100).toFixed(0)}%`, "#f26b5b");
  }
}

function describe(result) {
  if (!result.face_box) return "No face in view";
  if (!result.student_id) {
    return result.similarity === null
      ? "Face not recognized (no trained faces yet)"
      : `Face not recognized (closest trained face ${Math.round(result.similarity * 100)}%, needs ${Math.round(result.threshold * 100)}%)`;
  }
  const identity = `Recognized ${result.student_name || result.student_id}`;
  if (result.yolo_error) return `${identity} · Attire check unavailable: ${result.yolo_error}`;
  if (result.returned) return `${identity} · Proper attire, removed from today's blocked list`;
  if (result.violation && result.violation.already_blocked) {
    return `${identity} · ${result.violation.reason} (already blocked today)`;
  }
  if (result.violation) return `${identity} · Violation: ${result.violation.reason}`;
  return `${identity} · Proper attire`;
}

function shouldAlert(result) {
  if (!result.violation || result.violation.already_blocked) return false;
  const handledAt = recentlyHandled.get(result.student_id);
  return !handledAt || Date.now() - handledAt > SUPPRESS_REPEAT_MS;
}

async function processCameraFrames(stream) {
  if (processingCameraFrames) return;
  processingCameraFrames = true;
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  try {
    while (cameraStream === stream && cameraModal.open) {
      if (!violationModal.open && cameraVideo.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
        const scale = Math.min(1, 640 / cameraVideo.videoWidth);
        canvas.width = Math.round(cameraVideo.videoWidth * scale);
        canvas.height = Math.round(cameraVideo.videoHeight * scale);
        context.drawImage(cameraVideo, 0, 0, canvas.width, canvas.height);
        const frame = canvas.toDataURL("image/jpeg", 0.8);
        try {
          const result = await requestJson("/api/vision/frame", {
            method: "POST",
            body: JSON.stringify({ frame }),
          });
          drawResult(result, canvas.width, canvas.height);
          cameraStatus.textContent = describe(result);
          cameraStatus.classList.toggle("error", Boolean(result.yolo_error || result.violation));
          if (result.returned) {
            renderRows(result.rows);
            showToast(`${result.student_name || result.student_id} returned with proper attire.`);
          }
          if (shouldAlert(result)) openViolation(result, frame);
        } catch (error) {
          cameraStatus.textContent = error.message;
          cameraStatus.classList.add("error");
          break;
        }
      }
      // The next frame goes out as soon as the previous answer is in (plus a short pause).
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
  } finally {
    processingCameraFrames = false;
    if (cameraStream && cameraModal.open && cameraStream !== stream) {
      processCameraFrames(cameraStream);
    }
  }
}

// ---------------------------------------------------------------- violation alert
function setViolationStudent(student) {
  violationStudentId.value = student.studentID;
  violationStudentName.textContent = student.studentName || "—";
  violationPhoto.hidden = !student.hasPhoto;
  document.querySelector("#violation-no-photo").hidden = Boolean(student.hasPhoto);
  if (student.hasPhoto) {
    violationPhoto.src = `/api/students/${encodeURIComponent(student.studentID)}/photo`;
  }
}

async function lookUpViolationStudent() {
  const studentId = violationStudentId.value.trim().toUpperCase();
  if (!studentId) return;
  try {
    const data = await requestJson(`/api/students/${encodeURIComponent(studentId)}`);
    setViolationStudent(data.student);
  } catch (error) {
    showToast(error.message, true);
  }
}

function openViolation(result, frame) {
  pendingViolation = { frame, faceBox: result.face_box };
  document.querySelector("#violation-reason").textContent = result.violation.reason;
  setViolationStudent({ studentID: result.student_id, studentName: result.student_name, hasPhoto: false });
  violationModal.showModal();
  alarm.currentTime = 0;
  alarm.play().catch(() => {});
  lookUpViolationStudent(); // loads the student's reference photo
}

async function resolveViolation(action) {
  if (!pendingViolation) return;
  const studentId = violationStudentId.value.trim().toUpperCase();
  const buttons = violationModal.querySelectorAll("button");
  buttons.forEach((button) => { button.disabled = true; });
  try {
    const data = await requestJson(`/api/vision/${action}`, {
      method: "POST",
      body: JSON.stringify({
        student_id: studentId,
        frame: pendingViolation.frame,
        face_box: pendingViolation.faceBox,
      }),
    });
    recentlyHandled.set(studentId, Date.now());
    renderRows(data.rows);
    showToast(data.warning ? `${data.message} ${data.warning}` : data.message, Boolean(data.warning));
    violationModal.close();
  } catch (error) {
    showToast(error.message, true);
  } finally {
    buttons.forEach((button) => { button.disabled = false; });
  }
}

violationStudentId.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    lookUpViolationStudent();
  }
});
document.querySelector("#acknowledge-violation").addEventListener("click", () => resolveViolation("acknowledge"));
document.querySelector("#revoke-violation").addEventListener("click", () => resolveViolation("revoke"));
violationModal.addEventListener("cancel", (event) => event.preventDefault()); // the guard must decide
violationModal.addEventListener("close", () => {
  alarm.pause();
  pendingViolation = null;
});

// ---------------------------------------------------------------- camera lifecycle
document.querySelector("#open-camera").addEventListener("click", async () => {
  cameraModal.showModal();
  cameraStatus.textContent = "Starting camera and server-side recognition…";
  cameraStatus.classList.remove("error");
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showToast("Camera access requires a secure browser context (HTTPS or localhost).", true);
    return;
  }
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    cameraVideo.srcObject = cameraStream;
    document.querySelector("#camera-placeholder").hidden = true;
    cameraVideo.onloadedmetadata = () => {
      // Match the frame to the camera's aspect ratio so the overlay boxes line up with the video.
      document.querySelector("#camera-frame").style.aspectRatio = `${cameraVideo.videoWidth} / ${cameraVideo.videoHeight}`;
      processCameraFrames(cameraStream);
    };
  } catch (error) {
    showToast(error.name === "NotAllowedError" ? "Allow camera permission in your browser to start monitoring." : "Could not access the camera.", true);
    cameraStatus.textContent = "Could not access the camera.";
    cameraStatus.classList.add("error");
  }
});

function stopCamera() {
  cameraVideo.onloadedmetadata = null;
  if (cameraStream) cameraStream.getTracks().forEach((track) => track.stop());
  cameraStream = null;
  cameraVideo.srcObject = null;
  cameraOverlayContext.clearRect(0, 0, cameraOverlay.width, cameraOverlay.height);
  document.querySelector("#camera-placeholder").hidden = false;
}
document.querySelector("#close-camera").addEventListener("click", () => cameraModal.close());
cameraModal.addEventListener("close", stopCamera);

document.querySelector("#current-date").textContent = new Intl.DateTimeFormat(undefined, {
  year: "numeric",
  month: "short",
  day: "numeric",
}).format(new Date());
loadRows();
