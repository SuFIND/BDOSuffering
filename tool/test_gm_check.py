import cv2
from win32gui import FindWindow
from utils.capture_utils import WinDCApiCap
from utils.cv_utils import color_threshold

# 请配合spy++确认名称
# 查找的windows窗体名称
window_title = "黑色沙漠 - 435534"
# 查找的windows窗体类名称
window_class = "BlackDesertWindowClass"


def main():
    # GM字体颜色 rgb
    gm_chat_color = (57, 181, 47,)
    # 颜色相似度阈值
    threshold = 0.6

    hwnd = FindWindow(window_class, window_title)
    win_dc = WinDCApiCap(hwnd)
    # 获取截图
    sc_np = win_dc.get_hwnd_screenshot_to_numpy_array()

    # 获取截图的长宽高
    or_h, or_w = sc_np.shape[:2]

    # 切割获取右下角的玩家聊天框小图减少干扰
    start_row = round(or_h / 4 * 3)
    end_row = or_h
    start_col = 0
    end_col = round(or_w / 4)
    cropped = sc_np[start_row:end_row, start_col:end_col, :3]
    # 展示切割后的原图
    cv2.imshow("after cropped", cropped)
    cv2.waitKey(0)

    # 获取色彩范围
    lower, upper = color_threshold(gm_chat_color, threshold=threshold)
    # 创建黑白图片
    mask = cv2.inRange(cropped[:, :, :3], lower, upper)

    # 展示套用黑白蒙层后的图片
    cv2.imshow("after mask", mask)
    cv2.waitKey(0)

    # 计算黑色像素数量
    count = cv2.countNonZero(mask)
    print("find pix count", count)


if __name__ == '__main__':
    main()
