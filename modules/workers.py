import time

from PySide6.QtCore import QThread, Signal, QTimer

from .utils import log_operation


class Worker(QThread):
    """通用后台线程：执行同步函数，避免阻塞 UI。

    label 为功能名（如 "软件包/安装 fastfetch"），完成/失败自动记操作日志。
    timeout 为看门狗秒数：超时仍未完成则判失败上报、界面不再死等；
    置 timed_out 标记，任务随后完成也不再二次上报（调用方 _cleanup
    须跳过 deleteLater，避免销毁仍在运行的线程）。"""

    finished_ok = Signal(object)
    finished_err = Signal(str)

    def __init__(self, fn, *args, label: str = "", timeout: float = 0, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._label = label or getattr(fn, "__name__", "task")
        self._timeout = timeout
        self.timed_out = False
        self._finished = False

    def start(self, *args, **kwargs):
        if self._timeout > 0:
            QTimer.singleShot(int(self._timeout * 1000), self._on_timeout)
        super().start(*args, **kwargs)

    def _on_timeout(self):
        if self._finished or not self.isRunning():
            return
        self.timed_out = True
        msg = f"操作超时（超过 {self._timeout:g} 秒），已终止等待"
        log_operation(self._label, False, self._timeout, msg)
        self.finished_err.emit(msg)

    def run(self):
        start = time.monotonic()
        try:
            result = self._fn(*self._args, **self._kwargs)
            self._finished = True
            if self.timed_out:
                return
            self.finished_ok.emit(result)
            log_operation(self._label, True, time.monotonic() - start)
        except Exception as e:
            self._finished = True
            if self.timed_out:
                return
            self.finished_err.emit(str(e))
            log_operation(self._label, False, time.monotonic() - start, str(e))
            # 关键点：完整堆栈落盘，供远程诊断
            from .utils import logger as _lg
            _lg.exception(f"Worker[{self._label}] failed")
