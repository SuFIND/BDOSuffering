# -*- coding: utf-8 -*-
import random

import cv2
import onnxruntime as ort
import torch
import numpy as np
import torchvision.transforms as transforms


def color_threshold(rgb: tuple, threshold=0.95):
    lower_color = []
    upper_color = []
    for color in rgb:
        if color != 0:
            upper = min(round(color / threshold), 255)
        else:
            upper = 0
        lower = max(round(color * threshold), 0)
        lower_color.append(lower)
        upper_color.append(upper)
    return np.array(lower_color), np.array(upper_color)


def static_color_pix_count(img: np.ndarray, rgb, threshold=0.95):
    """
    统计图片中特定颜色区间内像素的取值
    :param img:
    :param rgb:
    :param threshold:
    :return:
    """
    # 获取色彩范围
    lower, upper = color_threshold(rgb, threshold=threshold)

    # 创建黑白图片
    mask = cv2.inRange(img[:, :, :3], lower, upper)

    # 计算黑色像素数量
    count = cv2.countNonZero(mask)
    return count


def resize_and_pad_img(img, target_height, target_width):
    """
    keep ratio and resize img and pad to target size
    :param img:
    :param target_height:
    :param target_width:
    :return:
    """
    height, width = img.shape[:2]
    ratio_h = height / target_height
    ratio_w = width / target_width
    ratio = max(ratio_h, ratio_w, 1)

    to_sub_width = max(target_width - width, 0)
    to_sub_height = max(target_height - height, 0)

    if ratio > 1:
        size = (int(width / ratio), int(height / ratio))
        img = cv2.resize(img, size, interpolation=cv2.INTER_CUBIC)
        to_sub_width = int(width / ratio)
        to_sub_height = int(height / ratio)

    pad_color = [114, 114, 114]

    a = target_width - to_sub_width
    b = target_height - to_sub_height

    after_pad_img = cv2.copyMakeBorder(img, 0, int(b), 0, int(a), cv2.BORDER_CONSTANT, value=pad_color)
    rst = {'ratio': ratio, "after_do_img": after_pad_img, 'pad_bottom': int(b), "pad_right": int(a)}
    return rst


def to_numpy(tensor: torch.Tensor):
    return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()


class Detector:
    img_scale = (640, 640)

    def __init__(self, onnx_file_path: str, labels_map: dict) -> None:
        providers = ["CPUExecutionProvider"]
        if torch.cuda.is_available():
            providers.insert(0, 'CUDAExecutionProvider')

        self.session = ort.InferenceSession(onnx_file_path, providers=providers)
        self.labels_map = labels_map
        self.output_names = [one.name for one in self.session.get_outputs()]

        self.labels_color_map = {}
        for _, label in self.labels_map.items():
            color = [random.randint(0, 255) for _ in range(3)]
            self.labels_color_map[label] = color

    def labels(self):
        """
        获取标签
        :return:
        """
        return [val for _, val in self.labels_map.items()]

    def infer(self, or_img: np.ndarray, min_score=0.6) -> dict:
        """
        进行推理
        :return:
        """
        rst = {}

        # 转换为BGR通道
        bgr_img = cv2.cvtColor(or_img, cv2.COLOR_RGB2BGR)

        # pad and resize
        pre_do_rst = resize_and_pad_img(bgr_img, self.img_scale[0], self.img_scale[1])
        ip_img = pre_do_rst["after_do_img"]
        ratio = pre_do_rst['ratio']  # > 1

        to_tensor = transforms.ToTensor()
        ip_tensor = to_tensor(ip_img)
        ip_tensor.unsqueeze_(0)

        inputs = {"images": to_numpy(ip_tensor)}
        onnx_infer_outputs = self.session.run(self.output_names, inputs)

        cache = {}
        for item_name, val in zip(self.output_names, onnx_infer_outputs):
            cache[item_name] = val[0]

        num_dets = cache["num_dets"][0]
        for det_idx in range(num_dets):
            score = cache['scores'][det_idx]
            # 过滤置信度低于阀值的目标
            if score < min_score:
                continue

            # top, left, bottom, right
            bbox = cache['boxes'][det_idx]
            bbox = [round(i) for i in bbox]
            or_bbox = [int(i * ratio) for i in bbox]
            label = self.labels_map[cache["labels"][det_idx]]

            rst.setdefault(label, [])
            rst[label].append({
                "score": score,
                "bbox": or_bbox,
            })

        return rst

    def test(self, img: np.ndarray, min_score=0.7) -> np.ndarray:
        """可视化测试"""

        rst = self.infer(img, min_score)

        for label, dets in rst.items():
            for det in dets:
                bbox = det["bbox"]
                score = det["score"]

                color = self.labels_color_map[label]

                name = f'{label}:{score:0.4f}'

                cv2.rectangle(img, bbox[:2], bbox[2:], color, 2)
                cv2.putText(
                    img,
                    name, (bbox[0], bbox[1] - 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75, [225, 255, 255],
                    thickness=2)
        return img
