"""Supabase Postgres storage: one table per original Firestore collection.

Python attribute names (and therefore the JSON used by the website and Android app) keep the
Firestore field names (studentID, guardName, ...); the database columns use snake_case.

    Firestore collection   Postgres table    primary key
    Student                student           student_id
    admin                  admin             admin_id
    security               security          guard_id      (guards; admin_id -> admin)
    lecturer               lecturer          lecturer_id
    class                  class             class_id      (lecturer_id -> lecturer)
    classDetails           class_details     detail_id     (class_id -> class, student_id -> student)
    blocked                blocked           blocked_id    (students blocked for an attire violation)
    returns                returns           return_id     (blocked students who came back properly dressed)
    notification           notification      date          (total students blocked on that date)

Passwords are never stored in plain text: adminPassword / guardPassword / lecturerPw are hashed
into the account table's password_hash column and never returned.
"""
import hashlib
import hmac
import os
import re
import secrets
from datetime import date, datetime, time, timezone

from dotenv import load_dotenv
from sqlalchemy import (
    JSON, Date, DateTime, ForeignKey, Integer, String, Time, create_engine, func, inspect, select, text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

import supabase_storage


load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./attire-local.db")
# No pre-ping: it costs an extra ~90 ms round trip to Supabase on every query. Connections are
# recycled before the pooler's idle timeout instead.
engine_options = {"pool_recycle": 240}
if DATABASE_URL.startswith("sqlite:"):
    engine_options["connect_args"] = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
JsonType = JSON().with_variant(JSONB(), "postgresql")
PASSWORD_ITERATIONS = 310_000


def _utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# ----------------------------------------------------------------------------- collections

class Student(Base):
    __tablename__ = "student"

    studentID: Mapped[str] = mapped_column("student_id", String(20), primary_key=True)
    studentName: Mapped[str] = mapped_column("student_name", String(120), default="")
    faculty: Mapped[str] = mapped_column(String(10), default="", index=True)
    programme: Mapped[str] = mapped_column(String(20), default="")
    semester: Mapped[int | None] = mapped_column(Integer, nullable=True)
    yearOfStudy: Mapped[int | None] = mapped_column("year_of_study", Integer, nullable=True)
    tutorialGroup: Mapped[int | None] = mapped_column("tutorial_group", Integer, nullable=True)
    studentEmail: Mapped[str] = mapped_column("student_email", String(120), default="")
    studentPhoneNo: Mapped[str] = mapped_column("student_phone_no", String(30), default="")
    studentStatus: Mapped[str] = mapped_column("student_status", String(30), default="")


class Admin(Base):
    __tablename__ = "admin"

    adminID: Mapped[str] = mapped_column("admin_id", String(20), primary_key=True)
    adminName: Mapped[str] = mapped_column("admin_name", String(120), default="")
    adminEmail: Mapped[str] = mapped_column("admin_email", String(120), default="")
    adminPhoneNo: Mapped[str] = mapped_column("admin_phone_no", String(30), default="")
    password_hash: Mapped[str] = mapped_column(String(256))
    loginDate: Mapped[str] = mapped_column("login_date", String(30), default="")
    status: Mapped[str] = mapped_column(String(30), default="")


class Security(Base):
    __tablename__ = "security"

    guardID: Mapped[str] = mapped_column("guard_id", String(20), primary_key=True)
    guardName: Mapped[str] = mapped_column("guard_name", String(120), default="")
    guardPhoneNo: Mapped[str] = mapped_column("guard_phone_no", String(30), default="")
    adminID: Mapped[str | None] = mapped_column(
        "admin_id", String(20), ForeignKey("admin.admin_id", ondelete="SET NULL"), nullable=True
    )
    password_hash: Mapped[str] = mapped_column(String(256))


class Lecturer(Base):
    __tablename__ = "lecturer"

    lecturerID: Mapped[str] = mapped_column("lecturer_id", String(20), primary_key=True)
    lecturerName: Mapped[str] = mapped_column("lecturer_name", String(120), default="")
    lecturerEmail: Mapped[str] = mapped_column("lecturer_email", String(120), default="")
    password_hash: Mapped[str] = mapped_column(String(256))
    loginDate: Mapped[str] = mapped_column("login_date", String(30), default="")
    status: Mapped[str] = mapped_column(String(30), default="")


class Class(Base):
    __tablename__ = "class"

    classID: Mapped[str] = mapped_column("class_id", String(20), primary_key=True)
    classDate: Mapped[date | None] = mapped_column("class_date", Date, nullable=True)
    classTime: Mapped[time | None] = mapped_column("class_time", Time, nullable=True)
    classType: Mapped[str] = mapped_column("class_type", String(10), default="")
    courseID: Mapped[str] = mapped_column("course_id", String(20), default="")
    lecturerID: Mapped[str | None] = mapped_column(
        "lecturer_id", String(20), ForeignKey("lecturer.lecturer_id", ondelete="SET NULL"),
        nullable=True, index=True,
    )


class ClassDetails(Base):
    __tablename__ = "class_details"

    detailID: Mapped[str] = mapped_column("detail_id", String(40), primary_key=True)
    classID: Mapped[str] = mapped_column(
        "class_id", String(20), ForeignKey("class.class_id", ondelete="CASCADE"), index=True
    )
    studentID: Mapped[str] = mapped_column(
        "student_id", String(20), ForeignKey("student.student_id", ondelete="CASCADE"), index=True
    )


class Blocked(Base):
    __tablename__ = "blocked"

    blockedID: Mapped[str] = mapped_column("blocked_id", String(20), primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    time: Mapped[time] = mapped_column(Time)
    studentID: Mapped[str] = mapped_column("student_id", String(20), index=True)
    studentName: Mapped[str] = mapped_column("student_name", String(120), default="")
    guardID: Mapped[str] = mapped_column("guard_id", String(20), default="", index=True)
    status: Mapped[str] = mapped_column(String(30), default="")
    photoPath: Mapped[str | None] = mapped_column("photo_path", String(512), nullable=True)


class Returns(Base):
    __tablename__ = "returns"

    returnID: Mapped[str] = mapped_column("return_id", String(20), primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    time: Mapped[time] = mapped_column(Time)
    studentID: Mapped[str] = mapped_column("student_id", String(20), index=True)
    studentName: Mapped[str] = mapped_column("student_name", String(120), default="")
    guardID: Mapped[str] = mapped_column("guard_id", String(20), default="", index=True)
    status: Mapped[str] = mapped_column(String(30), default="")


class Notification(Base):
    __tablename__ = "notification"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    totalnum: Mapped[int] = mapped_column(Integer, default=0)


# Ordered so that referenced rows are imported before the rows that reference them.
MODELS = {
    "admin": Admin,
    "security": Security,
    "lecturer": Lecturer,
    "Student": Student,
    "class": Class,
    "classDetails": ClassDetails,
    "blocked": Blocked,
    "returns": Returns,
    "notification": Notification,
}
RESOURCE_KEYS = {resource: next(attr.key for attr in inspect(model).column_attrs
                                if attr.columns[0].primary_key)
                 for resource, model in MODELS.items()}
# role -> (password field in the old Firestore documents, email field)
ACCOUNT_FIELDS = {
    "admin": ("adminPassword", "adminEmail"),
    "security": ("guardPassword", None),
    "lecturer": ("lecturerPw", "lecturerEmail"),
}
ID_FORMATS = {"blocked": ("BL", 8), "returns": ("R", 8)}


# ----------------------------------------------------------------------------- other tables

class PasswordResetChallenge(Base):
    __tablename__ = "password_reset_challenges"

    role: Mapped[str] = mapped_column(String(20), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class FaceSample(Base):
    __tablename__ = "student_face_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("student.student_id", ondelete="CASCADE"), index=True, nullable=False
    )
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    embedding: Mapped[list] = mapped_column(JsonType, nullable=False)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


def init_store():
    Base.metadata.create_all(engine)
    if engine.dialect.name != "postgresql":
        return
    with engine.begin() as connection:
        # The Flask server connects as the database owner, which bypasses RLS. Enabling RLS with
        # no policies stops the public Supabase Data API from reading these tables.
        for table in Base.metadata.tables:
            connection.execute(text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
        has_storage = connection.execute(
            text("SELECT to_regclass('storage.buckets') IS NOT NULL")
        ).scalar()
        if has_storage:
            connection.execute(
                text(
                    "INSERT INTO storage.buckets (id, name, public) VALUES (:bucket, :bucket, false) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {"bucket": supabase_storage.bucket_name()},
            )


# ----------------------------------------------------------------------------- conversion

def _columns(model):
    """{attribute name: python type} for the model's public fields."""
    return {
        attr.key: attr.columns[0].type.python_type
        for attr in inspect(model).column_attrs
        if attr.key != "password_hash"
    }


def _nullable(model):
    return {attr.key for attr in inspect(model).column_attrs if attr.columns[0].nullable}


def _to_python(field, kind, value, nullable=True):
    if value is None or (value == "" and (kind is not str or nullable)):
        return None
    try:
        if kind is str:
            return str(value)
        if kind is int:
            return int(float(value))
        if kind is date:
            return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])
        if kind is time:
            return value if isinstance(value, time) else time.fromisoformat(str(value))
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} has an invalid value: {value!r}") from error
    return value


def _to_json(value):
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    return value


def _to_dict(row):
    return {
        field: _to_json(getattr(row, field))
        for field in _columns(type(row))
        if getattr(row, field) is not None
    }


def _model(resource):
    try:
        return MODELS[resource]
    except KeyError as error:
        raise ValueError("Unknown resource.") from error


# ----------------------------------------------------------------------------- passwords

def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, encoded):
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError, AttributeError):
        return False


def authenticate(role, account_id, password):
    if role not in ACCOUNT_FIELDS:
        return None
    with SessionLocal() as db:
        account = db.get(MODELS[role], account_id)
        if account is None or not verify_password(password, account.password_hash):
            return None
        return {"id": account_id, "role": role, **_to_dict(account)}


def account_email(role, account_id):
    email_field = ACCOUNT_FIELDS.get(role, (None, None))[1]
    if not email_field:
        return None
    with SessionLocal() as db:
        account = db.get(MODELS[role], account_id)
        return getattr(account, email_field) if account else None


def save_password_reset_challenge(role, account_id, code_hash, expires_at, now):
    with SessionLocal.begin() as db:
        challenge = db.get(PasswordResetChallenge, (role, account_id))
        if challenge is not None and challenge.created_at > now - 60:
            return False
        if challenge is None:
            challenge = PasswordResetChallenge(role=role, account_id=account_id)
            db.add(challenge)
        challenge.code_hash = code_hash
        challenge.expires_at = expires_at
        challenge.created_at = now
        challenge.attempts = 0
    return True


def complete_password_reset(role, account_id, code_hash, password, now):
    with SessionLocal.begin() as db:
        challenge = db.get(PasswordResetChallenge, (role, account_id))
        if challenge is None or challenge.expires_at <= now or challenge.attempts >= 5:
            if challenge is not None:
                db.delete(challenge)
            return False
        if not hmac.compare_digest(challenge.code_hash, code_hash):
            challenge.attempts += 1
            if challenge.attempts >= 5:
                db.delete(challenge)
            return False

        account = db.get(MODELS[role], account_id)
        db.delete(challenge)
        if account is None:
            return False
        account.password_hash = hash_password(password)
        return True


# ----------------------------------------------------------------------------- records

def save_record(resource, payload, *, record_id=None):
    """Create or update (upsert) a record; unknown fields are ignored. Returns the saved record."""
    model = _model(resource)
    key_field = RESOURCE_KEYS[resource]
    key = str(record_id or payload.get(key_field, "")).strip()
    if not key:
        raise ValueError(f"{key_field} is required.")
    columns = _columns(model)
    nullable = _nullable(model)
    values = {
        field: _to_python(field, columns[field], value, field in nullable)
        for field, value in payload.items()
        if field in columns and field != key_field
    }
    password = None
    if resource in ACCOUNT_FIELDS:
        password = str(payload.get(ACCOUNT_FIELDS[resource][0], "") or "")

    with SessionLocal.begin() as db:
        row = db.get(model, _to_python(key_field, columns[key_field], key))
        if row is None:
            if resource in ACCOUNT_FIELDS and not password:
                raise ValueError("A password is required for a new account.")
            row = model(**{key_field: _to_python(key_field, columns[key_field], key)})
            db.add(row)
        for field, value in values.items():
            setattr(row, field, value)
        if password:
            row.password_hash = hash_password(password)
        db.flush()
        return _to_dict(row)


def list_records(resource, filters=None):
    """Records matching every filter (string fields compare case-insensitively)."""
    model = _model(resource)
    columns = _columns(model)
    statement = select(model)
    for field, value in (filters or {}).items():
        if value is None or value == "":
            continue
        if field not in columns:
            return []
        column = getattr(model, field)
        if columns[field] is str:
            statement = statement.where(func.lower(column) == str(value).casefold())
        else:
            try:
                statement = statement.where(column == _to_python(field, columns[field], value))
            except ValueError:
                return []
    statement = statement.order_by(getattr(model, RESOURCE_KEYS[resource]))
    with SessionLocal() as db:
        return [_to_dict(row) for row in db.scalars(statement).all()]


def get_record(resource, record_id):
    model = _model(resource)
    key_field = RESOURCE_KEYS[resource]
    try:
        key = _to_python(key_field, _columns(model)[key_field], record_id)
    except ValueError:
        return None
    with SessionLocal() as db:
        row = db.get(model, key)
        return _to_dict(row) if row else None


def delete_record(resource, record_id):
    model = _model(resource)
    key_field = RESOURCE_KEYS[resource]
    try:
        key = _to_python(key_field, _columns(model)[key_field], record_id)
    except ValueError:
        return False
    with SessionLocal.begin() as db:
        row = db.get(model, key)
        if row is None:
            return False
        db.delete(row)
        return True


def next_id(resource):
    """Next sequential ID in the Firestore format, e.g. BL00000042 / R00000007."""
    prefix, width = ID_FORMATS[resource]
    model = MODELS[resource]
    column = getattr(model, RESOURCE_KEYS[resource])
    with SessionLocal() as db:
        existing = db.scalars(select(column).where(column.like(f"{prefix}%"))).all()
    numbers = [int(match.group(1)) for value in existing if (match := re.fullmatch(rf"{prefix}(\d+)", value))]
    return f"{prefix}{max(numbers, default=0) + 1:0{width}d}"


def count_blocked_student(day):
    """Add one to the notification total for `day` (a student was blocked that day)."""
    day = _to_python("date", date, day)
    with SessionLocal.begin() as db:
        notification = db.get(Notification, day)
        if notification is None:
            db.add(Notification(date=day, totalnum=1))
        else:
            notification.totalnum = (notification.totalnum or 0) + 1


# ----------------------------------------------------------------------------- face samples

def add_face_samples(student_id, samples, model_version, *, replace=False):
    """Store (storage_path, embedding) pairs; returns storage paths that were replaced."""
    with SessionLocal.begin() as db:
        replaced = []
        if replace:
            existing = db.scalars(select(FaceSample).where(FaceSample.student_id == student_id)).all()
            replaced = [sample.storage_path for sample in existing]
            for sample in existing:
                db.delete(sample)
        for storage_path, embedding in samples:
            db.add(FaceSample(
                student_id=student_id,
                storage_path=storage_path,
                embedding=embedding,
                model_version=model_version,
                created_at=_utcnow(),
            ))
    return replaced


def list_face_samples(student_ids=None):
    """Return {studentID: [sample, ...]} ordered oldest first."""
    with SessionLocal() as db:
        statement = select(FaceSample).order_by(FaceSample.id)
        if student_ids is not None:
            if not student_ids:
                return {}
            statement = statement.where(FaceSample.student_id.in_(student_ids))
        samples = {}
        for sample in db.scalars(statement).all():
            samples.setdefault(sample.student_id, []).append({
                "id": sample.id,
                "storage_path": sample.storage_path,
                "embedding": sample.embedding,
                "model_version": sample.model_version,
            })
        return samples


def update_face_sample_embedding(sample_id, embedding, model_version):
    with SessionLocal.begin() as db:
        sample = db.get(FaceSample, sample_id)
        if sample is not None:
            sample.embedding = embedding
            sample.model_version = model_version


def delete_face_samples(student_id, sample_ids=None):
    """Delete a student's samples (or only sample_ids); returns their storage paths."""
    with SessionLocal.begin() as db:
        statement = select(FaceSample).where(FaceSample.student_id == student_id)
        if sample_ids is not None:
            statement = statement.where(FaceSample.id.in_(sample_ids))
        samples = db.scalars(statement).all()
        paths = [sample.storage_path for sample in samples]
        for sample in samples:
            db.delete(sample)
        return paths


def import_legacy_record(resource, payload, document_id):
    """Import one Firestore document; plain-text passwords are hashed on the way in."""
    save_record(resource, payload, record_id=payload.get(RESOURCE_KEYS[resource]) or document_id)
