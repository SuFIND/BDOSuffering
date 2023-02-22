# -*- coding: utf-8 -*-
# @Desc: 半自动标注数据
import json
import os

import cv2

from app.init_func import init_labels_dic
from utils.cv_utils import Detector

img_dir = ""
labels_dir = ""
onnx_path = ""
label_cls_path = ""
min_score = 0.6


def auto_label():
    # providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    providers = ["CPUExecutionProvider"]
    labels = init_labels_dic(label_cls_path)
    detector = Detector(onnx_path, labels, providers)

    for img_file in os.listdir(img_dir):
        img_name, file_format = img_file.split(".")
        if file_format != "json":
            continue
        img = cv2.imread(os.path.join(img_dir, img_file))
        infer_rst = detector.infer(img, min_score=min_score)

        shapes = []
        for label, infos in infer_rst.items():
            for info in infos:
                shape = {
                    "label": label,
                    "points": [[
                        info["bbox"][0],
                        info["bbox"][1]
                    ], [
                        info["bbox"][2],
                        info["bbox"][3],
                    ]],
                    "group_id": None,
                    "shape_type": "rectangle",
                    "flags": {}
                }
                shapes.append(shape)

        labelmeJsonStruct = {
            "version": "5.0.5",
            "flags": {},
            "shapes": shapes,
            "imagePath": f"../images/{img_name}.json",
            "imageData": None,
            "imageHeight": img.size[0],
            "imageWidth": img.size[1],
        }

        with open(os.path.join(labels_dir, f"{img_name}.json"), "w", encoding="uft8") as fp:
            json.dump(labelmeJsonStruct, fp, ensure_ascii=False)


if __name__ == '__main__':
    auto_label()
