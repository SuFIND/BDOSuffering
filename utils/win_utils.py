import sys
from ctypes import wintypes, windll, byref, sizeof

import win32gui, win32api, win32con
from app.init_resource import global_var

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


def get_bdo_rect(hwnd):
    try:
        f = windll.dwmapi.DwmGetWindowAttribute
    except WindowsError:
        f = None
    title_height = global_var["BDO_window_title_bar_height"]
    have_borderless = is_borderless(hwnd)
    if f:
        rect = wintypes.RECT()
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        f(wintypes.HWND(hwnd),
          wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
          byref(rect),
          sizeof(rect)
          )
        if have_borderless:
            return rect.left, rect.top + title_height, rect.right, rect.bottom
        else:
            return rect.left, rect.top, rect.right, rect.bottom
    else:
        rect = win32gui.GetWindowRect(hwnd)
        title_height = win32api.GetSystemMetrics(12)
        if have_borderless:
            return rect[0], rect[1] + title_height, rect[2], rect[4]
        else:
            return rect[0], rect[1], rect[2], rect[4]


def is_borderless(hwnd):
    """
    判断窗口是否有边框
    :param hwnd:
    :return:
    """
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    return style & win32con.WS_POPUP == win32con.WS_POPUP


def set_unmuted():
    """
    设置不禁音
    :return:
    """
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))

    # 如果当前设备被静音了
    if volume.GetMute():
        volume.SetMute(0, None)


def is_admin():
    """
    是否是管理员权限
    :return:
    """
    try:
        return windll.shell32.IsUserAnAdmin()
    except:
        return False


def apply_admin_runtime():
    """
    申请管理员权限运行
    :return:
    """
    windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
