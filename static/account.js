// Profile: change password. Forgot password: request an emailed code, then set a new password.
const passwordForm = document.querySelector("#password-form");
if (passwordForm) {
  passwordForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const next = document.querySelector("#new-password").value;
    if (next !== document.querySelector("#confirm-password").value) {
      showToast("The new passwords do not match.", true);
      return;
    }
    try {
      const data = await requestJson("/api/profile/password", {
        method: "POST",
        body: JSON.stringify({ current: document.querySelector("#current-password").value, new: next }),
      });
      passwordForm.reset();
      showToast(data.message);
    } catch (error) {
      showToast(error.message, true);
    }
  });
}

const requestForm = document.querySelector("#reset-request-form");
const confirmForm = document.querySelector("#reset-confirm-form");
if (requestForm) {
  requestForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const data = await requestJson("/api/auth/password-reset/request", {
        method: "POST",
        body: JSON.stringify({ id: document.querySelector("#reset-id").value.trim() }),
      });
      showToast(data.message);
      requestForm.hidden = true;
      confirmForm.hidden = false;
      document.querySelector("#reset-intro").textContent = "Enter the code from your email and choose a new password.";
      document.querySelector("#reset-code").focus();
    } catch (error) {
      showToast(error.message, true);
    }
  });

  confirmForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const password = document.querySelector("#reset-password").value;
    if (password !== document.querySelector("#reset-password2").value) {
      showToast("The passwords do not match.", true);
      return;
    }
    try {
      const data = await requestJson("/api/auth/password-reset/confirm", {
        method: "POST",
        body: JSON.stringify({
          id: document.querySelector("#reset-id").value.trim(),
          code: document.querySelector("#reset-code").value.trim(),
          password,
        }),
      });
      showToast(data.message);
      setTimeout(() => window.location.assign("/"), 1500);
    } catch (error) {
      showToast(error.message, true);
    }
  });
}
