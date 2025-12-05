"""
Spinner 组件 - 参考 Kode-cli 的加载动画
"""

import sys
import time
import random
import threading
from typing import Optional, List, Callable
from contextlib import contextmanager
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.spinner import Spinner as RichSpinner
from .theme import get_theme


# 加载动画字符 - 类似 Kode-cli
SPINNER_FRAMES = ['·', '✢', '✳', '∗', '✻', '✽']

# 加载提示语 - 类似 Kode-cli 的有趣提示
LOADING_MESSAGES = [
    "思考中",
    "推理中",
    "计算中",
    "分析中",
    "检索中",
    "处理中",
    "生成中",
    "整合中",
    "理解中",
    "探索中",
    "组织中",
    "构建中",
    "优化中",
    "联想中",
    "匹配中",
]


class Spinner:
    """自定义 Spinner 动画组件"""
    
    def __init__(
        self, 
        console: Console = None,
        message: str = None,
        show_elapsed: bool = True,
        show_interrupt_hint: bool = True,
    ):
        self.console = console or Console()
        self.theme = get_theme()
        self.message = message or random.choice(LOADING_MESSAGES)
        self.show_elapsed = show_elapsed
        self.show_interrupt_hint = show_interrupt_hint
        
        self._running = False
        self._start_time = 0
        self._frame_index = 0
        self._thread: Optional[threading.Thread] = None
        self._live: Optional[Live] = None
    
    def _get_frame(self) -> str:
        """获取当前动画帧"""
        frames = SPINNER_FRAMES + SPINNER_FRAMES[::-1]
        frame = frames[self._frame_index % len(frames)]
        self._frame_index += 1
        return frame
    
    def _render(self) -> Text:
        """渲染 Spinner 文本"""
        text = Text()
        
        # 动画字符
        text.append(self._get_frame(), style=self.theme.primary)
        text.append(" ")
        
        # 消息
        text.append(f"{self.message}… ", style=self.theme.primary)
        
        # 已用时间
        if self.show_elapsed:
            elapsed = int(time.time() - self._start_time)
            text.append(f"({elapsed}s", style=self.theme.secondary_text)
            
            if self.show_interrupt_hint:
                text.append(" · ", style=self.theme.secondary_text)
                text.append("esc", style=f"bold {self.theme.secondary_text}")
                text.append(" 中断", style=self.theme.secondary_text)
            
            text.append(")", style=self.theme.secondary_text)
        
        return text
    
    def start(self) -> None:
        """启动 Spinner"""
        self._running = True
        self._start_time = time.time()
        self._frame_index = 0
        
        self._live = Live(
            self._render(),
            console=self.console,
            refresh_per_second=8,
            transient=True,
        )
        self._live.start()
        
        def update_loop():
            while self._running:
                if self._live:
                    self._live.update(self._render())
                time.sleep(0.12)
        
        self._thread = threading.Thread(target=update_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """停止 Spinner"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)
        if self._live:
            self._live.stop()
            self._live = None
    
    def update_message(self, message: str) -> None:
        """更新消息"""
        self.message = message


@contextmanager
def SpinnerContext(
    message: str = None,
    console: Console = None,
    show_elapsed: bool = True,
    show_interrupt_hint: bool = True,
):
    """Spinner 上下文管理器"""
    spinner = Spinner(
        console=console,
        message=message,
        show_elapsed=show_elapsed,
        show_interrupt_hint=show_interrupt_hint,
    )
    try:
        spinner.start()
        yield spinner
    finally:
        spinner.stop()


class ProgressSpinner:
    """带进度的 Spinner"""
    
    def __init__(
        self,
        console: Console = None,
        total: int = 100,
        message: str = "处理中",
    ):
        self.console = console or Console()
        self.theme = get_theme()
        self.total = total
        self.current = 0
        self.message = message
        self._live: Optional[Live] = None
    
    def _render(self) -> Text:
        """渲染进度文本"""
        text = Text()
        
        # 进度条
        progress = self.current / self.total if self.total > 0 else 0
        bar_width = 20
        filled = int(bar_width * progress)
        
        text.append("[", style=self.theme.secondary_text)
        text.append("█" * filled, style=self.theme.primary)
        text.append("░" * (bar_width - filled), style=self.theme.secondary_text)
        text.append("] ", style=self.theme.secondary_text)
        
        # 百分比
        text.append(f"{int(progress * 100)}% ", style=self.theme.primary)
        
        # 消息
        text.append(self.message, style=self.theme.secondary_text)
        
        return text
    
    def start(self) -> None:
        """启动进度显示"""
        self._live = Live(
            self._render(),
            console=self.console,
            refresh_per_second=4,
            transient=True,
        )
        self._live.start()
    
    def update(self, current: int, message: str = None) -> None:
        """更新进度"""
        self.current = current
        if message:
            self.message = message
        if self._live:
            self._live.update(self._render())
    
    def stop(self) -> None:
        """停止进度显示"""
        if self._live:
            self._live.stop()
            self._live = None
