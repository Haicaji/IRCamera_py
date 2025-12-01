"""
IR Camera Viewer - 红外摄像头查看器

主应用程序入口
"""

import asyncio
import cv2
import numpy as np
import os

from constants import Layout
from camera_controller import IRCameraController
from gui_components import ControlPanel
from logger import log_info, log_error, log_warning


class IRCameraApp:
    """红外摄像头应用程序"""
    
    WINDOW_NAME = "IR Camera Viewer"
    
    def __init__(self):
        self.controller = IRCameraController()
        self.loop = None
        
        # 窗口尺寸
        self.window_width = Layout.MIN_WINDOW_WIDTH
        self.window_height = 480 + Layout.CONTROL_PANEL_HEIGHT
        
        # UI 组件
        self.control_panel = None
        
        # 按钮引用（用于更新文本）
        self.btn_record = None
        self.btn_filter = None
        self.btn_color = None
        self.btn_device = None
    
    def _setup_ui(self):
        """设置 UI 组件"""
        # 根据设备数量决定是否需要双行
        has_multi_devices = len(self.controller.devices) > 1
        panel_height = Layout.CONTROL_PANEL_HEIGHT_2ROWS if has_multi_devices else Layout.CONTROL_PANEL_HEIGHT
        panel_y = self.window_height - panel_height
        
        self.control_panel = ControlPanel(
            self.window_width,
            panel_height,
            panel_y
        )
        
        # 第一行按钮
        self.control_panel.add_button("Photo", self._on_photo)
        self.btn_record = self.control_panel.add_button("Record", self._on_record)
        self.btn_filter = self.control_panel.add_button("Filter: OFF", self._on_filter)
        self.btn_color = self.control_panel.add_button("Color: OFF", self._on_color)
        
        # 设备切换按钮（多设备时显示在第二行）
        if has_multi_devices:
            device_y = panel_y + Layout.BUTTON_HEIGHT + Layout.BUTTON_MARGIN * 2
            device_width = self.window_width - Layout.BUTTON_MARGIN * 2
            self.btn_device = self.control_panel.add_button_at(
                Layout.BUTTON_MARGIN, device_y, device_width,
                "Device", self._on_device
            )
    
    def _update_button_texts(self):
        """更新按钮文本"""
        if self.btn_record:
            self.btn_record.text = "Stop" if self.controller.is_recording else "Record"
            self.btn_record.active = self.controller.is_recording
        
        if self.btn_filter:
            self.btn_filter.text = f"Filter: {self.controller.frame_filter.display_name}"
        
        if self.btn_color:
            self.btn_color.text = f"Color: {self.controller.mapping_mode.display_name}"
        
        if self.btn_device:
            names = self.controller.get_device_names()
            idx = self.controller.current_device_index
            self.btn_device.text = f"Device: {names[idx]}"
    
    # ==================== 事件处理 ====================
    
    def _on_photo(self):
        """拍照"""
        path = self.controller.take_photo()
        if path:
            self.control_panel.set_status(f"Saved: {os.path.basename(path)}")
    
    def _on_record(self):
        """录像"""
        if self.controller.is_recording:
            path = self.controller.stop_recording()
            if path:
                self.control_panel.set_status(f"Saved: {os.path.basename(path)}")
        else:
            path = self.controller.start_recording()
            if path:
                self.control_panel.set_status("Recording...")
    
    def _on_filter(self):
        """切换帧过滤"""
        self.controller.frame_filter = self.controller.frame_filter.next()
    
    def _on_color(self):
        """切换颜色映射"""
        self.controller.mapping_mode = self.controller.mapping_mode.next()
    
    def _on_device(self):
        """切换设备"""
        if len(self.controller.devices) <= 1:
            return
        
        next_idx = (self.controller.current_device_index + 1) % len(self.controller.devices)
        self.loop.run_until_complete(self.controller.select_device(next_idx))
        self.loop.run_until_complete(self.controller.start())
        
        names = self.controller.get_device_names()
        self.control_panel.set_status(f"Device: {names[next_idx]}")
    
    def _on_mouse(self, event, x, y, flags, param):
        """鼠标事件回调"""
        clicked = event == cv2.EVENT_LBUTTONDOWN
        self.control_panel.handle_mouse(x, y, clicked)
    
    # ==================== 主循环 ====================
    
    def _render_frame(self, frame) -> np.ndarray:
        """渲染完整画面"""
        # 创建显示画面
        display = np.zeros((self.window_height, self.window_width, 4), dtype=np.uint8)
        
        if frame is not None:
            # 调整帧大小
            frame_height = self.window_height - Layout.CONTROL_PANEL_HEIGHT
            frame_resized = cv2.resize(frame, (self.window_width, frame_height))
            display[:frame_height, :] = frame_resized
        else:
            # 等待画面
            cv2.putText(display, "Waiting for frames...",
                       (self.window_width // 2 - 100, 
                        (self.window_height - Layout.CONTROL_PANEL_HEIGHT) // 2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 1)
        
        # 更新按钮文本
        self._update_button_texts()
        
        # 绘制控制面板
        self.control_panel.draw(display, self.controller.is_recording)
        
        # 转换为 BGR
        return cv2.cvtColor(display, cv2.COLOR_BGRA2BGR)
    
    def run(self):
        """运行应用"""
        log_info("=" * 40)
        log_info("IR Camera Viewer")
        log_info("=" * 40)
        
        # 初始化事件循环
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self._initialize()
            self._main_loop()
        except Exception as e:
            log_error(f"Error: {e}")
        finally:
            self._cleanup()
    
    def _initialize(self):
        """初始化"""
        log_info("Searching for IR cameras...")
        
        # 查找设备
        devices = self.loop.run_until_complete(self.controller.find_ir_cameras())
        
        if not devices:
            raise RuntimeError("No IR camera found")
        
        log_info(f"Found {len(devices)} IR device(s):")
        for i, name in enumerate(self.controller.get_device_names()):
            log_info(f"  [{i}] {name}")
        
        # 选择第一个设备
        log_info("Initializing device...")
        if not self.loop.run_until_complete(self.controller.select_device(0)):
            raise RuntimeError("Failed to initialize device")
        
        # 更新窗口尺寸
        cam_w, cam_h = self.controller.frame_size
        self.window_width = max(cam_w, Layout.MIN_WINDOW_WIDTH)
        
        # 根据设备数量决定控制面板高度
        has_multi_devices = len(self.controller.devices) > 1
        panel_height = Layout.CONTROL_PANEL_HEIGHT_2ROWS if has_multi_devices else Layout.CONTROL_PANEL_HEIGHT
        self.window_height = cam_h + panel_height
        log_info(f"Resolution: {cam_w}x{cam_h}")
        
        # 开始捕获
        if not self.loop.run_until_complete(self.controller.start()):
            raise RuntimeError("Failed to start capture")
        
        # 设置 UI
        self._setup_ui()
        
        # 创建窗口
        cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.WINDOW_NAME, self.window_width, self.window_height)
        cv2.setMouseCallback(self.WINDOW_NAME, self._on_mouse)
        
        log_info("Application started")
    
    def _main_loop(self):
        """主循环"""
        while self.controller.is_running:
            # 检查窗口是否被关闭
            if cv2.getWindowProperty(self.WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                break
            
            # 获取帧
            frame = self.controller.get_frame()
            
            # 渲染
            display = self._render_frame(frame)
            cv2.imshow(self.WINDOW_NAME, display)
            
            # 处理按键
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q') or key == 27:  # q 或 ESC
                break
    
    def _cleanup(self):
        """清理资源"""
        log_info("Shutting down...")
        self.loop.run_until_complete(self.controller.stop())
        cv2.destroyAllWindows()
        self.loop.close()
        log_info("Application closed")


def main():
    """程序入口"""
    app = IRCameraApp()
    app.run()


if __name__ == "__main__":
    main()
