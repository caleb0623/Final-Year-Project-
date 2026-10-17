import hmac
import io
import os
import time
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import numpy as np

import postgres_store as store
import supabase_storage
import vision_service
import web_app
from web_app import app

FRAME = {"frame": "data:image/jpeg;base64,aW1hZ2U="}
BLANK_IMAGE = np.zeros((240, 320, 3), dtype=np.uint8)
CROP_TOP = [{"class": "Crop_Top", "confidence": 0.91, "bbox": [10.0, 60.0, 200.0, 220.0]}]


class AttireCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        store.init_store()
        app.config["TESTING"] = True

    def setUp(self):
        with store.SessionLocal.begin() as db:
            db.query(store.PasswordResetChallenge).delete()
            db.query(store.FaceSample).delete()
            for model in reversed(list(store.MODELS.values())):
                db.query(model).delete()
        web_app.clear_caches()
        self.client = app.test_client()
        store.save_record("security", {"guardID": "SG00001", "guardName": "Guard One", "guardPassword": "test-password"})
        store.save_record("security", {"guardID": "SG00002", "guardName": "Guard Two", "guardPassword": "test-password"})
        store.save_record("admin", {"adminID": "AD00001", "adminName": "Demo Admin",
                                    "adminEmail": "admin@example.test", "adminPassword": "test-password"})
        store.save_record("Student", {"studentID": "22WMR00001", "studentName": "Demo Student", "faculty": "FOCS"})
        store.save_record("Student", {"studentID": "22WMR00002", "studentName": "Other Student", "faculty": "FAFB"})

    def sign_in(self, role, account_id):
        self.client.get("/")
        with self.client.session_transaction() as state:
            csrf_token = state["csrf_token"]
        response = self.client.post("/", data={
            "role": role, "account_id": account_id, "password": "test-password", "csrf_token": csrf_token,
        })
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as state:
            return {"X-CSRF-Token": state["csrf_token"]}

    # ------------------------------------------------------------------ accounts

    def test_password_is_hashed_and_not_returned(self):
        account = store.authenticate("security", "SG00001", "test-password")
        self.assertEqual(account["guardName"], "Guard One")
        self.assertNotIn("guardPassword", account)
        self.assertIsNone(store.authenticate("security", "SG00001", "wrong-password"))

    def test_password_reset_code_updates_account_password(self):
        code = "123456"
        code_hash = hmac.new(
            app.config["SECRET_KEY"].encode("utf-8"), f"admin:AD00001:{code}".encode("utf-8"), "sha256",
        ).hexdigest()
        now = int(time.time())
        store.save_password_reset_challenge("admin", "AD00001", code_hash, now + 600, now)

        response = self.client.post("/api/auth/password-reset/confirm",
                                    json={"id": "AD00001", "code": code, "password": "new-password"})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(store.authenticate("admin", "AD00001", "new-password"))
        reused = self.client.post("/api/auth/password-reset/confirm",
                                  json={"id": "AD00001", "code": code, "password": "another-password"})
        self.assertEqual(reused.status_code, 400)

    def test_firestore_documents_map_to_typed_tables(self):
        store.import_legacy_record("Student", {
            "face": "", "faculty": "FOCS", "programme": "RDS", "semester": 2, "studentEmail": "hph@example.test",
            "studentID": "19WMR12034", "studentName": "Hii Puong Hou", "studentPhoneNo": "0123456786",
            "studentStatus": "good", "tutorialGroup": 1, "yearOfStudy": 3,
        }, "19WMR12034")
        store.import_legacy_record("lecturer", {"lecturerID": "L00001", "lecturerName": "Lecturer",
                                                "lecturerPw": "123", "lecturerEmail": "l@example.test"}, "L00001")
        store.import_legacy_record("class", {"classDate": "2023-03-15", "classID": "C0000000001", "classTime": "08:00:00",
                                             "classType": "L", "courseID": "BACS3021", "lecturerID": "L00001"}, "C0000000001")
        store.import_legacy_record("classDetails", {"classID": "C0000000001", "studentID": "19WMR12034"},
                                   "03NOZPz5i0FzTOsejELY")
        store.import_legacy_record("notification", {"date": "2023-03-14", "totalnum": 3}, "2023-03-14")

        student = store.get_record("Student", "19WMR12034")
        self.assertEqual((student["semester"], student["yearOfStudy"], student["faculty"]), (2, 3, "FOCS"))
        self.assertNotIn("face", student)
        self.assertEqual(store.get_record("class", "C0000000001")["classTime"], "08:00:00")
        self.assertEqual(store.list_records("classDetails", {"classID": "C0000000001"})[0]["detailID"],
                         "03NOZPz5i0FzTOsejELY")
        self.assertEqual(store.get_record("notification", "2023-03-14")["totalnum"], 3)
        lecturer = store.authenticate("lecturer", "L00001", "123")
        self.assertNotIn("lecturerPw", lecturer)
        self.assertNotIn("password_hash", lecturer)

    def test_blocked_ids_are_sequential_and_notification_counts_blocks(self):
        store.save_record("blocked", {"blockedID": "BL00000041", "date": "2023-03-14", "time": "00:28:02",
                                      "studentID": "22WMR00002", "guardID": "SG00001"})
        headers = self.sign_in("security", "SG00001")
        rows = self.client.post("/api/blocked", headers=headers, json={"student_id": "22WMR00001"}).get_json()["rows"]
        self.assertEqual(rows[0]["blockedID"], "BL00000042")
        self.assertEqual(store.get_record("notification", str(date.today()))["totalnum"], 1)
        self.client.delete("/api/blocked/BL00000042", headers=headers)
        self.assertEqual(store.list_records("returns")[0]["returnID"], "R00000001")

    def test_storage_configuration_status(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIn("SUPABASE_URL", supabase_storage.configuration_error())
        settings = {"SUPABASE_URL": "https://project.supabase.co", "SUPABASE_SECRET_KEY": "key"}
        with patch.dict(os.environ, settings, clear=True):
            self.assertIsNone(supabase_storage.configuration_error())
            self.assertEqual(supabase_storage.bucket_name(), "attire-checker")

    # ------------------------------------------------------------------ admin

    def test_admin_adds_student_and_trains_face_with_several_samples(self):
        headers = self.sign_in("admin", "AD00001")
        created = self.client.post("/api/admin/students", headers=headers,
                                   json={"studentID": "23wmr00009", "studentName": "New Student", "faculty": "FOCS"})
        self.assertEqual(created.status_code, 201)
        duplicate = self.client.post("/api/admin/students", headers=headers,
                                     json={"studentID": "23WMR00009", "studentName": "Again"})
        self.assertEqual(duplicate.status_code, 409)

        embeddings = [[0.6, 0.8], ValueError("No face was found in the photo."), [0.8, 0.6]]
        with patch.object(supabase_storage, "configuration_error", return_value=None), \
                patch("vision_service.extract_face_embedding", side_effect=embeddings), \
                patch("supabase_storage.upload_object") as upload:
            response = self.client.post(
                "/api/admin/students/23WMR00009/face-samples",
                headers=headers,
                data={"images": [(io.BytesIO(b"a"), "1.jpg", "image/jpeg"),
                                 (io.BytesIO(b"b"), "2.jpg", "image/jpeg"),
                                 (io.BytesIO(b"c"), "3.jpg", "image/jpeg")]},
                content_type="multipart/form-data",
            )
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json()["saved"], 2)
        self.assertEqual(len(response.get_json()["skipped"]), 1)
        self.assertEqual(upload.call_count, 2)
        samples = store.list_face_samples(["23WMR00009"])["23WMR00009"]
        self.assertTrue(all(sample["storage_path"].startswith("faces/23WMR00009/") for sample in samples))
        page = self.client.get("/admin/students")
        self.assertIn(b"2 samples", page.data)

    def test_face_training_requires_admin(self):
        headers = self.sign_in("security", "SG00001")
        denied = self.client.post("/api/admin/students/22WMR00001/face-samples", headers=headers,
                                  data={"images": (io.BytesIO(b"x"), "face.jpg", "image/jpeg")},
                                  content_type="multipart/form-data")
        self.assertEqual(denied.status_code, 403)

    def test_report_filters_by_date_range_and_faculty_and_downloads_csv(self):
        today = str(date.today())
        old = str(date.today() - timedelta(days=30))
        store.save_record("blocked", {"blockedID": "BL1", "date": today, "time": "08:00:00",
                                      "studentID": "22WMR00001", "studentName": "Demo Student", "guardID": "SG00001"})
        store.save_record("blocked", {"blockedID": "BL2", "date": today, "time": "09:00:00",
                                      "studentID": "22WMR00002", "studentName": "Other Student", "guardID": "SG00001"})
        store.save_record("blocked", {"blockedID": "BL3", "date": old, "time": "09:00:00",
                                      "studentID": "22WMR00001", "studentName": "Demo Student", "guardID": "SG00002"})
        self.sign_in("admin", "AD00001")
        rows = self.client.get(f"/api/admin/reports?start={today}&end={today}&faculty=FOCS").get_json()["rows"]
        self.assertEqual([row["blockedID"] for row in rows], ["BL1"])
        csv_response = self.client.get(f"/admin/reports/download?start={old}&end={today}&faculty=")
        self.assertEqual(csv_response.status_code, 200)
        body = csv_response.data.decode("utf-8-sig")
        self.assertTrue(body.startswith("Blocked ID,Time Stamp,Student Name,Student ID,Faculty,Guard ID"))
        self.assertEqual(body.count("\n"), 4)
        bad_range = self.client.get(f"/api/admin/reports?start={today}&end={old}")
        self.assertEqual(bad_range.status_code, 400)

    # ------------------------------------------------------------------ guard

    def test_guard_manages_todays_blocked_list(self):
        headers = self.sign_in("security", "SG00001")
        self.assertEqual(self.client.get("/dashboard").status_code, 200)
        no_csrf = self.client.post("/api/blocked", json={"student_id": "22WMR00001"})
        self.assertEqual(no_csrf.status_code, 400)
        added = self.client.post("/api/blocked", headers=headers, json={"student_id": "22wmr00001"})
        self.assertEqual(added.status_code, 201)
        blocked_id = added.get_json()["rows"][0]["blockedID"]
        again = self.client.post("/api/blocked", headers=headers, json={"student_id": "22WMR00001"})
        self.assertEqual(again.status_code, 409)
        updated = self.client.patch(f"/api/blocked/{blocked_id}", headers=headers, json={"student_id": "22WMR00002"})
        self.assertEqual(updated.get_json()["rows"][0]["studentID"], "22WMR00002")
        removed = self.client.delete(f"/api/blocked/{blocked_id}", headers=headers)
        self.assertEqual(removed.get_json()["rows"], [])
        self.assertEqual(len(store.list_records("returns", {"studentID": "22WMR00002"})), 1)

    def scan(self, headers, detections):
        match = {"student_id": "22WMR00001", "similarity": 0.82, "threshold": 0.363,
                 "face_box": [40.0, 30.0, 120.0, 130.0]}
        with patch("vision_service.decode_image", return_value=BLANK_IMAGE), \
                patch("vision_service.match_face", return_value=match), \
                patch("vision_service.detect_attire", **detections):
            return self.client.post("/api/vision/frame", headers=headers, json=FRAME).get_json()

    def test_scan_reports_violation_and_acknowledge_blocks_with_photo(self):
        headers = self.sign_in("security", "SG00001")
        result = self.scan(headers, {"return_value": CROP_TOP})
        self.assertEqual(result["student_name"], "Demo Student")
        self.assertEqual(result["violation"], {"reason": "1 Crop_Top", "already_blocked": False})

        with patch("vision_service.decode_image", return_value=BLANK_IMAGE), \
                patch("supabase_storage.upload_object") as upload:
            response = self.client.post("/api/vision/acknowledge", headers=headers,
                                        json={**FRAME, "student_id": "22WMR00001", "face_box": result["face_box"]})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.get_json()["warning"])
        path = upload.call_args.args[0]
        self.assertTrue(path.startswith(f"violations/{date.today()}-22WMR00001-"))
        record = store.list_records("blocked", {"studentID": "22WMR00001"})[0]
        self.assertEqual(record["photoPath"], path)
        self.assertTrue(response.get_json()["rows"][0]["hasPhoto"])

        self.assertTrue(self.scan(headers, {"return_value": CROP_TOP})["violation"]["already_blocked"])

    def test_revoke_returns_student_and_keeps_frame_for_active_learning(self):
        headers = self.sign_in("security", "SG00001")
        self.client.post("/api/blocked", headers=headers, json={"student_id": "22WMR00001"})
        with patch("vision_service.decode_image", return_value=BLANK_IMAGE), \
                patch("supabase_storage.upload_object") as upload:
            response = self.client.post("/api/vision/revoke", headers=headers,
                                        json={**FRAME, "student_id": "22WMR00001"})
        self.assertEqual(response.get_json()["rows"], [])
        self.assertTrue(upload.call_args.args[0].startswith("active-learning/"))
        self.assertEqual(len(store.list_records("returns", {"studentID": "22WMR00001"})), 1)

    def test_blocked_student_is_returned_after_consecutive_proper_attire_scans(self):
        headers = self.sign_in("security", "SG00001")
        store.save_record("blocked", {"blockedID": "BLNEW", "date": str(date.today()),
                                      "time": datetime.now().strftime("%H:%M:%S"), "studentID": "22WMR00001",
                                      "studentName": "Demo Student", "guardID": "SG00002"})
        self.assertFalse(self.scan(headers, {"return_value": []})["returned"])   # 1st proper scan
        self.assertTrue(self.scan(headers, {"return_value": CROP_TOP})["violation"])  # violation resets
        self.assertFalse(self.scan(headers, {"return_value": []})["returned"])
        result = self.scan(headers, {"return_value": []})                         # 2nd in a row
        self.assertTrue(result["returned"])
        self.assertEqual(result["rows"], [])
        self.assertIsNone(store.get_record("blocked", "BLNEW"))
        self.assertEqual(store.list_records("returns")[0]["guardID"], "SG00001")

    def test_scan_reports_missing_yolo_weights(self):
        headers = self.sign_in("security", "SG00001")
        result = self.scan(headers, {"side_effect": vision_service.VisionConfigurationError("YOLO weights are missing.")})
        self.assertEqual(result["yolo_error"], "YOLO weights are missing.")
        self.assertIsNone(result["violation"])

    # ------------------------------------------------------------------ lecturer & accounts

    def test_lecturer_sees_only_students_of_own_classes(self):
        today = str(date.today())
        store.save_record("lecturer", {"lecturerID": "L00001", "lecturerName": "Lecturer One",
                                       "lecturerPw": "test-password", "lecturerEmail": "l1@example.test"})
        store.save_record("class", {"classID": "C1", "classDate": today, "classTime": "08:00:00",
                                    "courseID": "BACS3021", "lecturerID": "L00001"})
        store.save_record("classDetails", {"classID": "C1", "studentID": "22WMR00001"}, record_id="D1")
        for blocked_id, student_id in (("BL1", "22WMR00001"), ("BL2", "22WMR00002")):
            store.save_record("blocked", {"blockedID": blocked_id, "date": today, "time": "08:00:00",
                                          "studentID": student_id, "guardID": "SG00001", "photoPath": "violations/x.jpg"})
        store.save_record("notification", {"date": today, "totalnum": 2})

        self.sign_in("lecturer", "L00001")
        for page in ("/lecturer", "/lecturer/returns", "/lecturer/history", "/profile"):
            self.assertEqual(self.client.get(page).status_code, 200, page)
        rows = self.client.get(f"/api/lecturer/blocked?date={today}").get_json()["rows"]
        self.assertEqual([row["blockedID"] for row in rows], ["BL1"])
        self.assertTrue(rows[0]["hasPhoto"])
        history = self.client.get(f"/api/lecturer/history?start={today}&end={today}").get_json()["rows"]
        self.assertEqual(history, [{"date": today, "totalnum": 2}])
        with patch("supabase_storage.download_object", return_value=b"jpeg"):
            self.assertEqual(self.client.get("/api/blocked/BL1/photo").status_code, 200)
            self.assertEqual(self.client.get("/api/blocked/BL2/photo").status_code, 404)
        self.assertEqual(self.client.get("/admin/students").status_code, 403)

    def test_admin_manages_security_guards(self):
        headers = self.sign_in("admin", "AD00001")
        self.assertEqual(self.client.get("/admin/guards").status_code, 200)
        short = self.client.post("/api/admin/guards", headers=headers, json={"guardName": "New", "guardPassword": "123"})
        self.assertEqual(short.status_code, 400)
        created = self.client.post("/api/admin/guards", headers=headers,
                                   json={"guardName": "New Guard", "guardPhoneNo": "012", "guardPassword": "new-password"})
        self.assertEqual(created.status_code, 201)
        guard = created.get_json()["guard"]
        self.assertEqual((guard["guardID"], guard["adminID"]), ("SG00003", "AD00001"))
        self.assertIsNotNone(store.authenticate("security", "SG00003", "new-password"))
        self.client.put("/api/admin/guards/SG00003", headers=headers, json={"guardName": "Renamed", "guardPhoneNo": ""})
        self.assertEqual(store.get_record("security", "SG00003")["guardName"], "Renamed")
        self.assertIsNotNone(store.authenticate("security", "SG00003", "new-password"))
        found = self.client.get("/api/admin/guards?q=renam").get_json()["guards"]
        self.assertEqual([guard["guardID"] for guard in found], ["SG00003"])
        self.assertEqual(self.client.delete("/api/admin/guards/SG00003", headers=headers).status_code, 200)
        self.assertIsNone(store.get_record("security", "SG00003"))

    def test_user_changes_own_password(self):
        headers = self.sign_in("security", "SG00001")
        wrong = self.client.post("/api/profile/password", headers=headers,
                                 json={"current": "nope", "new": "another-password"})
        self.assertEqual(wrong.status_code, 400)
        changed = self.client.post("/api/profile/password", headers=headers,
                                   json={"current": "test-password", "new": "another-password"})
        self.assertEqual(changed.status_code, 200)
        self.assertIsNotNone(store.authenticate("security", "SG00001", "another-password"))
        self.assertEqual(self.client.get("/forgot-password").status_code, 200)

    # ------------------------------------------------------------------ mobile API

    def test_api_requires_token_and_limits_security_records(self):
        self.assertEqual(self.client.get("/api/records/blocked").status_code, 401)
        login = self.client.post("/api/auth/login",
                                 json={"role": "security", "id": "SG00001", "password": "test-password"})
        headers = {"Authorization": f"Bearer {login.get_json()['access_token']}"}
        records = self.client.get("/api/records/security", headers=headers).get_json()["records"]
        self.assertEqual([record["guardID"] for record in records], ["SG00001"])
        self.assertEqual(
            self.client.post("/api/records/Student", headers=headers, json={"studentID": "X"}).status_code, 403
        )

    def test_mobile_loads_violation_photo_with_bearer_token(self):
        store.save_record("blocked", {"blockedID": "BL9", "date": str(date.today()), "time": "08:00:00",
                                      "studentID": "22WMR00001", "guardID": "SG00001",
                                      "photoPath": "violations/x.jpg"})
        own = self.client.post("/api/auth/login", json={"role": "security", "id": "SG00001", "password": "test-password"})
        other = self.client.post("/api/auth/login", json={"role": "security", "id": "SG00002", "password": "test-password"})
        with patch("supabase_storage.download_object", return_value=b"jpeg-bytes"):
            allowed = self.client.get("/api/blocked/BL9/photo",
                                      headers={"Authorization": f"Bearer {own.get_json()['access_token']}"})
            denied = self.client.get("/api/blocked/BL9/photo",
                                     headers={"Authorization": f"Bearer {other.get_json()['access_token']}"})
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.data, b"jpeg-bytes")
        self.assertEqual(denied.status_code, 404)


if __name__ == "__main__":
    unittest.main()
