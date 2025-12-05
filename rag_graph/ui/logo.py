"""
Logo 组件 - 参考 Kode-cli 的启动界面
"""

import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from .theme import get_theme


# ASCII Logo - 类似 Kode-cli 风格
ASCII_LOGO = """
  ____                   _       ____      _    ____
 / ___|  _ __  __ _  _ __ | |__   |  _ \\    / \\  / ___|
| |  _  | '__|/ _` || '_ \\| '_ \\  | |_) |  / _ \\| |  _
| |_| | | |  | (_| || |_) | | | | |  _ <  / ___ \\ |_| |
 \\____| |_|   \\__,_|| .__/|_| |_| |_| \\_\\/_/   \\_\\____|
                    |_|
"""

PRODUCT_NAME = "GraphRAG"
PRODUCT_VERSION = "1.0.0"
PRODUCT_DESCRIPTION = "智能图RAG旅游助手"


class Logo:
    """Logo 显示组件"""
    
    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.theme = get_theme()
    
    def render(
        self,
        show_logo: bool = True,
        show_status: bool = True,
        neo4j_status: str = "未连接",
        milvus_status: str = "未连接",
        model_name: str = "未配置",
        cwd: str = None,
        update_available: str = None,
    ) -> None:
        """渲染 Logo 和状态信息"""
        
        content_lines = []
        
        # 更新提示
        if update_available:
            content_lines.append(f"[{self.theme.warning}]有新版本可用: {update_available}[/]")
            content_lines.append("")
        
        # 欢迎信息
        content_lines.append(
            f"[{self.theme.primary}]✻[/] 欢迎使用 [{self.theme.primary}][bold]{PRODUCT_NAME}[/bold][/] {PRODUCT_DESCRIPTION}!"
        )
        content_lines.append("")
        
        # 帮助信息和工作目录
        content_lines.append(f"  [{self.theme.secondary_text}][italic]/help 获取帮助信息[/italic][/]")
        if cwd:
            content_lines.append(f"  [{self.theme.secondary_text}]cwd: {cwd}[/]")
        
        # 服务状态
        if show_status:
            content_lines.append("")
            content_lines.append(f"  [{self.theme.secondary_text}]服务状态:[/]")
            
            # Neo4j 状态
            neo4j_color = self.theme.success if neo4j_status == "已连接" else self.theme.error
            content_lines.append(f"    • Neo4j: [{neo4j_color}]{neo4j_status}[/]")
            
            # Milvus 状态
            milvus_color = self.theme.success if milvus_status == "已连接" else self.theme.error
            content_lines.append(f"    • Milvus: [{milvus_color}]{milvus_status}[/]")
            
            # 模型信息
            content_lines.append(f"    • 模型: [{self.theme.secondary_text}]{model_name}[/]")
        
        # 创建面板
        panel = Panel(
            "\n".join(content_lines),
            border_style=self.theme.primary,
            box=box.ROUNDED,
            padding=(0, 1),
        )
        
        self.console.print(panel)
    
    def render_minimal(self) -> None:
        """渲染简洁版 Logo"""
        self.console.print(
            f"[{self.theme.primary}]✻[/] [{self.theme.primary}][bold]{PRODUCT_NAME}[/bold][/] v{PRODUCT_VERSION}",
            style=self.theme.text
        )


def show_logo(
    console: Console = None,
    neo4j_status: str = "未连接",
    milvus_status: str = "未连接", 
    model_name: str = "未配置",
    cwd: str = None,
) -> None:
    """显示 Logo 的便捷函数"""
    logo = Logo(console)
    logo.render(
        neo4j_status=neo4j_status,
        milvus_status=milvus_status,
        model_name=model_name,
        cwd=cwd or os.getcwd(),
    )
