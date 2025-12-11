"""
IR Camera Viewer - 红外摄像头查看器

常量和枚举定义
"""

from enum import Enum


class IRFrameFilter(Enum):
    """帧过滤模式
    
    红外摄像头会交替发送照明帧和原始帧：
    - 照明帧：红外 LED 开启时捕获
    - 原始帧：红外 LED 关闭时捕获
    """
    NONE = 0        # 不过滤，显示所有帧
    RAW = 1         # 仅显示原始帧（LED 关闭）
    ILLUMINATED = 2  # 仅显示照明帧（LED 开启）
    
    def next(self):
        """获取下一个过滤模式"""
        members = list(self.__class__)
        idx = (self.value + 1) % len(members)
        return members[idx]
    
    @property
    def display_name(self):
        """显示名称"""
        names = {
            IRFrameFilter.NONE: "OFF",
            IRFrameFilter.RAW: "RAW",
            IRFrameFilter.ILLUMINATED: "ILLUM"
        }
        return names.get(self, "OFF")


class IRMappingMode(Enum):
    """颜色映射模式"""
    NONE = 0        # 原始灰度
    GREEN = 1       # 绿色映射
    HEAT = 2        # 热力图
    JET = 3         # Jet 色彩映射
    
    def next(self):
        """获取下一个映射模式"""
        members = list(self.__class__)
        idx = (self.value + 1) % len(members)
        return members[idx]
    
    @property
    def display_name(self):
        """显示名称"""
        names = {
            IRMappingMode.NONE: "OFF",
            IRMappingMode.GREEN: "GREEN",
            IRMappingMode.HEAT: "HEAT",
            IRMappingMode.JET: "JET"
        }
        return names.get(self, "OFF")


# UI 颜色常量
class Colors:
    """UI 颜色定义 (BGR 格式)"""
    BACKGROUND = (40, 40, 40)
    BUTTON = (80, 80, 80)
    BUTTON_HOVER = (100, 100, 100)
    BUTTON_ACTIVE = (0, 120, 0)
    BUTTON_RECORDING = (0, 0, 255)
    TEXT = (255, 255, 255)
    TEXT_SUCCESS = (0, 255, 0)
    TEXT_RECORDING = (0, 0, 255)
    BORDER = (120, 120, 120)


# UI 布局常量
class Layout:
    """UI 布局参数"""
    CONTROL_PANEL_HEIGHT = 60  # 单行按钮高度
    CONTROL_PANEL_HEIGHT_2ROWS = 105  # 双行按钮高度
    BUTTON_HEIGHT = 35
    BUTTON_WIDTH = 100  # 按钮宽度
    BUTTON_MARGIN = 5   # 减小间距
    BUTTONS_PER_ROW = 6  # 每行按钮数量
    MIN_WINDOW_WIDTH = 640
    STATUS_DISPLAY_TIME = 3  # 状态消息显示时间（秒）
