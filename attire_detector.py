"""YOLOv7 attire detector (cleaned-up successor of detect_cleaning.py)."""
import os

import numpy as np
import torch

from models.experimental import attempt_load
from utils.datasets import letterbox
from utils.general import check_img_size, non_max_suppression, scale_coords
from utils.torch_utils import select_device


class AttireDetector:
    def __init__(self, weights, img_size=640, conf_thres=0.5, iou_thres=0.45, device=""):
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        torch.set_num_threads(os.cpu_count() or 1)  # PyTorch defaults to half the cores
        self.device = select_device(device)
        self.half = self.device.type != "cpu"  # half precision only supported on CUDA

        self.model = attempt_load([weights], map_location=self.device)
        self.stride = int(self.model.stride.max())
        self.img_size = check_img_size(img_size, s=self.stride)
        if self.half:
            self.model.half()
        self.names = self.model.module.names if hasattr(self.model, "module") else self.model.names

        if self.device.type != "cpu":  # warm up
            self.model(torch.zeros(1, 3, self.img_size, self.img_size).to(self.device)
                       .type_as(next(self.model.parameters())))

    def detect(self, image_bgr):
        """Return [{class, confidence, bbox:[x1,y1,x2,y2]}] in original image pixels."""
        img = letterbox(image_bgr, self.img_size, stride=self.stride)[0]
        img = np.ascontiguousarray(img[:, :, ::-1].transpose(2, 0, 1))  # BGR→RGB, HWC→CHW
        tensor = torch.from_numpy(img).to(self.device)
        tensor = (tensor.half() if self.half else tensor.float()) / 255.0
        tensor = tensor.unsqueeze(0)

        with torch.no_grad():
            prediction = self.model(tensor)[0]
        detections = non_max_suppression(prediction, self.conf_thres, self.iou_thres)[0]

        results = []
        if len(detections):
            detections[:, :4] = scale_coords(tensor.shape[2:], detections[:, :4], image_bgr.shape).round()
            for *xyxy, conf, cls in reversed(detections):
                results.append({
                    "class": self.names[int(cls)],
                    "confidence": float(conf),
                    "bbox": [float(value) for value in xyxy],
                })
        return results
