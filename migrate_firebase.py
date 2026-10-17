"""Move the legacy Firebase data and images into Supabase.

    python migrate_firebase.py                      # dry run: count Firestore records
    python migrate_firebase.py --apply              # copy Firestore records to Supabase Postgres
    python migrate_firebase.py --apply --images     # ...and Firebase Storage images to Supabase Storage
    python migrate_firebase.py --apply --local-dir . --no-firestore   # only images from legacy local folders

Image mapping (old -> new):
    Firebase  students/<studentID>        -> faces/<studentID>/legacy.jpg  (+ face template for recognition)
    Firebase  <date>-<studentID>          -> violations/<date>-<studentID>.jpg (linked to the blocked record)
    local     students/<studentID>.jpg    -> same as Firebase students/
    local     saveid/<date>-<studentID>.jpg -> same as Firebase <date>-<studentID>
    local     activeLearning/<name>.png   -> active-learning/legacy/<name>.jpg
"""
import argparse
import os
import re
import sys
from pathlib import Path

import postgres_store as store
import supabase_storage
import vision_service

VIOLATION_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-([A-Za-z0-9]+?)(?:\.(?:jpe?g|png))?$", re.IGNORECASE)
STUDENT_NAME = re.compile(r"^students/([A-Za-z0-9]+?)(?:\.(?:jpe?g|png))?$", re.IGNORECASE)
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def _as_jpeg(content):
    return vision_service.encode_jpeg(vision_service.decode_image(content))


def migrate_image(name, content, apply):
    """Copy one legacy image. `name` uses Firebase naming (students/<id> or <date>-<id>)."""
    if match := STUDENT_NAME.match(name):
        student_id = match.group(1).upper()
        path = f"faces/{student_id}/legacy.jpg"
        if not apply:
            return f"student photo -> {path}"
        existing = store.list_face_samples([student_id]).get(student_id, [])
        if any(sample["storage_path"] == path for sample in existing):
            return f"student photo already migrated ({path})"
        jpeg = _as_jpeg(content)
        try:
            embedding = vision_service.extract_face_embedding(jpeg)
        except ValueError as error:
            raise ValueError(f"no usable face ({error})") from error
        supabase_storage.upload_object(path, jpeg, "image/jpeg")
        store.add_face_samples(student_id, [(path, embedding)], vision_service.face_model_version())
        return f"student photo -> {path} (face template created)"

    if match := VIOLATION_NAME.match(Path(name).name):
        day, student_id = match.group(1), match.group(2).upper()
        path = f"violations/{day}-{student_id}.jpg"
        if not apply:
            return f"violation photo -> {path}"
        supabase_storage.upload_object(path, _as_jpeg(content), "image/jpeg")
        linked = 0
        for record in store.list_records("blocked", {"date": day, "studentID": student_id}):
            store.save_record("blocked", {**record, "photoPath": path}, record_id=record["blockedID"])
            linked += 1
        return f"violation photo -> {path} (linked to {linked} blocked record(s))"

    raise ValueError("unrecognised file name")


def firebase_images(bucket_name):
    from firebase_admin import storage

    for blob in storage.bucket(bucket_name).list_blobs():
        if not blob.name.endswith("/"):
            yield blob.name, blob.download_as_bytes


def local_images(directory):
    root = Path(directory)
    for folder, prefix in (("students", "students/"), ("saveid", "")):
        for file in sorted((root / folder).glob("*")):
            if file.suffix.lower() in IMAGE_SUFFIXES:
                yield prefix + file.name, file.read_bytes
    for file in sorted((root / "activeLearning").glob("*")):
        if file.suffix.lower() in IMAGE_SUFFIXES:
            yield f"activeLearning/{file.name}", file.read_bytes


def copy_images(sources, apply):
    failed = 0
    for name, read in sources:
        try:
            if name.startswith("activeLearning/"):
                path = f"active-learning/legacy/{Path(name).stem}.jpg"
                if apply:
                    supabase_storage.upload_object(path, _as_jpeg(read()), "image/jpeg")
                print(f"  {name}: active-learning frame -> {path}")
                continue
            print(f"  {name}: {migrate_image(name, read() if apply else b'', apply)}")
        except Exception as error:  # report and keep going; the source image is untouched
            failed += 1
            print(f"  ERROR {name}: {error}", file=sys.stderr)
    return failed


def main():
    parser = argparse.ArgumentParser(description="Copy Firebase records and images to Supabase.")
    parser.add_argument("--apply", action="store_true", help="Write to Supabase. Without it, only report.")
    parser.add_argument("--no-firestore", action="store_true", help="Skip Firestore records.")
    parser.add_argument("--images", action="store_true", help="Copy Firebase Storage images.")
    parser.add_argument(
        "--bucket",
        default=os.environ.get("FIREBASE_STORAGE_BUCKET", "trying-a2ca1.appspot.com"),
        help="Firebase Storage bucket (default: %(default)s).",
    )
    parser.add_argument("--local-dir", help="Folder containing legacy students/, saveid/, activeLearning/.")
    args = parser.parse_args()

    needs_firebase = not args.no_firestore or args.images
    if needs_firebase:
        credential_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not credential_path:
            parser.error("Set GOOGLE_APPLICATION_CREDENTIALS to the Firebase service-account JSON file.")
        import firebase_admin
        from firebase_admin import credentials

        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(credentials.Certificate(credential_path))
    if args.apply:
        store.init_store()
        if (args.images or args.local_dir) and supabase_storage.configuration_error():
            parser.error(supabase_storage.configuration_error())

    failed = 0
    if not args.no_firestore:
        from firebase_admin import firestore

        client = firestore.client()
        print("Firestore records:")
        for collection_name in store.RESOURCE_KEYS:
            documents = list(client.collection(collection_name).stream())
            print(f"  {collection_name}: {len(documents)} records")
            if not args.apply:
                continue
            for document in documents:
                try:
                    store.import_legacy_record(collection_name, document.to_dict() or {}, document.id)
                except Exception as error:
                    failed += 1
                    print(f"  ERROR importing {collection_name}/{document.id}: {error}", file=sys.stderr)

    # Images run after records so violation photos can be linked to the imported blocked records.
    if args.images:
        print(f"Firebase Storage images ({args.bucket}):")
        failed += copy_images(firebase_images(args.bucket), args.apply)
    if args.local_dir:
        print(f"Local images ({args.local_dir}):")
        failed += copy_images(local_images(args.local_dir), args.apply)

    if failed:
        print(f"Migration finished with {failed} failure(s).", file=sys.stderr)
        return 1
    print("Migration completed. Firebase data was left unchanged." if args.apply
          else "Dry run only. Add --apply to copy to Supabase.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
