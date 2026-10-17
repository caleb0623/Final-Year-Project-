"""Attire Checker website (replaces the FaceBaseSuccess.ipynb Tkinter app).

Administrators manage students, capture face samples ("train"), and generate blocked-student
reports. Security guards monitor the camera (face recognition + YOLO attire check) and manage
today's blocked list. All data lives in Supabase Postgres; all images in private Supabase Storage.
The /api/auth and /api/records endpoints serve the Android app.
"""
import base64
import csv
import hmac
import io
import logging
import os
import secrets
import smtplib
import threading
import time
import uuid
from datetime import date, datetime
from email.message import EmailMessage
from functools import wraps

from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.exceptions import HTTPException

import postgres_store as store
import supabase_storage
import vision_service


app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("ATTIRE_WEB_SECRET") or secrets.token_hex(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("ATTIRE_WEB_HTTPS") == "1",
    MAX_CONTENT_LENGTH=40 * 1024 * 1024,
)
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)
if os.environ.get("ATTIRE_BEHIND_PROXY") == "1":
    # Render / Hugging Face terminate HTTPS at a proxy; trust its X-Forwarded-* headers.
    from werkzeug.middleware.proxy_fix import ProxyFix

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
store.init_store()
token_serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="attire-api-token")

HOME_PAGES = {"admin": "admin_students", "security": "dashboard", "lecturer": "lecturer_today"}
ROLE_LABELS = {"admin": "Administrator", "security": "Security guard", "lecturer": "Lecturer"}
NAME_FIELDS = {"admin": "adminName", "security": "guardName", "lecturer": "lecturerName"}
FACULTIES = ["FOCS", "FAFB", "FOET", "FSSH", "FCCI", "FOBE", "FOAS"]
STUDENT_FIELDS = (
    "studentName", "faculty", "programme", "semester", "yearOfStudy", "tutorialGroup",
    "studentEmail", "studentPhoneNo", "studentStatus",
)
IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_FACE_IMAGE_BYTES = 5 * 1024 * 1024
MAX_FACE_IMAGES_PER_REQUEST = 20
# A blocked student is moved to the returns list once this many consecutive scans show proper
# attire (2 = about half a second), so one frame where YOLO misses the clothing doesn't count.
AUTO_RETURN_CONFIRMATIONS = int(os.environ.get("AUTO_RETURN_CONFIRMATIONS", "2"))
_proper_attire_streak = {}  # studentID -> consecutive proper-attire scans while blocked


class _Cached:
    """Small in-memory cache: Supabase is ~250 ms away, the camera sends several frames a second."""

    def __init__(self, loader, ttl=60):
        self.loader, self.ttl = loader, ttl
        self.value, self.expires = None, 0.0
        self.lock = threading.Lock()

    def get(self):
        with self.lock:
            if time.monotonic() >= self.expires:
                self.value = self.loader()
                self.expires = time.monotonic() + self.ttl
            return self.value

    def clear(self):
        with self.lock:
            self.expires = 0.0


_face_samples = _Cached(store.list_face_samples)
_students = _Cached(lambda: {record["studentID"]: record for record in store.list_records("Student")})
_session_users = {}  # (role, id) -> (expires, record)


def clear_caches():
    _face_samples.clear()
    _students.clear()
    _session_users.clear()
    _proper_attire_streak.clear()


# ----------------------------------------------------------------------------- sessions & auth

def _csrf_token():
    token = session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def _csrf_valid():
    submitted = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    expected = session.get("csrf_token")
    return bool(expected and submitted and secrets.compare_digest(submitted, expected))


@app.before_request
def protect_form_posts():
    if request.path.startswith("/api/"):
        return None
    if request.method in {"POST", "PATCH", "DELETE"} and not _csrf_valid():
        return "Your session expired. Reload the page and try again.", 400


def _session_user():
    role = session.get("account_role")
    account_id = session.get("account_id")
    if role not in HOME_PAGES or not account_id:
        return None
    key = (role, account_id)
    cached = _session_users.get(key)
    if cached and cached[0] > time.monotonic():
        return cached[1]
    record = store.get_record(role, account_id)
    _session_users[key] = (time.monotonic() + 30, record)
    return record


def _web_page(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if _session_user() is None:
                session.clear()
                return redirect(url_for("home"))
            if session.get("account_role") not in roles:
                return "You are not allowed to access this page.", 403
            return view(*args, **kwargs)

        return wrapped

    return decorator


def _web_api(*roles):
    """Browser JSON endpoints: session cookie + X-CSRF-Token on state-changing requests."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if _session_user() is None:
                return jsonify(error="Please sign in again."), 401
            if session.get("account_role") not in roles:
                return jsonify(error="Your account cannot access this resource."), 403
            if request.method != "GET" and not _csrf_valid():
                return jsonify(error="Your session expired. Reload the page and try again."), 400
            return view(*args, **kwargs)

        return wrapped

    return decorator


def _api_user():
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return None
    try:
        return token_serializer.loads(authorization[7:], max_age=8 * 60 * 60)
    except (BadSignature, SignatureExpired):
        return None


def _api_authenticated(view):
    """Android app endpoints: bearer token from /api/auth/login."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = _api_user()
        if user is None:
            return jsonify(error="A valid sign-in is required."), 401
        request.api_user = user
        return view(*args, **kwargs)

    return wrapped


# ----------------------------------------------------------------------------- helpers

def _today():
    return str(date.today())


def _student_record(student_id):
    return _students.get().get(student_id) if student_id else None


def _blocked_today(student_id):
    return store.list_records("blocked", {"studentID": student_id, "date": _today()})


def _blocked_rows(guard_id, student_id=None):
    filters = {"date": _today(), "guardID": guard_id}
    if student_id:
        filters["studentID"] = student_id
    rows = store.list_records("blocked", filters)
    for record in rows:
        record["time"] = f'{record.get("date", "")} {record.get("time", "")}'.strip()
        record["hasPhoto"] = bool(record.pop("photoPath", None))
    rows.sort(key=lambda record: record.get("time", ""), reverse=True)
    return rows


def _remove_today_returns(student_id):
    for record in store.list_records("returns", {"studentID": student_id, "date": _today()}):
        store.delete_record("returns", record["returnID"])


def _block_student(student, guard_id, photo_path=None):
    now = datetime.now()
    record = {
        "blockedID": store.next_id("blocked"),
        "date": _today(),
        "time": now.strftime("%H:%M:%S"),
        "status": "",
        "studentID": student["studentID"],
        "guardID": guard_id,
        "studentName": student.get("studentName", ""),
    }
    if photo_path:
        record["photoPath"] = photo_path
    store.save_record("blocked", record)
    store.count_blocked_student(record["date"])
    _remove_today_returns(student["studentID"])
    return record


def _return_student(blocked_record, guard_id):
    """Move a blocked record to the returns list (student came back properly dressed)."""
    now = datetime.now()
    store.save_record(
        "returns",
        {
            "returnID": store.next_id("returns"),
            "date": _today(),
            "time": now.strftime("%H:%M:%S"),
            "status": "",
            "studentID": blocked_record.get("studentID", ""),
            "guardID": guard_id,
            "studentName": blocked_record.get("studentName", ""),
        },
    )
    store.delete_record("blocked", blocked_record["blockedID"])


def _image_response(path):
    try:
        content = supabase_storage.download_object(path)
    except supabase_storage.StorageConfigurationError as error:
        return jsonify(error=str(error)), 503
    except supabase_storage.StorageRequestError:
        logger.exception("Could not download %s from Supabase Storage.", path)
        return jsonify(error="The photo could not be loaded."), 502
    mimetype = {"png": "image/png", "webp": "image/webp"}.get(path.rsplit(".", 1)[-1], "image/jpeg")
    return Response(content, mimetype=mimetype, headers={"Cache-Control": "private, max-age=300"})


def _upload_or_warn(path, content, what):
    """Upload an image; return a warning string instead of failing the guard's action."""
    try:
        supabase_storage.upload_object(path, content, "image/jpeg")
        return None
    except (supabase_storage.StorageConfigurationError, supabase_storage.StorageRequestError) as error:
        logger.exception("Could not upload %s to Supabase Storage.", what)
        return f"The {what} could not be saved to cloud storage: {error}"


def _decode_frame(payload):
    frame_data = payload.get("frame") if isinstance(payload, dict) else None
    if not isinstance(frame_data, str) or not frame_data.startswith("data:image/jpeg;base64,"):
        raise ValueError("A JPEG camera frame is required.")
    try:
        image_bytes = base64.b64decode(frame_data.partition(",")[2], validate=True)
    except (ValueError, base64.binascii.Error) as error:
        raise ValueError("The camera frame is not valid base64.") from error
    if not image_bytes or len(image_bytes) > 2 * 1024 * 1024:
        raise ValueError("Camera frame must be smaller than 2 MB.")
    return vision_service.decode_image(image_bytes)


def _send_email(recipient, subject, body, attachment=None):
    """attachment: (filename, bytes, maintype, subtype). Raises RuntimeError if not configured."""
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("SMTP_FROM", smtp_username or "")
    if not all((smtp_host, smtp_username, smtp_password, sender)):
        raise RuntimeError("Email is not configured on the server (SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD).")
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(body)
    if attachment:
        filename, content, maintype, subtype = attachment
        message.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)
    with smtplib.SMTP(smtp_host, int(os.environ.get("SMTP_PORT", "587")), timeout=15) as smtp:
        smtp.starttls()
        smtp.login(smtp_username, smtp_password)
        smtp.send_message(message)


# ----------------------------------------------------------------------------- login

@app.route("/", methods=["GET", "POST"])
def home():
    if _session_user():
        return redirect(url_for(HOME_PAGES[session["account_role"]]))

    error = None
    if request.method == "POST":
        role = request.form.get("role", "security").strip().lower()
        account_id = request.form.get("account_id", request.form.get("guard_id", "")).strip().upper()
        password = request.form.get("password", "")
        account = (
            store.authenticate(role, account_id, password)
            if role in HOME_PAGES and account_id and password
            else None
        )
        if account:
            session.clear()
            session["account_id"] = account_id
            session["account_role"] = role
            session["csrf_token"] = secrets.token_urlsafe(32)
            return redirect(url_for(HOME_PAGES[role]))
        error = "Account ID or password was not recognized."

    return render_template("login.html", csrf_token=_csrf_token(), error=error)


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ----------------------------------------------------------------------------- admin pages

def _page_context(active):
    """Values every signed-in page needs for the shared sidebar."""
    role = session["account_role"]
    user = store.get_record(role, session["account_id"]) or {}
    return {
        "active": active,
        "role": role,
        "role_label": ROLE_LABELS[role],
        "account_id": session["account_id"],
        "account_name": user.get(NAME_FIELDS[role], ""),
        "csrf_token": _csrf_token(),
    }


@app.get("/admin/students")
@_web_page("admin")
def admin_students():
    students = sorted(store.list_records("Student"), key=lambda student: str(student.get("studentID", "")))
    samples = store.list_face_samples([student.get("studentID", "") for student in students])
    return render_template(
        "admin_students.html",
        students=students,
        sample_counts={student_id: len(items) for student_id, items in samples.items()},
        faculties=FACULTIES,
        storage_configuration_error=supabase_storage.configuration_error(),
        **_page_context("students"),
    )


@app.get("/admin/reports")
@_web_page("admin")
def admin_reports():
    return render_template("admin_reports.html", faculties=FACULTIES, today=_today(), **_page_context("reports"))


# ----------------------------------------------------------------------------- admin: students

def _student_payload(payload, student_id):
    if not isinstance(payload, dict):
        raise ValueError("A JSON object is required.")
    record = {"studentID": student_id}
    for field in STUDENT_FIELDS:
        record[field] = str(payload.get(field, "") or "").strip()
    if not record["studentName"]:
        raise ValueError("Student name is required.")
    if record["faculty"] and record["faculty"] not in FACULTIES:
        raise ValueError("Choose a faculty from the list.")
    return record


@app.post("/api/admin/students")
@_web_api("admin")
def api_create_student():
    payload = request.get_json(silent=True) or {}
    student_id = str(payload.get("studentID", "")).strip().upper()
    if not student_id:
        return jsonify(error="Student ID is required."), 400
    if _student_record(student_id):
        return jsonify(error=f"Student ID {student_id} already exists."), 409
    try:
        record = store.save_record("Student", _student_payload(payload, student_id))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    _students.clear()
    return jsonify(record=record, message=f"Student {student_id} added."), 201


@app.put("/api/admin/students/<student_id>")
@_web_api("admin")
def api_update_student(student_id):
    student_id = student_id.strip().upper()
    existing = _student_record(student_id)
    if existing is None:
        return jsonify(error="Student record was not found."), 404
    try:
        record = store.save_record("Student", {**existing, **_student_payload(request.get_json(silent=True), student_id)})
    except ValueError as error:
        return jsonify(error=str(error)), 400
    _students.clear()
    return jsonify(record=record, message=f"Student {student_id} updated.")


@app.delete("/api/admin/students/<student_id>")
@_web_api("admin")
def api_delete_student(student_id):
    student_id = student_id.strip().upper()
    if not store.delete_record("Student", student_id):
        return jsonify(error="Student record was not found."), 404
    paths = store.delete_face_samples(student_id)
    _students.clear()
    _face_samples.clear()
    try:
        supabase_storage.delete_objects(paths)
    except (supabase_storage.StorageConfigurationError, supabase_storage.StorageRequestError):
        logger.exception("Could not remove face images of deleted student %s.", student_id)
    return jsonify(message=f"Student {student_id} deleted.")


# ----------------------------------------------------------------------------- admin: face training

@app.post("/api/admin/students/<student_id>/face-samples")
@_web_api("admin")
def api_add_face_samples(student_id):
    """Register face with camera (several captured frames) or gallery (uploaded photos)."""
    student_id = student_id.strip().upper()
    if _student_record(student_id) is None:
        return jsonify(error="Student record was not found."), 404
    files = [item for item in request.files.getlist("images") if item and item.filename]
    if not files:
        return jsonify(error="Capture or choose at least one face photo."), 400
    if len(files) > MAX_FACE_IMAGES_PER_REQUEST:
        return jsonify(error=f"Send at most {MAX_FACE_IMAGES_PER_REQUEST} photos at a time."), 400
    storage_error = supabase_storage.configuration_error()
    if storage_error:
        return jsonify(error=storage_error), 503

    accepted, skipped = [], []
    for index, image_file in enumerate(files, start=1):
        content_type = (image_file.mimetype or "").lower()
        if content_type not in IMAGE_TYPES:
            skipped.append(f"Photo {index}: use a JPEG, PNG, or WebP image.")
            continue
        image_bytes = image_file.read(MAX_FACE_IMAGE_BYTES + 1)
        if not image_bytes or len(image_bytes) > MAX_FACE_IMAGE_BYTES:
            skipped.append(f"Photo {index}: must be smaller than 5 MB.")
            continue
        try:
            embedding = vision_service.extract_face_embedding(image_bytes)
        except vision_service.VisionConfigurationError as error:
            return jsonify(error=str(error)), 503
        except ValueError as error:
            skipped.append(f"Photo {index}: {error}")
            continue
        accepted.append((image_bytes, content_type, embedding))

    if not accepted:
        return jsonify(error="No usable face was found. " + " ".join(skipped[:3]), skipped=skipped), 400

    uploaded = []
    try:
        for image_bytes, content_type, embedding in accepted:
            path = f"faces/{student_id}/{uuid.uuid4().hex}{IMAGE_TYPES[content_type]}"
            supabase_storage.upload_object(path, image_bytes, content_type)
            uploaded.append((path, embedding))
        replaced = store.add_face_samples(
            student_id, uploaded, vision_service.face_model_version(),
            replace=request.form.get("replace") == "1",
        )
    except supabase_storage.StorageRequestError as error:
        logger.exception("Could not upload face samples for %s.", student_id)
        _cleanup([path for path, _ in uploaded])
        return jsonify(error=str(error)), 502
    except Exception:
        logger.exception("Could not save face samples for %s.", student_id)
        _cleanup([path for path, _ in uploaded])
        return jsonify(error="Could not save the face samples."), 500
    _cleanup(replaced)
    _face_samples.clear()

    total = len(store.list_face_samples([student_id]).get(student_id, []))
    return jsonify(
        message=f"Trained {student_id} with {len(uploaded)} new face sample(s); {total} in total.",
        saved=len(uploaded),
        total=total,
        skipped=skipped,
    )


def _cleanup(paths):
    try:
        supabase_storage.delete_objects(paths)
    except (supabase_storage.StorageConfigurationError, supabase_storage.StorageRequestError):
        logger.exception("Could not remove storage objects %s.", paths)


@app.delete("/api/admin/students/<student_id>/face-samples")
@_web_api("admin")
def api_delete_face_samples(student_id):
    student_id = student_id.strip().upper()
    paths = store.delete_face_samples(student_id)
    if not paths:
        return jsonify(error="This student has no face samples."), 404
    _face_samples.clear()
    _cleanup(paths)
    return jsonify(message=f"Face samples removed for {student_id}.")


@app.post("/api/admin/face-samples/retrain")
@_web_api("admin")
def api_retrain_faces():
    """Rebuild every face template from the photos kept in Supabase Storage."""
    trained, failed = 0, []
    for student_id, samples in store.list_face_samples().items():
        for sample in samples:
            try:
                image_bytes = supabase_storage.download_object(sample["storage_path"])
                embedding = vision_service.extract_face_embedding(image_bytes)
            except vision_service.VisionConfigurationError as error:
                return jsonify(error=str(error)), 503
            except supabase_storage.StorageConfigurationError as error:
                return jsonify(error=str(error)), 503
            except (supabase_storage.StorageRequestError, ValueError) as error:
                failed.append(f"{student_id}: {error}")
                continue
            store.update_face_sample_embedding(sample["id"], embedding, vision_service.face_model_version())
            trained += 1
    _face_samples.clear()
    return jsonify(
        message=f"Retrained {trained} face sample(s)." + (f" {len(failed)} could not be used." if failed else ""),
        trained=trained,
        failed=failed,
    )


# ----------------------------------------------------------------------------- admin: reports

def _report_rows(start, end, faculty):
    students = {record.get("studentID"): record for record in store.list_records("Student")}
    rows = []
    for record in store.list_records("blocked"):
        if not start <= record.get("date", "") <= end:
            continue
        student = students.get(record.get("studentID"), {})
        if faculty and student.get("faculty") != faculty:
            continue
        rows.append({
            "blockedID": record.get("blockedID", ""),
            "timestamp": f'{record.get("date", "")} {record.get("time", "")}'.strip(),
            "studentName": record.get("studentName") or student.get("studentName", ""),
            "studentID": record.get("studentID", ""),
            "faculty": student.get("faculty", ""),
            "guardID": record.get("guardID", ""),
        })
    rows.sort(key=lambda row: row["timestamp"])
    return rows


def _report_params(source):
    start = str(source.get("start", "")).strip()
    end = str(source.get("end", "")).strip()
    faculty = str(source.get("faculty", "")).strip().upper()
    try:
        start_date, end_date = date.fromisoformat(start), date.fromisoformat(end)
    except ValueError as error:
        raise ValueError("Choose a valid start and end date.") from error
    if end_date < start_date:
        raise ValueError("The end date must be on or after the start date.")
    if faculty and faculty not in FACULTIES:
        raise ValueError("Choose a faculty from the list.")
    return start, end, faculty


def _report_csv(rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Blocked ID", "Time Stamp", "Student Name", "Student ID", "Faculty", "Guard ID"])
    for row in rows:
        writer.writerow([row["blockedID"], row["timestamp"], row["studentName"],
                         row["studentID"], row["faculty"], row["guardID"]])
    return buffer.getvalue().encode("utf-8-sig")  # BOM so Excel opens it as UTF-8


def _report_filename(start, end, faculty):
    return f"Report_{start}_{end}_{faculty or 'ALL'}.csv"


@app.get("/api/admin/reports")
@_web_api("admin")
def api_report():
    try:
        start, end, faculty = _report_params(request.args)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(rows=_report_rows(start, end, faculty))


@app.get("/admin/reports/download")
@_web_page("admin")
def admin_report_download():
    try:
        start, end, faculty = _report_params(request.args)
    except ValueError as error:
        return str(error), 400
    return Response(
        _report_csv(_report_rows(start, end, faculty)),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{_report_filename(start, end, faculty)}"'},
    )


@app.post("/api/admin/reports/email")
@_web_api("admin")
def api_email_report():
    payload = request.get_json(silent=True) or {}
    try:
        start, end, faculty = _report_params(payload)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    recipient = str(payload.get("email", "")).strip()
    if "@" not in recipient or any(char in recipient for char in "\r\n,;"):
        return jsonify(error="Enter one valid recipient email address."), 400
    audience = faculty or "all faculties"
    try:
        _send_email(
            recipient,
            "Blocked Student Report",
            f"Dear {audience},\n\nThis is the latest report of the Blocked Student List for {audience} "
            f"from {start} to {end}.\n\n\n**This is an auto-generated email, please do not reply.",
            (_report_filename(start, end, faculty), _report_csv(_report_rows(start, end, faculty)), "text", "csv"),
        )
    except RuntimeError as error:
        return jsonify(error=str(error)), 503
    except (OSError, smtplib.SMTPException):
        logger.exception("Could not send the report email.")
        return jsonify(error="Could not send the report email. Try again later."), 503
    return jsonify(message=f"Report sent to {recipient}.")


# ----------------------------------------------------------------------------- guard dashboard

@app.get("/dashboard")
@_web_page("security")
def dashboard():
    context = _page_context("monitoring")
    return render_template(
        "dashboard.html", guard_id=context["account_id"], guard_name=context["account_name"], **context
    )


@app.get("/api/blocked")
@_web_api("security")
def list_blocked():
    student_id = request.args.get("student_id", "").strip().upper()
    if student_id and not _student_record(student_id):
        return jsonify(error=f"Student ID {student_id} was not found."), 404
    return jsonify(rows=_blocked_rows(session["account_id"], student_id or None))


@app.post("/api/blocked")
@_web_api("security")
def add_blocked():
    payload = request.get_json(silent=True) or {}
    student_id = str(payload.get("student_id", "")).strip().upper()
    if not student_id:
        return jsonify(error="Enter a student ID."), 400
    student = _student_record(student_id)
    if not student:
        return jsonify(error=f"Student ID {student_id} was not found."), 404
    if _blocked_today(student_id):
        return jsonify(error=f"Student ID {student_id} is already blocked today."), 409
    _block_student(student, session["account_id"])
    return jsonify(rows=_blocked_rows(session["account_id"]), message="Blocked record added."), 201


def _own_blocked_today(blocked_id):
    record = store.get_record("blocked", blocked_id)
    if not record or record.get("guardID") != session["account_id"] or record.get("date") != _today():
        return None
    return record


@app.delete("/api/blocked/<blocked_id>")
@_web_api("security")
def delete_blocked(blocked_id):
    record = _own_blocked_today(blocked_id)
    if record is None:
        return jsonify(error="Today's blocked record was not found."), 404
    _return_student(record, session["account_id"])
    return jsonify(rows=_blocked_rows(session["account_id"]), message="Record removed and return logged.")


@app.patch("/api/blocked/<blocked_id>")
@_web_api("security")
def update_blocked(blocked_id):
    payload = request.get_json(silent=True) or {}
    student_id = str(payload.get("student_id", "")).strip().upper()
    if not student_id:
        return jsonify(error="Enter the correct student ID."), 400
    record = _own_blocked_today(blocked_id)
    if record is None:
        return jsonify(error="Today's blocked record was not found."), 404
    student = _student_record(student_id)
    if not student:
        return jsonify(error=f"Student ID {student_id} was not found."), 404
    if student_id != record.get("studentID") and _blocked_today(student_id):
        return jsonify(error=f"Student ID {student_id} is already blocked today."), 409

    record.update({
        "time": datetime.now().strftime("%H:%M:%S"),
        "studentID": student_id,
        "studentName": student.get("studentName", ""),
        "guardID": session["account_id"],
    })
    store.save_record("blocked", record, record_id=blocked_id)
    _remove_today_returns(student_id)
    return jsonify(rows=_blocked_rows(session["account_id"]), message="Blocked record updated.")


# ----------------------------------------------------------------------------- guard monitoring

@app.post("/api/vision/frame")
@_web_api("security")
def api_vision_frame():
    """One monitoring step: recognize the face, then (if recognized) scan the attire."""
    try:
        image = _decode_frame(request.get_json(silent=True))
        match = vision_service.match_face(image, _face_samples.get())
    except vision_service.VisionConfigurationError as error:
        return jsonify(error=str(error)), 503
    except ValueError as error:
        return jsonify(error=str(error)), 400

    student = _student_record(match["student_id"])
    result = {
        "student_id": student["studentID"] if student else None,
        "student_name": (student or {}).get("studentName"),
        "similarity": match["similarity"],
        "threshold": match["threshold"],
        "face_box": match["face_box"],
        "detections": [],
        "violation": None,
        "returned": False,
        "yolo_error": None,
    }
    if student is None:
        return jsonify(result)

    try:
        detections = vision_service.detect_attire(image)
    except vision_service.VisionConfigurationError as error:
        result["yolo_error"] = str(error)
        return jsonify(result)
    result["detections"] = detections

    student_id = student["studentID"]
    blocked = _blocked_today(student_id)
    if detections:
        _proper_attire_streak.pop(student_id, None)
        result["violation"] = {
            "reason": vision_service.describe_detections(detections),
            "already_blocked": bool(blocked),
        }
    elif blocked:
        # A blocked student came back with proper clothing: move them to the returns list.
        streak = _proper_attire_streak.get(student_id, 0) + 1
        if streak >= AUTO_RETURN_CONFIRMATIONS:
            _proper_attire_streak.pop(student_id, None)
            for record in blocked:
                _return_student(record, session["account_id"])
            result["returned"] = True
            result["rows"] = _blocked_rows(session["account_id"])
        else:
            _proper_attire_streak[student_id] = streak
    else:
        _proper_attire_streak.pop(student_id, None)
    return jsonify(result)


def _face_box(payload):
    box = payload.get("face_box") if isinstance(payload, dict) else None
    if isinstance(box, list) and len(box) == 4 and all(isinstance(value, (int, float)) for value in box):
        return [float(value) for value in box]
    return None


@app.post("/api/vision/acknowledge")
@_web_api("security")
def api_vision_acknowledge():
    """Guard confirms the violation: block the student and save the face photo as evidence."""
    payload = request.get_json(silent=True) or {}
    student_id = str(payload.get("student_id", "")).strip().upper()
    student = _student_record(student_id)
    if student is None:
        return jsonify(error=f"The student ID {student_id} does not exist!"), 404
    if _blocked_today(student_id):
        return jsonify(message=f"{student_id} is already blocked today.", rows=_blocked_rows(session["account_id"]))
    try:
        image = _decode_frame(payload)
        evidence = vision_service.encode_jpeg(image, _face_box(payload))
    except (ValueError, vision_service.VisionConfigurationError) as error:
        return jsonify(error=str(error)), 400

    path = f"violations/{_today()}-{student_id}-{uuid.uuid4().hex[:8]}.jpg"
    warning = _upload_or_warn(path, evidence, "violation photo")
    _block_student(student, session["account_id"], None if warning else path)
    return jsonify(
        message=f"{student_id} {student.get('studentName', '')} added to today's blocked list.",
        warning=warning,
        rows=_blocked_rows(session["account_id"]),
    )


@app.post("/api/vision/revoke")
@_web_api("security")
def api_vision_revoke():
    """Guard rejects the detection: undo today's block and keep the frame for re-annotation."""
    payload = request.get_json(silent=True) or {}
    student_id = str(payload.get("student_id", "")).strip().upper()
    for record in _blocked_today(student_id):
        _return_student(record, session["account_id"])
    warning = None
    try:
        frame = vision_service.encode_jpeg(_decode_frame(payload))
        warning = _upload_or_warn(f"active-learning/{_today()}/{uuid.uuid4().hex}.jpg", frame, "revoked frame")
    except (ValueError, vision_service.VisionConfigurationError) as error:
        warning = str(error)
    return jsonify(message="Violation revoked.", warning=warning, rows=_blocked_rows(session["account_id"]))


@app.get("/api/students/<student_id>")
@_web_api("admin", "security")
def api_student(student_id):
    student = _student_record(student_id.strip().upper())
    if student is None:
        return jsonify(error=f"The student ID {student_id.upper()} does not exist!"), 404
    has_photo = bool(store.list_face_samples([student["studentID"]]).get(student["studentID"]))
    return jsonify(student={**student, "hasPhoto": has_photo})


@app.get("/api/students/<student_id>/photo")
@_web_api("admin", "security")
def api_student_photo(student_id):
    """Reference photo shown in the violation alert (first face sample)."""
    student_id = student_id.strip().upper()
    samples = store.list_face_samples([student_id]).get(student_id)
    if not samples:
        return jsonify(error="This student has no photo."), 404
    return _image_response(samples[0]["storage_path"])


@app.get("/api/blocked/<blocked_id>/photo")
def api_blocked_photo(blocked_id):
    """Violation evidence photo, for the guard dashboard (session) or the Android app (bearer)."""
    record = store.get_record("blocked", blocked_id)
    api_user = _api_user()
    if api_user is not None:
        visible = any(
            item.get("blockedID") == blocked_id for item in _records_visible_to(api_user, "blocked")
        )
    elif _session_user() is not None and record is not None:
        role = session["account_role"]
        if role == "lecturer":
            visible = any(item.get("blockedID") == blocked_id
                          for item in _records_visible_to(_lecturer_user(), "blocked"))
        else:
            visible = role == "admin" or record.get("guardID") == session.get("account_id")
    else:
        visible = False
    if not visible or not record:
        return jsonify(error="Record not found."), 404
    if not record.get("photoPath"):
        return jsonify(error="This record has no photo."), 404
    return _image_response(record["photoPath"])


# ----------------------------------------------------------------------------- admin: security guards

def _guard_payload(payload, *, new):
    if not isinstance(payload, dict):
        raise ValueError("A JSON object is required.")
    record = {
        "guardName": str(payload.get("guardName", "")).strip(),
        "guardPhoneNo": str(payload.get("guardPhoneNo", "")).strip(),
    }
    if not record["guardName"]:
        raise ValueError("Guard name is required.")
    password = str(payload.get("guardPassword", "") or "")
    if password or new:
        if len(password) < 8:
            raise ValueError("The password must contain at least 8 characters.")
        record["guardPassword"] = password
    return record


@app.get("/admin/guards")
@_web_page("admin")
def admin_guards():
    return render_template("admin_guards.html", **_page_context("guards"))


@app.get("/api/admin/guards")
@_web_api("admin")
def api_list_guards():
    query = request.args.get("q", "").strip().casefold()
    guards = [guard for guard in store.list_records("security")
              if query in guard.get("guardName", "").casefold() or query in guard["guardID"].casefold()]
    return jsonify(guards=guards)


@app.post("/api/admin/guards")
@_web_api("admin")
def api_create_guard():
    try:
        record = _guard_payload(request.get_json(silent=True), new=True)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    numbers = [int(digits) for guard in store.list_records("security")
               if (digits := "".join(filter(str.isdigit, guard["guardID"])))]
    record["guardID"] = f"SG{max(numbers, default=0) + 1:05d}"
    record["adminID"] = session["account_id"]
    guard = store.save_record("security", record)
    return jsonify(guard=guard, message=f"Security guard {guard['guardID']} added."), 201


@app.put("/api/admin/guards/<guard_id>")
@_web_api("admin")
def api_update_guard(guard_id):
    if store.get_record("security", guard_id) is None:
        return jsonify(error="Security guard was not found."), 404
    try:
        record = _guard_payload(request.get_json(silent=True), new=False)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    guard = store.save_record("security", record, record_id=guard_id)
    _session_users.clear()
    return jsonify(guard=guard, message=f"Security guard {guard_id} updated.")


@app.delete("/api/admin/guards/<guard_id>")
@_web_api("admin")
def api_delete_guard(guard_id):
    if not store.delete_record("security", guard_id):
        return jsonify(error="Security guard was not found."), 404
    _session_users.clear()
    return jsonify(message=f"Security guard {guard_id} deleted.")


# ----------------------------------------------------------------------------- lecturer

def _lecturer_user():
    return {"id": session["account_id"], "role": "lecturer"}


@app.get("/lecturer")
@_web_page("lecturer")
def lecturer_today():
    return render_template("lecturer.html", page="today", today=_today(), **_page_context("today"))


@app.get("/lecturer/returns")
@_web_page("lecturer")
def lecturer_returns():
    return render_template("lecturer.html", page="returns", today=_today(), **_page_context("returns"))


@app.get("/lecturer/history")
@_web_page("lecturer")
def lecturer_history():
    return render_template("lecturer.html", page="history", today=_today(), **_page_context("history"))


def _date_arg(name, default=""):
    value = request.args.get(name, "").strip() or default
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ValueError(f"Choose a valid {name} date.") from error


@app.get("/api/lecturer/history")
@_web_api("lecturer")
def api_lecturer_history():
    """Number of students blocked per day (the notification collection) within a date range."""
    try:
        start = _date_arg("start", "2000-01-01")
        end = _date_arg("end", _today())
    except ValueError as error:
        return jsonify(error=str(error)), 400
    rows = [row for row in store.list_records("notification") if start <= row["date"] <= end]
    rows.sort(key=lambda row: row["date"], reverse=True)
    return jsonify(rows=rows)


@app.get("/api/lecturer/<resource>")
@_web_api("lecturer")
def api_lecturer_records(resource):
    """Blocked / returned students of the lecturer's classes on one date."""
    if resource not in {"blocked", "returns"}:
        return jsonify(error="Unknown list."), 404
    try:
        day = _date_arg("date", _today())
    except ValueError as error:
        return jsonify(error=str(error)), 400
    rows = _records_visible_to(_lecturer_user(), resource, {"date": day})
    for row in rows:
        row["hasPhoto"] = bool(row.pop("photoPath", None))
    rows.sort(key=lambda row: row.get("time", ""), reverse=True)
    return jsonify(rows=rows, date=day)


# ----------------------------------------------------------------------------- profile & password

PROFILE_FIELDS = {
    "admin": [("adminID", "Admin ID"), ("adminName", "Name"), ("adminEmail", "Email"), ("adminPhoneNo", "Phone")],
    "security": [("guardID", "Guard ID"), ("guardName", "Name"), ("guardPhoneNo", "Phone"), ("adminID", "Created by")],
    "lecturer": [("lecturerID", "Lecturer ID"), ("lecturerName", "Name"), ("lecturerEmail", "Email")],
}


@app.get("/profile")
@_web_page("admin", "security", "lecturer")
def profile():
    user = _session_user()
    fields = [(label, user.get(field, "")) for field, label in PROFILE_FIELDS[session["account_role"]]]
    return render_template("profile.html", fields=fields, **_page_context("profile"))


@app.post("/api/profile/password")
@_web_api("admin", "security", "lecturer")
def api_change_password():
    payload = request.get_json(silent=True) or {}
    role, account_id = session["account_role"], session["account_id"]
    if store.authenticate(role, account_id, str(payload.get("current", ""))) is None:
        return jsonify(error="Your current password is incorrect."), 400
    new_password = str(payload.get("new", ""))
    if len(new_password) < 8:
        return jsonify(error="The new password must contain at least 8 characters."), 400
    store.save_record(role, {store.ACCOUNT_FIELDS[role][0]: new_password}, record_id=account_id)
    return jsonify(message="Password changed.")


@app.get("/forgot-password")
def forgot_password():
    return render_template("forgot_password.html")


# ----------------------------------------------------------------------------- Android app API

@app.post("/api/auth/login")
def api_login():
    payload = request.get_json(silent=True) or {}
    role = str(payload.get("role", "")).strip().lower()
    account_id = str(payload.get("id", "")).strip().upper()
    password = str(payload.get("password", ""))
    if role not in {"admin", "security", "lecturer"} or not account_id or not password:
        return jsonify(error="Provide a supported role, account ID, and password."), 400
    account = store.authenticate(role, account_id, password)
    if account is None:
        return jsonify(error="Invalid login credentials."), 401
    token = token_serializer.dumps({"id": account_id, "role": role})
    return jsonify(access_token=token, token_type="bearer", user=account)


def _reset_code_hash(role, account_id, code):
    return hmac.new(
        app.config["SECRET_KEY"].encode("utf-8"),
        f"{role}:{account_id}:{code}".encode("utf-8"),
        "sha256",
    ).hexdigest()


@app.post("/api/auth/password-reset/request")
def api_request_password_reset():
    payload = request.get_json(silent=True) or {}
    account_id = str(payload.get("id", "")).strip().upper()
    if not account_id:
        return jsonify(error="Enter an account ID."), 400

    for role in ("admin", "lecturer"):
        email = store.account_email(role, account_id)
        if not email:
            continue
        code = f"{secrets.randbelow(1_000_000):06d}"
        now = int(datetime.now().timestamp())
        if not store.save_password_reset_challenge(
            role, account_id, _reset_code_hash(role, account_id, code), now + 600, now
        ):
            break
        try:
            _send_email(
                email,
                "Password reset verification code",
                f"Your password reset code is {code}. It expires in 10 minutes.",
            )
        except RuntimeError:
            logger.error("Password reset requested without complete SMTP configuration.")
            return jsonify(error="Password reset email is not configured on the server."), 503
        except (OSError, smtplib.SMTPException, ValueError):
            logger.exception("Could not send password reset email for account role %s.", role)
            return jsonify(error="Could not send the reset email. Try again later."), 503
        break

    return jsonify(message="If the account is eligible, a verification code has been sent.")


@app.post("/api/auth/password-reset/confirm")
def api_confirm_password_reset():
    payload = request.get_json(silent=True) or {}
    account_id = str(payload.get("id", "")).strip().upper()
    code = str(payload.get("code", "")).strip()
    password = str(payload.get("password", ""))
    if not account_id or not code or not password:
        return jsonify(error="Enter the account ID, verification code, and new password."), 400
    if len(password) < 8:
        return jsonify(error="The new password must contain at least 8 characters."), 400

    for role in ("admin", "lecturer"):
        if store.complete_password_reset(
            role, account_id, _reset_code_hash(role, account_id, code), password,
            int(datetime.now().timestamp()),
        ):
            return jsonify(message="Password updated. You can now sign in.")
    return jsonify(error="The verification code is invalid or expired."), 400


@app.get("/api/auth/me")
@_api_authenticated
def api_me():
    user = request.api_user
    profile = store.get_record(user["role"], user["id"])
    if profile is None:
        return jsonify(error="Account no longer exists."), 401
    return jsonify(user={"id": user["id"], "role": user["role"], **profile})


def _records_visible_to(user, resource, filters=None):
    filters = dict(filters or {})
    role = user["role"]
    if resource in {"admin", "security", "lecturer"}:
        if resource != role:
            return []
        if role != "admin":
            filters[store.RESOURCE_KEYS[resource]] = user["id"]

    if role == "security" and resource in {"blocked", "returns"}:
        filters["guardID"] = user["id"]

    if role == "lecturer":
        if resource in {"blocked", "returns", "Student", "classDetails"}:
            class_ids = {record.get("classID") for record in store.list_records("class", {"lecturerID": user["id"]})}
            student_ids = {
                record.get("studentID")
                for record in store.list_records("classDetails")
                if record.get("classID") in class_ids
            }
            if resource == "classDetails":
                return [record for record in store.list_records(resource, filters)
                        if record.get("classID") in class_ids]
            return [record for record in store.list_records(resource, filters)
                    if record.get("studentID") in student_ids]
        if resource == "class":
            filters["lecturerID"] = user["id"]
        elif resource != "notification":
            return []

    return store.list_records(resource, filters)


@app.get("/api/records/<resource>")
@_api_authenticated
def api_list_records(resource):
    if resource not in store.RESOURCE_KEYS:
        return jsonify(error="Unknown resource."), 404
    filters = {
        key: request.args.get(key)
        for key in ("date", "status", "studentID", "guardID", "lecturerID", "classID")
        if request.args.get(key)
    }
    return jsonify(records=_records_visible_to(request.api_user, resource, filters))


def _can_write(user, resource):
    return user["role"] == "admin" or (user["role"] == "security" and resource in {"blocked", "returns"})


@app.route("/api/records/<resource>/<record_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
@_api_authenticated
def api_record(resource, record_id):
    if resource not in store.RESOURCE_KEYS:
        return jsonify(error="Unknown resource."), 404
    user = request.api_user
    if request.method == "GET":
        record = next(
            (item for item in _records_visible_to(user, resource)
             if item.get(store.RESOURCE_KEYS[resource]) == record_id),
            None,
        )
        return (jsonify(record=record), 200) if record else (jsonify(error="Record not found."), 404)
    if not _can_write(user, resource):
        return jsonify(error="Your account cannot change this resource."), 403
    existing = store.get_record(resource, record_id)
    if user["role"] == "security" and (not existing or existing.get("guardID") != user["id"]):
        return jsonify(error="Record not found."), 404
    if request.method == "DELETE":
        deleted = store.delete_record(resource, record_id)
        return (jsonify(message="Record deleted."), 200) if deleted else (jsonify(error="Record not found."), 404)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="A JSON object is required."), 400
    if user["role"] == "security":
        payload["guardID"] = user["id"]
    if request.method == "PATCH":
        if existing is None:
            return jsonify(error="Record not found."), 404
        payload = {**existing, **payload}
    try:
        record = store.save_record(resource, payload, record_id=record_id)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(record=record)


@app.post("/api/records/<resource>")
@_api_authenticated
def api_create_record(resource):
    if resource not in store.RESOURCE_KEYS:
        return jsonify(error="Unknown resource."), 404
    user = request.api_user
    if not _can_write(user, resource):
        return jsonify(error="Your account cannot create this resource."), 403
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="A JSON object is required."), 400
    if user["role"] == "security":
        payload["guardID"] = user["id"]
    if resource in store.ID_FORMATS and not payload.get(store.RESOURCE_KEYS[resource]):
        payload[store.RESOURCE_KEYS[resource]] = store.next_id(resource)
    is_new_block = resource == "blocked" and not store.get_record(resource, payload[store.RESOURCE_KEYS[resource]])
    try:
        record = store.save_record(resource, payload)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    if is_new_block:
        store.count_blocked_student(record["date"])
    return jsonify(record=record), 201


# ----------------------------------------------------------------------------- errors

@app.errorhandler(HTTPException)
def handle_http_error(error):
    if request.path.startswith("/api/"):
        return jsonify(error=error.description), error.code
    return error.description, error.code


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    logger.exception("Unhandled web application error")
    if request.path.startswith("/api/"):
        return jsonify(error="The request could not be completed. Check the server log for details."), 500
    return "The request could not be completed. Check the server log for details.", 500


if __name__ == "__main__" or os.environ.get("ATTIRE_WARM_UP") == "1":
    # Load the face and YOLO models now so the guard's first scan isn't an 8-second wait.
    threading.Thread(target=vision_service.warm_up, daemon=True).start()

if __name__ == "__main__":
    app.run(
        host=os.environ.get("ATTIRE_WEB_HOST", "127.0.0.1"),
        port=int(os.environ.get("ATTIRE_WEB_PORT", "5000")),
    )
