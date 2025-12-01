"""
IR Camera Viewer - 红外摄像头查看器

GUI 组件模块
"""

import cv2
import time
from constants import Colors, Layout


class Button:
    """按钮组件"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 text: str, action: callable):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.action = action
        self.hover = False
        self.active = False  # 用于切换按钮状态
    
    def contains(self, px: int, py: int) -> bool:
        """检查点是否在按钮内"""
        return (self.x <= px <= self.x + self.width and
                self.y <= py <= self.y + self.height)
    
    def draw(self, img, font_scale: float = 0.5):
        """绘制按钮"""
        # 确定颜色
        if self.active:
            color = Colors.BUTTON_RECORDING
        elif self.hover:
            color = Colors.BUTTON_HOVER
        else:
            color = Colors.BUTTON
        
        # 绘制背景
        cv2.rectangle(img, 
                     (self.x, self.y), 
                     (self.x + self.width, self.y + self.height),
                     color, -1)
        
        # 绘制边框
        cv2.rectangle(img,
                     (self.x, self.y),
                     (self.x + self.width, self.y + self.height),
                     Colors.BORDER, 1)
        
        # 绘制文本
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(self.text, font, font_scale, 1)[0]
        text_x = self.x + (self.width - text_size[0]) // 2
        text_y = self.y + (self.height + text_size[1]) // 2
        cv2.putText(img, self.text, (text_x, text_y),
                   font, font_scale, Colors.TEXT, 1, cv2.LINE_AA)


class StatusBar:
    """状态栏组件"""
    
    def __init__(self):
        self.message = ""
        self.timestamp = 0
        self.display_time = Layout.STATUS_DISPLAY_TIME
    
    def set_message(self, message: str):
        """设置状态消息"""
        self.message = message
        self.timestamp = time.time()
    
    def draw(self, img, x: int, y: int, font_scale: float = 0.5):
        """绘制状态消息"""
        if self.message and time.time() - self.timestamp < self.display_time:
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(img, self.message, (x, y),
                       font, font_scale, Colors.TEXT_SUCCESS, 1, cv2.LINE_AA)


class RecordingIndicator:
    """录像指示器组件"""
    
    def __init__(self):
        self.blink_interval = 0.5
        self.last_blink = 0
        self.visible = True
    
    def draw(self, img, x: int, y: int):
        """绘制录像指示器"""
        # 闪烁效果
        if time.time() - self.last_blink > self.blink_interval:
            self.visible = not self.visible
            self.last_blink = time.time()
        
        if self.visible:
            cv2.circle(img, (x, y), 8, Colors.TEXT_RECORDING, -1)
            cv2.putText(img, "REC", (x - 30, y + 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, Colors.TEXT_RECORDING, 1)


class ControlPanel:
    """控制面板"""
    
    def __init__(self, width: int, height: int, y_offset: int):
        self.width = width
        self.height = height
        self.y_offset = y_offset
        self.buttons = []
        self.status_bar = StatusBar()
        self.recording_indicator = RecordingIndicator()
    
    def add_button(self, text: str, action: callable) -> Button:
        """添加按钮"""
        # 计算按钮位置
        row = len(self.buttons) // 5
        col = len(self.buttons) % 5
        
        x = Layout.BUTTON_MARGIN + col * (Layout.BUTTON_WIDTH + Layout.BUTTON_MARGIN)
        y = self.y_offset + Layout.BUTTON_MARGIN + row * (Layout.BUTTON_HEIGHT + Layout.BUTTON_MARGIN)
        
        button = Button(x, y, Layout.BUTTON_WIDTH, Layout.BUTTON_HEIGHT, text, action)
        self.buttons.append(button)
        return button
    
    def add_button_at(self, x: int, y: int, width: int, text: str, action: callable) -> Button:
        """在指定位置添加按钮"""
        button = Button(x, y, width, Layout.BUTTON_HEIGHT, text, action)
        self.buttons.append(button)
        return button
    
    def handle_mouse(self, x: int, y: int, clicked: bool):
        """处理鼠标事件"""
        for button in self.buttons:
            button.hover = button.contains(x, y)
            if clicked and button.hover:
                button.action()
    
    def draw(self, img, is_recording: bool = False):
        """绘制控制面板"""
        # 绘制背景
        cv2.rectangle(img, 
                     (0, self.y_offset),
                     (self.width, self.y_offset + self.height),
                     Colors.BACKGROUND, -1)
        
        # 绘制分隔线
        cv2.line(img, (0, self.y_offset), (self.width, self.y_offset), Colors.BORDER, 1)
        
        # 绘制按钮
        for button in self.buttons:
            button.draw(img)
        
        # 绘制状态栏
        status_y = self.y_offset + self.height - 15
        self.status_bar.draw(img, 10, status_y)
        
        # 绘制录像指示器
        if is_recording:
            self.recording_indicator.draw(img, self.width - 50, self.y_offset + 25)
    
    def set_status(self, message: str):
        """设置状态消息"""
        self.status_bar.set_message(message)
