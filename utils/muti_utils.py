from multiprocessing import Lock
from multiprocessing.managers import SyncManager


class FormatMsg:
    def __init__(self, source):
        self.source = source

    def to_str(self, msg, level="info", ):
        return f"msg::{level}${self.source}${msg}"


class CanStopThread:
    def __init__(self):
        self._running = True

    def terminate(self):
        self._running = False

    # 这是一个demo，请继承并重写次方法
    # def run(self):
    #     while self._running:
    #         time.sleep(5)


class ExecSig:
    def __init__(self, sig_dic: SyncManager.dict, sig_lock: Lock):
        self.sig_dic: dict = sig_dic
        self.sig_lock = sig_lock
        self._init_sig_dic()

    def _init_sig_dic(self):
        key_cnt = self.sig_dic.keys().__len__()
        if key_cnt < 1:
            self.sig_dic.update({
                "start": False,
                "pause": False,
                "stop": True,
            })

    def set_pause(self):
        with self.sig_lock:
            self.sig_dic.update({
                "start": False,
                "pause": True,
                "stop": False,
            })

    def set_start(self):
        with self.sig_lock:
            self.sig_dic.update({
                "start": True,
                "pause": False,
                "stop": False,
            })

    def set_stop(self):
        with self.sig_lock:
            self.sig_dic.update({
                "start": False,
                "pause": False,
                "stop": True,
            })

    def is_pause(self):
        return self.sig_dic["pause"]

    def is_stop(self):
        return self.sig_dic["stop"]

    def is_start(self):
        return self.sig_dic["start"]