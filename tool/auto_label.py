# -*- coding: utf-8 -*-
# @Desc: 半自动标注数据
import json
import os
import argparse

import cv2
from tqdm import tqdm

from app.init_func import init_labels_dic
from utils.cv_utils import Detector


def dump_labelme_json(infer_rst: dict, img_height: int, img_width: int, dump_path: str, img_name: str):
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
        "imagePath": f"../images/{img_name}",
        "imageData": None,
        "imageHeight": img_height,
        "imageWidth": img_width,
    }

    with open(dump_path, "w", encoding="utf8") as fp:
        json.dump(labelmeJsonStruct, fp, ensure_ascii=False)


def auto_label(args):
    task = getattr(args, "task")
    img_dir = getattr(args, "img-dir")
    out_dir = getattr(args, "out-dir")
    onnx_path = getattr(args, "onnx-path")
    label_dic_path = getattr(args, "label-dic-path")
    confidence = getattr(args, "confidence")

    # providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    providers = ["CPUExecutionProvider"]
    labels = init_labels_dic(label_dic_path)
    detector = Detector(onnx_path, labels, providers)

    # 标签文件夹不存在则创建标签文件夹
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        print(f"created labels file dir {out_dir}")

    msg = ""

    for img_file in tqdm(os.listdir(img_dir)):
        img_name, file_format = img_file.split(".")
        if file_format not in {"png", "jpg", "jpeg"}:
            continue
        src_path = os.path.join(img_dir, img_file)
        img = cv2.imread(src_path)
        img_h = img.shape[0]
        img_w = img.shape[1]
        dump_path = os.path.join(out_dir, f"{img_name}.json")
        infer_rst = detector.infer(img, min_score=confidence)

        # 如果任务是自动标注的话
        if task == "autoLabel":
            dump_labelme_json(infer_rst, img_h, img_w, dump_path, img_file)

        if task == "negativeSampleCollection":
            to_monitor_labels = getattr(args, "to_monitor_labels")

            no_found = []
            for label in to_monitor_labels:
                if label in infer_rst:
                    continue
                no_found.append(label)

            # 说明该样本在该模型下有我们监控的样本，故跳过说鸡
            if len(no_found) < 1:
                os.remove(src_path)
                continue
            reason = ",".join(no_found)
            dump_labelme_json(infer_rst, img_h, img_w, dump_path, img_file)
            msg += f"{dump_path}\t{reason}\n"

    print("result:\n", msg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Auto Label',
        description='自动标注及负样本收集工具')
    parser.add_argument("task", type=str, choices=['autoLabel', 'negativeSampleCollection'], help="任务模式")
    parser.add_argument('img-dir', type=str, default='images', help='样本图片文件夹的路径')
    parser.add_argument('out-dir', type=str, default='labels', help='labelme标签文件输出的路径')
    parser.add_argument('onnx-path', type=str, help='用于半自动辅助标注的onnx模型文件路径')
    parser.add_argument('label-dic-path', type=str, help='用于半自动辅助标注的onnx模型标签文件路径')
    parser.add_argument('-prefix', '--img-path-prefix', type=str, default='../images',
                        help='生成的labelme的.json文件中，imagePath的路径前缀')
    parser.add_argument('-c', '--confidence', type=float, default=0.6, help='采用模型结果的最低置信度')
    args = parser.parse_args()

    # 如果任务是负样本收集
    if args.task == "negativeSampleCollection":
        print("请输入要监视的标签，并使用半角,分割标签：", end="")
        to_monitor_labels_str = input()
        setattr(args, "to_monitor_labels", to_monitor_labels_str.split(","))

    auto_label(args)
