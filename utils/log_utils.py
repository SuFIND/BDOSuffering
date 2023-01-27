import os


class Logger:
    import logging.handlers
    # 初始化日志模块
    logging.basicConfig()
    _logger = logging.getLogger("app")
    _logger.setLevel(logging.INFO)
    _log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(_log_dir):
        os.mkdir(_log_dir)
    _timeFileHandler = logging.handlers.TimedRotatingFileHandler(
        os.path.join(_log_dir, "BDOWingman.log"),
        when='midnight',
        interval=1,
        backupCount=7
    )
    _timeFileHandler.suffix = "%Y-%m-%d_%H-%M-%S.log"
    _formatter = logging.Formatter('%(asctime)s|%(name)s | %(levelname)s | %(message)s')
    _timeFileHandler.setFormatter(_formatter)
    _logger.addHandler(_timeFileHandler)

    @classmethod
    def error(cls, msg, *args, **kwargs):
        cls._logger.error(msg, *args, **kwargs)

    @classmethod
    def info(cls, msg, *args, **kwargs):
        cls._logger.info(msg, *args, **kwargs)

    @classmethod
    def warning(cls, msg, *args, **kwargs):
        cls._logger.warning(msg, *args, **kwargs)

    @classmethod
    def debug(cls, msg, *args, **kwargs):
        cls._logger.debug(msg, *args, **kwargs)