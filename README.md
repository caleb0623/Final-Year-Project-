---
title: TAR UMT Attire Checker
emoji: 👔
colorFrom: red
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
short_description: Face recognition and attire monitoring for TAR UMT
---

# 🎓 Attire Checker System

> **AI-powered student identification and attire monitoring**: a Final Year Project at Tunku Abdul Rahman University of Management and Technology (TARUMT).

The system recognises a student's face at the campus entrance, scans their clothing for dress-code violations with YOLOv7, and keeps a daily blocked list that security guards, administrators and lecturers can act on.

It runs as a **website** (Flask) for administrators and security guards, plus an **Android app** for mobile access. All data is stored in **Supabase**: Postgres for records and private Storage for images.

---

## ✨ Features

### Administrator
| Feature | Where |
|---|---|
| Sign in | `/` (account type: Administrator) |
| Add / edit / delete student records (ID, name, faculty, programme, contact) | Students & faces |
| **Register face with camera**: captures 8 samples while the student moves their face | Students & faces → Train face |
| **Register face from gallery**: upload one or more photos | Students & faces → Train face |
| **Train**: every sample becomes an SFace face template; *Retrain all faces* rebuilds them from the photos in Supabase | Students & faces |
| **Generate report**: blocked students for a date range and faculty, preview, download CSV, or email it | Reports |

### Security guard
| Feature | Where |
|---|---|
| Sign in | `/` (account type: Security guard) |
| Today's blocked list for this guard: search by student ID, refresh | Dashboard |
| Add / update (correct the student ID) / remove a record (removal logs a *return*) | Dashboard |
| **Face recognition + attire scan**: the browser camera sends a frame every second; the face is matched, then YOLOv7 scans the attire | Dashboard → Open camera |
| **Violation alert**: student's enrolled photo, editable student ID, reason (e.g. `1 Crop_Top`), alarm sound | pops up automatically |
| **Acknowledge**: blocks the student and saves the face photo as evidence | violation alert |
| **Revoke**: undoes today's block and saves the frame for re-annotation (active learning) | violation alert |
| **Auto-return**: a blocked student who comes back properly dressed is moved to the returns list | automatic |

YOLOv7 classes: `Crop_Top`, `Miniskirt`, `Ripped_Pants`, `Shorts`, `Sleeveless` (dataset: `Assembled-5/data.yaml`).

---

## 🏗️ Architecture

```
Browser (admin / guard)            Android app (lecturer / guard / admin)
   │  session cookie + CSRF            │  bearer token
   └──────────────┬────────────────────┘
                  ▼
        Flask  web_app.py
          ├─ vision_service.py ── YuNet face detection + SFace face templates  (models/*.onnx)
          │                    └─ attire_detector.py → YOLOv7 (models/, utils/)  (YOLO_WEIGHTS)
          ├─ postgres_store.py ── Supabase Postgres  (SQLAlchemy + psycopg, session pooler)
          └─ supabase_storage.py ─ Supabase Storage, private bucket (server-side secret key)
```

The camera runs in the browser; frames are sent to the server, which does all of the AI work. The browser never receives database or storage credentials.

### Data in Supabase

The tables, Row Level Security and the bucket are **created automatically** the first time the app starts (`postgres_store.init_store()`).

Each Firestore collection has its own table. The JSON used by the website and the Android app keeps the Firestore field names (`studentID`, `guardName`, …), while the columns are snake_case.

| Firestore collection | Table (primary key) | Columns | Purpose |
|---|---|---|---|
| `Student` | `student` (`student_id`) | name, faculty, programme, semester, year_of_study, tutorial_group, email, phone, status | Student details |
| `admin` | `admin` (`admin_id`) | name, email, phone, password_hash, login_date, status | Administrator details |
| `security` | `security` (`guard_id`) | name, phone, admin_id → admin, password_hash | Security guard details |
| `lecturer` | `lecturer` (`lecturer_id`) | name, email, password_hash, login_date, status | Lecturer details |
| `class` | `class` (`class_id`) | class_date, class_time, class_type, course_id, lecturer_id → lecturer | Classes and who teaches them |
| `classDetails` | `class_details` (`detail_id`) | class_id → class, student_id → student | Which students attend which class |
| `blocked` | `blocked` (`blocked_id`, e.g. `BL00000001`) | date, time, student_id, student_name, guard_id, status, photo_path | Students blocked for a violation |
| `returns` | `returns` (`return_id`, e.g. `R00000001`) | date, time, student_id, student_name, guard_id, status | Blocked students who came back properly dressed |
| `notification` | `notification` (`date`) | totalnum | Number of students blocked on that date; the server adds 1 for every new block |
| *(new)* | `student_face_samples` | student_id → student, storage_path, embedding | Face templates for recognition |
| *(new)* | `password_reset_challenges` | role, account_id, code_hash, expiry | Android password-reset codes |

Passwords (`adminPassword`, `guardPassword`, `lecturerPw`) are stored only as PBKDF2 hashes in `password_hash` and are never returned by the API. Deleting a student also removes their class enrolments and face samples.

RLS is enabled on every table with no policies, so the public Supabase Data API cannot read them. The Flask server connects as the database owner and is unaffected.

Storage bucket (private, default name `student-faces`):

| Path | Written when |
|---|---|
| `faces/<studentID>/<uuid>.jpg` | an admin trains a face |
| `violations/<date>-<studentID>-<id>.jpg` | a guard acknowledges a violation (linked from the blocked record's `photoPath`) |
| `active-learning/<date>/<uuid>.jpg` | a guard revokes a detection |

---

## 📦 Setup

### 1. Python environment (Python 3.10–3.12)
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate on macOS/Linux)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu   # or a CUDA build
pip install -r requirements.txt
```

### 2. Models
| File | Notes |
|---|---|
| `models/face_detection_yunet_2023mar.onnx` | from [opencv_zoo](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) |
| `models/face_recognition_sface_2021dec.onnx` | from [opencv_zoo](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface) |
| `models/attire-best.pt` | **your trained YOLOv7 attire weights** (previously `tiny6.pt`); set `YOLO_WEIGHTS` if stored elsewhere |

Model files are git-ignored. Without the YOLO weights, face recognition still works and the camera shows "Attire check unavailable".

### 3. Supabase settings (`.env`)
Copy `.env.example` to `.env` and fill in:

| Variable | Where to find it |
|---|---|
| `DATABASE_URL` | Dashboard → **Connect** → *Session pooler* (port 5432). Use the `postgresql+psycopg://` scheme and URL-encode special characters in the password. |
| `SUPABASE_URL` | Dashboard → Project Settings → API |
| `SUPABASE_SECRET_KEY` | Dashboard → Project Settings → **API Keys → Secret key** (`sb_secret_...`). Server only. |
| `SUPABASE_STORAGE_BUCKET` | Bucket name (created automatically, private) |
| `AUTO_RETURN_CONFIRMATIONS` (optional) | Consecutive proper-attire scans before a blocked student is returned (default 2) |
| `ATTIRE_WEB_SECRET` | Any long random string |
| `SMTP_*` (optional) | For emailing reports and password-reset codes |

### 4. Create the first accounts
```bash
python create_account.py --role admin --id AD00001 --name "Admin Name" --email admin@example.com
python create_account.py --role security --id SG00001 --name "Guard Name" --admin-id AD00001
```

### 5. Run
```bash
python web_app.py                 # http://127.0.0.1:5000
python -m unittest discover tests
```
The browser camera needs **localhost or HTTPS**. For a deployment behind HTTPS set `ATTIRE_WEB_HTTPS=1` (secure cookies) and `ATTIRE_WEB_HOST=0.0.0.0`.

---

## 🚀 Deploying (going live)

The website pages, the browser/Android API and the AI models are **one Flask app**, deployed as one Docker container. There is no separate frontend to host. The database and images stay in Supabase.

```
Browser / Android app ──HTTPS──▶ Docker container (Flask + gunicorn + YuNet/SFace + YOLOv7) ──▶ Supabase (Postgres + Storage)
```

The model files are not in git (the repo is public). On first start, the container downloads them from the private bucket's `models/` folder (`attire-best.pt`, `face_detection_yunet_2023mar.onnx`, `face_recognition_sface_2021dec.onnx`). To update the attire model, upload a new `models/attire-best.pt` there and restart.

**Recommended: Hugging Face Spaces** (free CPU tier: 2 vCPU, 16 GB RAM)
1. huggingface.co → New Space → SDK **Docker** → Blank → hardware *CPU basic (free)*.
2. In the Space → Settings → **Variables and secrets**, add the secrets `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY` and `ATTIRE_WEB_SECRET`, and the variable `SUPABASE_STORAGE_BUCKET=student-faces`. Optionally add `SMTP_*`.
3. Push this repository to the Space: `git remote add space https://huggingface.co/spaces/<user>/<space>` then `git push space main`. The Space's README needs the header `sdk: docker` and `app_port: 7860`.
4. The site is served at `https://<user>-<space>.hf.space`. HTTPS is included, which the browser camera requires.

**Render**: New → Web Service → connect this GitHub repo. It detects the `Dockerfile` (or use `render.yaml`). Add the same environment variables. The **free plan (512 MB RAM, 0.1 CPU) is too small** for PyTorch + YOLO; use at least *Starter*.

Free tiers sleep when idle, so the first request after a pause takes about a minute while the models load. After deploying, set the Android app's `ATTIRE_API_BASE_URL` Gradle property to the new HTTPS address.

---

## 🔁 Migrating from Firebase

`migrate_firebase.py` copies the old Firestore collections and Firebase Storage images into Supabase. Firebase itself is left unchanged.

```bash
pip install -r requirements-migrate.txt
set GOOGLE_APPLICATION_CREDENTIALS=path\to\firebase-service-account.json
python migrate_firebase.py                       # dry run: shows what would be copied
python migrate_firebase.py --apply --images      # records + Firebase Storage images
python migrate_firebase.py --apply --no-firestore --local-dir .   # leftover local image folders
```

| Old image | New location |
|---|---|
| Firebase `students/<id>` / local `students/<id>.jpg` | `faces/<id>/legacy.jpg`, plus a face template, so migrated students are recognised right away |
| Firebase `<date>-<id>` / local `saveid/<date>-<id>.jpg` | `violations/<date>-<id>.jpg`, linked to that day's blocked record |
| local `activeLearning/*.png` | `active-learning/legacy/*.jpg` |

Passwords are re-hashed during migration (Firestore stored them in plain text).

---

## 📱 Android app

`Mobile Application/` talks only to the Flask API (`/api/auth/*`, `/api/records/*`, and `/api/blocked/<id>/photo` for violation photos). Set the server address with the Gradle property `ATTIRE_API_BASE_URL` (default `http://10.0.2.2:5000/`, which is the host machine from the emulator). Firebase is no longer used by the app.

---

## 📁 Project structure

```
web_app.py             Flask routes: admin, guard, Android API
vision_service.py      face detection / templates / matching, attire scan wrapper
attire_detector.py     YOLOv7 inference
postgres_store.py      Supabase Postgres tables and queries
supabase_storage.py    Supabase Storage (private bucket)
migrate_firebase.py    one-off Firebase → Supabase migration
create_account.py      create admin / guard / lecturer accounts
templates/, static/    website pages, JS, CSS, alarm sound
models/, utils/        YOLOv7 network code needed to load the weights; face ONNX models
Assembled-5/           attire dataset labels (Roboflow, CC BY 4.0)
Mobile Application/    Android app (Kotlin)
tests/                 unit tests (run against in-memory SQLite)
```

---

## 🔬 Technical notes

- **Face recognition** replaced the notebook's Haar cascade + LBPH (`trainer.yml` + `names.pkl`) with YuNet + SFace. Each sample is a normalised 128-d template, and a frame matches the student with the highest cosine similarity if it is ≥ `FACE_MATCH_THRESHOLD` (default 0.363, the value OpenCV recommends for SFace). Images are scaled to at most 640 px before detection, because YuNet loses accuracy on full-resolution phone photos. Adding a student only adds templates; nothing has to be retrained from scratch.
- **Attire detection** runs only after a face is recognised, as in the original flow. Any YOLO detection (confidence ≥ 0.5) counts as a violation.
- **Auto-return**: a blocked student is moved to returns after `AUTO_RETURN_CONFIRMATIONS` (default 2) consecutive proper-attire scans, so a single frame where YOLO misses the clothing doesn't release them.
- **YOLOv7** network code is from [WongKinYiu/yolov7](https://github.com/WongKinYiu/yolov7) (GPL-3.0, see `LICENSE.md`); only the parts needed for inference are kept. Requires `torch < 2.6`.
