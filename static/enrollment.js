const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
const toast = document.querySelector("#toast");
const faceDialog = document.querySelector("#face-enrollment-modal");
const studentDialog = document.querySelector("#student-modal");
const video = document.querySelector("#face-camera-preview");
const imageInput = document.querySelector("#face-image-upload");
const cameraStatus = document.querySelector("#face-camera-status");
const sampleStrip = document.querySelector("#face-samples");
const startCameraButton = document.querySelector("#start-face-camera");
const captureButton = document.querySelector("#capture-face");
const trainButton = document.querySelector("#train-face");
const CAMERA_SAMPLES = 8;
const CAMERA_SAMPLE_INTERVAL_MS = 400;
let toastTimeout;
let cameraStream = null;
let activeStudentId = null;
let samples = []; // { blob, name }

const busyDialog = document.querySelector("#busy-dialog");
busyDialog.addEventListener("cancel", (event) => event.preventDefault()); // Esc can't dismiss it

function showBusy(message) {
  document.querySelector("#busy-text").textContent = message;
  if (!busyDialog.open) busyDialog.showModal();
}

function hideBusy() {
  if (busyDialog.open) busyDialog.close();
}

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("visible");
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => toast.classList.remove("visible"), 5000);
}

async function sendRequest(url, options = {}) {
  const isJson = options.body && !(options.body instanceof FormData);
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(isJson ? { "Content-Type": "application/json" } : {}),
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

// ---------------------------------------------------------------- student records
function openStudentDialog(student = null) {
  const form = document.querySelector("#student-form");
  form.reset();
  form.dataset.mode = student ? "edit" : "add";
  document.querySelector("#student-modal-eyebrow").textContent = student ? "EDIT STUDENT" : "NEW STUDENT";
  document.querySelector("#student-modal-title").textContent = student ? `Edit ${student.studentID}` : "Add student";
  const idInput = document.querySelector("#student-id");
  idInput.readOnly = Boolean(student);
  if (student) {
    for (const element of form.elements) {
      if (element.name && student[element.name] !== undefined) element.value = student[element.name];
    }
  }
  studentDialog.showModal();
  (student ? document.querySelector("#student-name") : idInput).focus();
}

document.querySelector("#open-add-student").addEventListener("click", () => openStudentDialog());
document.querySelectorAll(".edit-student").forEach((button) => {
  button.addEventListener("click", () => openStudentDialog(JSON.parse(button.closest("tr").dataset.student)));
});

document.querySelector("#student-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form).entries());
  payload.studentID = payload.studentID.trim().toUpperCase();
  const saveButton = document.querySelector("#save-student");
  saveButton.disabled = true;
  try {
    const data = form.dataset.mode === "edit"
      ? await sendRequest(`/api/admin/students/${encodeURIComponent(payload.studentID)}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        })
      : await sendRequest("/api/admin/students", { method: "POST", body: JSON.stringify(payload) });
    studentDialog.close();
    showToast(data.message);
    window.location.reload();
  } catch (error) {
    showToast(error.message, true);
  } finally {
    saveButton.disabled = false;
  }
});

document.querySelectorAll(".delete-student").forEach((button) => {
  button.addEventListener("click", async () => {
    const studentId = button.closest("tr").dataset.studentId;
    if (!window.confirm(`Delete student ${studentId} and all of their face photos?`)) return;
    button.disabled = true;
    try {
      const data = await sendRequest(`/api/admin/students/${encodeURIComponent(studentId)}`, { method: "DELETE" });
      showToast(data.message);
      window.location.reload();
    } catch (error) {
      showToast(error.message, true);
      button.disabled = false;
    }
  });
});

// ---------------------------------------------------------------- face samples
function renderSamples() {
  sampleStrip.replaceChildren();
  for (const sample of samples) {
    const image = document.createElement("img");
    image.src = URL.createObjectURL(sample.blob);
    image.alt = "";
    image.onload = () => URL.revokeObjectURL(image.src);
    sampleStrip.append(image);
  }
  trainButton.disabled = samples.length === 0;
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = null;
  }
  video.srcObject = null;
  video.hidden = true;
  startCameraButton.disabled = false;
  startCameraButton.classList.remove("is-active");
  captureButton.disabled = true;
}

function openEnrollment(studentId) {
  activeStudentId = studentId;
  samples = [];
  renderSamples();
  document.querySelector("#face-student-id").textContent = studentId;
  document.querySelector("#face-replace").checked = false;
  imageInput.value = "";
  cameraStatus.textContent = "Start the camera or choose photos.";
  faceDialog.showModal();
}

document.querySelectorAll(".train-face").forEach((button) => {
  button.addEventListener("click", () => openEnrollment(button.closest("tr").dataset.studentId));
});

startCameraButton.addEventListener("click", async () => {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showToast("Camera access is unavailable. Open the site on localhost or HTTPS, or use gallery photos.", true);
    return;
  }
  startCameraButton.disabled = true;
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ audio: false, video: { facingMode: "user" } });
    video.srcObject = cameraStream;
    video.hidden = false;
    await video.play();
    startCameraButton.classList.add("is-active");
    captureButton.disabled = false;
    cameraStatus.textContent = `Camera ready. Press "Capture samples" to take ${CAMERA_SAMPLES} photos.`;
  } catch (error) {
    stopCamera();
    showToast(`Could not start the camera: ${error.message}`, true);
  }
});

function grabFrame() {
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
  return new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.92));
}

captureButton.addEventListener("click", async () => {
  if (!cameraStream || !video.videoWidth) {
    showToast("Wait for the camera preview before capturing.", true);
    return;
  }
  captureButton.disabled = true;
  for (let index = 1; index <= CAMERA_SAMPLES; index += 1) {
    cameraStatus.textContent = `Move your face and change expression… ${index}/${CAMERA_SAMPLES}`;
    const blob = await grabFrame();
    if (blob) samples.push({ blob, name: `camera-${Date.now()}-${index}.jpg` });
    renderSamples();
    await new Promise((resolve) => setTimeout(resolve, CAMERA_SAMPLE_INTERVAL_MS));
  }
  cameraStatus.textContent = `${samples.length} sample(s) ready. Press Train.`;
  captureButton.disabled = false;
});

imageInput.addEventListener("change", () => {
  for (const file of imageInput.files) samples.push({ blob: file, name: file.name });
  imageInput.value = "";
  renderSamples();
  cameraStatus.textContent = `${samples.length} sample(s) ready. Press Train.`;
});

trainButton.addEventListener("click", async () => {
  const form = new FormData();
  for (const sample of samples) form.append("images", sample.blob, sample.name);
  if (document.querySelector("#face-replace").checked) form.append("replace", "1");
  trainButton.disabled = true;
  cameraStatus.textContent = "Training… detecting faces and building templates.";
  showBusy(`Training ${activeStudentId} with ${samples.length} photo(s)… please wait`);
  try {
    const data = await sendRequest(
      `/api/admin/students/${encodeURIComponent(activeStudentId)}/face-samples`,
      { method: "POST", body: form },
    );
    const skipped = data.skipped.length ? ` ${data.skipped.length} photo(s) skipped: ${data.skipped[0]}` : "";
    showBusy(`Done. ${data.message}`);
    showToast(data.message + skipped, Boolean(data.skipped.length));
    setTimeout(() => window.location.reload(), data.skipped.length ? 3000 : 1200);
  } catch (error) {
    hideBusy();
    cameraStatus.textContent = error.message;
    showToast(error.message, true);
    trainButton.disabled = false;
  }
});

document.querySelector("#close-face-modal").addEventListener("click", () => faceDialog.close());
document.querySelector("#cancel-face-enrollment").addEventListener("click", () => faceDialog.close());
faceDialog.addEventListener("close", stopCamera);

document.querySelectorAll(".remove-face").forEach((button) => {
  button.addEventListener("click", async () => {
    const studentId = button.closest("tr").dataset.studentId;
    if (!window.confirm(`Remove all face samples for ${studentId}?`)) return;
    button.disabled = true;
    try {
      const data = await sendRequest(
        `/api/admin/students/${encodeURIComponent(studentId)}/face-samples`,
        { method: "DELETE" },
      );
      showToast(data.message);
      window.location.reload();
    } catch (error) {
      showToast(error.message, true);
      button.disabled = false;
    }
  });
});

document.querySelector("#retrain-all").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  if (!window.confirm("Rebuild every face template from the photos stored in Supabase?")) return;
  button.disabled = true;
  showBusy("Retraining all faces… please wait");
  try {
    const data = await sendRequest("/api/admin/face-samples/retrain", { method: "POST" });
    showToast(data.message, data.failed.length > 0);
  } catch (error) {
    showToast(error.message, true);
  } finally {
    hideBusy();
    button.disabled = false;
  }
});
