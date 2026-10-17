"""Private Supabase Storage access for face samples, violation evidence and active-learning frames.

Object layout inside the bucket:
    faces/<studentID>/<uuid>.jpg            face samples used to build recognition templates
    violations/<date>-<studentID>-<uuid>.jpg face crop saved when a guard acknowledges a violation
    active-learning/<date>/<uuid>.jpg        frames a guard revoked, kept for re-annotation
"""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class StorageConfigurationError(RuntimeError):
    pass


class StorageRequestError(RuntimeError):
    pass


def bucket_name():
    return (
        os.environ.get("SUPABASE_STORAGE_BUCKET")
        or os.environ.get("SUPABASE_FACE_BUCKET")
        or "attire-checker"
    ).strip()


def _settings():
    base_url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    service_key = (
        os.environ.get("SUPABASE_SECRET_KEY")
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    ).strip()
    bucket = bucket_name()
    if not base_url or not service_key or not bucket:
        raise StorageConfigurationError(
            "Set SUPABASE_URL, SUPABASE_SECRET_KEY, and SUPABASE_STORAGE_BUCKET."
        )
    if not base_url.startswith("https://"):
        raise StorageConfigurationError("SUPABASE_URL must use HTTPS.")
    return base_url, service_key, bucket


def configuration_error():
    try:
        _settings()
    except StorageConfigurationError as error:
        return str(error)
    return None


def _send(method, url_suffix, *, content=None, headers=None, timeout=20):
    base_url, service_key, bucket = _settings()
    request = Request(
        f"{base_url}/storage/v1/object/{url_suffix.format(bucket=bucket)}",
        data=content,
        headers={"Authorization": f"Bearer {service_key}", "apikey": service_key, **(headers or {})},
        method=method,
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except HTTPError as error:
        detail = error.read(1024).decode("utf-8", errors="replace")
        raise StorageRequestError(f"Supabase Storage returned HTTP {error.code}: {detail}") from error
    except (URLError, TimeoutError) as error:
        raise StorageRequestError("Could not connect to Supabase Storage.") from error


def upload_object(path, content, content_type, timeout=20):
    _send(
        "POST",
        "{bucket}/" + quote(path),
        content=content,
        headers={"Content-Type": content_type, "x-upsert": "true"},
        timeout=timeout,
    )


def download_object(path, timeout=20):
    return _send("GET", "authenticated/{bucket}/" + quote(path), timeout=timeout)


def delete_objects(paths):
    paths = [path for path in paths if path]
    if not paths:
        return
    _send(
        "DELETE",
        "{bucket}",
        content=json.dumps({"prefixes": paths}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
