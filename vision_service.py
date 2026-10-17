"""Face recognition (YuNet + SFace) and attire detection (YOLOv7) used by the web app.

Replaces the notebook's Haar cascade + LBPH pipeline: instead of retraining one LBPH model
(trainer/trainer.yml + names.pkl), every face sample is turned into an SFace template and a
camera frame is matched against all templates by cosine similarity.
"""
import os
from pathlib import Path
from threading import Lock


class VisionConfigurationError(RuntimeError):
    pass


_face_lock = Lock()
_face_model_load_lock = Lock()
_face_detector = None
_face_recognizer = None
_yolo_lock = Lock()
_yolo_detector = None


def _load_opencv_numpy():
    try:
        import cv2
        import numpy as np
    except ImportError as error:
        raise VisionConfigurationError(
            "Install the AI dependencies from requirements.txt."
        ) from error
    return cv2, np


_model_download_lock = Lock()


def _ensure_model_file(path):
    """Model files are not in git; on a fresh server, fetch models/<name> from Supabase Storage."""
    path = Path(path)
    if path.is_file():
        return path
    with _model_download_lock:
        if path.is_file():
            return path
        import supabase_storage

        try:
            content = supabase_storage.download_object(f"models/{path.name}", timeout=600)
        except (supabase_storage.StorageConfigurationError, supabase_storage.StorageRequestError):
            return path  # the caller reports the missing file
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".part")
        temporary.write_bytes(content)
        temporary.replace(path)
    return path


def face_model_version():
    # "+640" marks templates built from images scaled for YuNet (see DETECTION_MAX_SIDE).
    return "yunet-2023mar+sface-2021dec+640"


def _load_face_models():
    global _face_detector, _face_recognizer
    if _face_detector is not None and _face_recognizer is not None:
        return _face_detector, _face_recognizer

    with _face_model_load_lock:
        if _face_detector is not None and _face_recognizer is not None:
            return _face_detector, _face_recognizer
        detector_path = _ensure_model_file(
            os.environ.get("FACE_DETECTOR_MODEL", "models/face_detection_yunet_2023mar.onnx")
        )
        recognizer_path = _ensure_model_file(
            os.environ.get("FACE_RECOGNIZER_MODEL", "models/face_recognition_sface_2021dec.onnx")
        )
        missing = [str(path) for path in (detector_path, recognizer_path) if not path.is_file()]
        if missing:
            raise VisionConfigurationError(
                "Face model files are missing: "
                + ", ".join(missing)
                + ". Configure FACE_DETECTOR_MODEL and FACE_RECOGNIZER_MODEL."
            )
        cv2, _ = _load_opencv_numpy()
        if not hasattr(cv2, "FaceDetectorYN_create") or not hasattr(cv2, "FaceRecognizerSF_create"):
            raise VisionConfigurationError(
                "Install opencv-contrib-python-headless to use YuNet and SFace."
            )
        try:
            detector = cv2.FaceDetectorYN_create(str(detector_path), "", (320, 320), 0.8, 0.3, 5000)
            recognizer = cv2.FaceRecognizerSF_create(str(recognizer_path), "")
        except cv2.error as error:
            raise VisionConfigurationError(f"Could not load face models: {error}") from error

        _face_detector, _face_recognizer = detector, recognizer
        return detector, recognizer


def decode_image(image_bytes):
    cv2, np = _load_opencv_numpy()
    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("The uploaded file is not a readable image.")
    return image


# YuNet is built for small inputs: on a full-resolution phone photo the face is so large that the
# detection score drops and the landmarks used for alignment drift, which ruins the template.
# Every image is therefore scaled so its longest side is at most this many pixels.
DETECTION_MAX_SIDE = 640


def _embed(image, *, require_single_face):
    """Return (embedding, face_box) for the main face in a BGR image, or (None, None).

    face_box is in the coordinates of the image that was passed in.
    """
    cv2, np = _load_opencv_numpy()
    detector, recognizer = _load_face_models()
    scale = min(1.0, DETECTION_MAX_SIDE / max(image.shape[:2]))
    if scale < 1.0:
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    with _face_lock:
        detector.setInputSize((image.shape[1], image.shape[0]))
        _, faces = detector.detect(image)
        if faces is None or len(faces) == 0:
            if require_single_face:
                raise ValueError("No face was found in the photo.")
            return None, None
        faces = sorted(faces, key=lambda item: item[2] * item[3], reverse=True)
        face = faces[0]  # largest face is the person in front of the camera
        if require_single_face and len(faces) > 1 and faces[1][2] * faces[1][3] > 0.5 * face[2] * face[3]:
            raise ValueError("More than one person is in the photo. Use a photo of the student alone.")
        aligned = recognizer.alignCrop(image, face)
        embedding = recognizer.feature(aligned).reshape(-1).astype(np.float32)
    norm = float(np.linalg.norm(embedding))
    if not np.isfinite(norm) or norm == 0:
        raise ValueError("Could not create a reliable face template from this photo.")
    x, y, w, h = (float(value) / scale for value in face[:4])
    return (embedding / norm).astype(float).tolist(), [x, y, x + w, y + h]


def extract_face_embedding(image_bytes):
    """Template for a face *sample*: the student must be the main (largest) face in the photo."""
    image = decode_image(image_bytes)
    if image.shape[0] < 100 or image.shape[1] < 100:
        raise ValueError("Use a clear face photo at least 100 by 100 pixels.")
    embedding, _ = _embed(image, require_single_face=True)
    return embedding


def _match_threshold():
    try:
        threshold = float(os.environ.get("FACE_MATCH_THRESHOLD", "0.363"))
    except ValueError as error:
        raise VisionConfigurationError("FACE_MATCH_THRESHOLD must be a number from -1 to 1.") from error
    if not -1 <= threshold <= 1:
        raise VisionConfigurationError("FACE_MATCH_THRESHOLD must be a number from -1 to 1.")
    return threshold


def match_face(image, samples):
    """Match the largest face in a BGR frame against {studentID: [sample, ...]}."""
    _, np = _load_opencv_numpy()
    embedding, face_box = _embed(image, require_single_face=False)
    if embedding is None:
        return {"student_id": None, "similarity": None, "threshold": _match_threshold(), "face_box": None}
    query = np.asarray(embedding, dtype=np.float32)

    best_student, best_score = None, -1.0
    for student_id, student_samples in samples.items():
        for sample in student_samples:
            if sample.get("model_version") != face_model_version():
                continue
            vector = np.asarray(sample["embedding"], dtype=np.float32)
            if vector.shape != query.shape:
                continue
            score = float(np.dot(query, vector))
            if score > best_score:
                best_student, best_score = student_id, score

    threshold = _match_threshold()
    return {
        "student_id": best_student if best_score >= threshold else None,
        "similarity": round(best_score, 4) if best_student is not None else None,
        "threshold": threshold,
        "face_box": face_box,
    }


def encode_jpeg(image, face_box=None, margin=0.35):
    """JPEG bytes of the whole frame, or of the face box plus a margin."""
    cv2, _ = _load_opencv_numpy()
    if face_box:
        height, width = image.shape[:2]
        x1, y1, x2, y2 = face_box
        pad_x, pad_y = (x2 - x1) * margin, (y2 - y1) * margin
        left, top = max(0, int(x1 - pad_x)), max(0, int(y1 - pad_y))
        right, bottom = min(width, int(x2 + pad_x)), min(height, int(y2 + pad_y))
        if right > left and bottom > top:
            image = image[top:bottom, left:right]
    ok, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise ValueError("Could not encode the image.")
    return buffer.tobytes()


def detect_attire(image):
    """Run YOLOv7 on a BGR frame and return improper-attire detections."""
    global _yolo_detector
    if _yolo_detector is None:
        weight_path = _ensure_model_file(os.environ.get("YOLO_WEIGHTS", "models/attire-best.pt"))
        if not weight_path.is_file():
            raise VisionConfigurationError(
                f"YOLO weights were not found at {weight_path}. Set YOLO_WEIGHTS to the trained model file."
            )
        with _yolo_lock:
            if _yolo_detector is None:
                try:
                    from attire_detector import AttireDetector
                    _yolo_detector = AttireDetector(str(weight_path))
                except (ImportError, OSError, RuntimeError) as error:
                    raise VisionConfigurationError(f"Could not load YOLO: {error}") from error

    with _yolo_lock:
        return _yolo_detector.detect(image)


def warm_up():
    """Load the face and YOLO models and run each once, so the first camera frame is fast."""
    import logging

    logger = logging.getLogger(__name__)
    _, np = _load_opencv_numpy()
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    for name, step in (("face models", lambda: match_face(blank, {})), ("YOLO", lambda: detect_attire(blank))):
        try:
            step()
            logger.info("Warmed up %s.", name)
        except VisionConfigurationError as error:
            logger.warning("Could not warm up %s: %s", name, error)


def describe_detections(detections):
    """Human-readable reason such as '1 Crop_Top, 2 Shorts' (as the Tkinter alert showed)."""
    counts = {}
    for detection in detections:
        counts[detection["class"]] = counts.get(detection["class"], 0) + 1
    return ", ".join(f"{count} {name}" for name, count in counts.items())
