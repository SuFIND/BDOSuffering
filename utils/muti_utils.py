class OverSig(Exception):
    """正常结束"""
    pass


class StopSig(Exception):
    """停止信号"""
    pass


class ExceptionSig(Exception):
    """异常停止信号"""
    pass


class RetrySig(RuntimeError):
    def __init__(self, *args, **kwargs):
        super(RetrySig, self).__init__(*args)
        self.redo = []
        if 'redo' in kwargs:
            self.redo = kwargs.get("redo", [])


class FormatMsg:
    def __init__(self, source):
        self.source = source

    def to_str(self, msg, level="info", ):
        return f"{level}${self.source}${msg}"
