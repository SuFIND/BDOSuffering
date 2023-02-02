# -*- coding: utf-8 -*-
import cv2
import numpy as np


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
