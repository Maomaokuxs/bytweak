from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    """通用后台线程：执行同步函数，避免阻塞 UI。"""
    finished_ok = Signal(object)
    finished_err = Signal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.finished_ok.emit(result)
        except Exception as e:
            self.finished_err.emit(str(e))
