"""
主题配置 - 参考 Kode-cli 的配色方案
"""

from dataclasses import dataclass
from typing import Optional
from rich.style import Style
from rich.theme import Theme as RichTheme


@dataclass
class Theme:
    """终端界面主题配置"""
    
    # 主色调
    primary: str = "bright_cyan"
    secondary: str = "bright_blue"
    
    # 状态颜色
    success: str = "bright_green"
    warning: str = "bright_yellow"
    error: str = "bright_red"
    info: str = "bright_blue"
    
    # 文本颜色
    text: str = "white"
    secondary_text: str = "bright_black"
    muted: str = "dim"
    
    # 边框颜色
    border: str = "bright_cyan"
    secondary_border: str = "bright_black"
    
    # 特殊颜色
    bash_border: str = "bright_yellow"
    prompt: str = "bright_cyan"
    user_input: str = "bright_white"
    assistant: str = "bright_green"
    
    def to_rich_theme(self) -> RichTheme:
        """转换为 Rich 主题"""
        return RichTheme({
            "primary": self.primary,
            "secondary": self.secondary,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
            "info": self.info,
            "text": self.text,
            "secondary_text": self.secondary_text,
            "muted": self.muted,
            "border": self.border,
            "prompt": self.prompt,
            "user_input": self.user_input,
            "assistant": self.assistant,
        })


# 默认主题实例
_default_theme = Theme()


def get_theme() -> Theme:
    """获取当前主题"""
    return _default_theme


def set_theme(theme: Theme) -> None:
    """设置主题"""
    global _default_theme
    _default_theme = theme
