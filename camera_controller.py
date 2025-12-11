"""
IR Camera Viewer - 红外摄像头查看器

摄像头控制器模块
"""

import asyncio
import cv2
import numpy as np
from threading import Lock
from queue import Queue, Empty
from datetime import datetime
import os

from winrt.windows.media.capture import (
    MediaCapture,
    MediaCaptureInitializationSettings,
    MediaCaptureSharingMode,
    StreamingCaptureMode,
    MediaCaptureMemoryPreference,
)
from winrt.windows.media.capture.frames import (
    MediaFrameSourceGroup,
    MediaFrameSourceKind,
    MediaFrameReaderAcquisitionMode,
)
from winrt.windows.graphics.imaging import (
    SoftwareBitmap,
    BitmapPixelFormat,
    BitmapBufferAccessMode,
)

from constants import IRFrameFilter, IRMappingMode


class IRCameraController:
    """红外摄像头控制器
    
    负责：
    - 设备发现和选择
    - 帧捕获和处理
    - 帧过滤和颜色映射
    - 拍照和录像
    """

    def __init__(self):
        # 媒体捕获相关
        self._media_capture = None
        self._frame_reader = None
        self._lock = Lock()
        self._running = False
        
        # 帧队列
        self._frame_queue = Queue(maxsize=2)
        self._last_frame = None
        
        # 设备信息
        self._devices = []
        self._current_device_index = 0
        self._frame_width = 640
        self._frame_height = 480
        
        # 处理选项
        self._frame_filter = IRFrameFilter.NONE
        self._mapping_mode = IRMappingMode.NONE
        self._is_illuminated = False
        
        # 录像相关
        self._is_recording = False
        self._video_writer = None
        self._video_path = None

    # ==================== 属性 ====================
    
    @property
    def frame_filter(self) -> IRFrameFilter:
        return self._frame_filter
    
    @frame_filter.setter
    def frame_filter(self, value: IRFrameFilter):
        self._frame_filter = value

    @property
    def mapping_mode(self) -> IRMappingMode:
        return self._mapping_mode
    
    @mapping_mode.setter
    def mapping_mode(self, value: IRMappingMode):
        self._mapping_mode = value

    @property
    def devices(self) -> list:
        return self._devices

    @property
    def current_device_index(self) -> int:
        return self._current_device_index

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @property
    def frame_size(self) -> tuple:
        return (self._frame_width, self._frame_height)

    @property
    def is_running(self) -> bool:
        return self._running

    # ==================== 设备管理 ====================

    async def find_ir_cameras(self) -> list:
        """查找所有红外摄像头设备"""
        self._devices = []
        devices = await MediaFrameSourceGroup.find_all_async()
        
        for device in devices:
            source_infos = device.source_infos
            if source_infos and len(source_infos) > 0:
                for source_info in source_infos:
                    if source_info.source_kind == MediaFrameSourceKind.INFRARED:
                        self._devices.append(device)
                        break
        
        return self._devices

    def get_device_names(self) -> list:
        """获取设备名称列表"""
        return [d.display_name for d in self._devices]

    async def select_device(self, index: int, exclusive: bool = False) -> bool:
        """选择指定索引的设备"""
        if index < 0 or index >= len(self._devices):
            return False
        
        # 停止当前捕获
        if self._frame_reader is not None:
            await self.stop()
        
        device = self._devices[index]
        self._current_device_index = index
        
        # 初始化 MediaCapture
        self._media_capture = MediaCapture()
        
        settings = MediaCaptureInitializationSettings()
        settings.source_group = device
        settings.sharing_mode = (MediaCaptureSharingMode.EXCLUSIVE_CONTROL 
                                 if exclusive else MediaCaptureSharingMode.SHARED_READ_ONLY)
        settings.streaming_capture_mode = StreamingCaptureMode.VIDEO
        settings.memory_preference = MediaCaptureMemoryPreference.CPU
        
        try:
            await self._media_capture.initialize_with_settings_async(settings)
        except Exception:
            if exclusive:
                # 尝试共享模式
                settings.sharing_mode = MediaCaptureSharingMode.SHARED_READ_ONLY
                await self._media_capture.initialize_with_settings_async(settings)
            else:
                raise
        
        # 获取帧源
        frame_sources = self._media_capture.frame_sources
        if not frame_sources:
            return False
        
        frame_source = next(iter(frame_sources.values()), None)
        if frame_source is None:
            return False
        
        # 选择最佳格式
        supported_formats = frame_source.supported_formats
        if supported_formats and len(supported_formats) > 0:
            best_format = max(
                supported_formats,
                key=lambda f: f.video_format.width * f.video_format.height
            )
            await frame_source.set_format_async(best_format)
            self._frame_width = best_format.video_format.width
            self._frame_height = best_format.video_format.height
        
        # 创建帧读取器
        self._frame_reader = await self._media_capture.create_frame_reader_async(frame_source)
        self._frame_reader.acquisition_mode = MediaFrameReaderAcquisitionMode.REALTIME
        self._frame_reader.add_frame_arrived(self._on_frame_arrived)
        
        return True

    # ==================== 捕获控制 ====================

    async def start(self) -> bool:
        """开始捕获"""
        if self._frame_reader is None:
            return False
        
        self._running = True
        await self._frame_reader.start_async()
        return True

    async def stop(self):
        """停止捕获"""
        self._running = False
        
        if self._is_recording:
            self.stop_recording()
        
        if self._frame_reader is not None:
            await self._frame_reader.stop_async()
            self._frame_reader = None
        
        if self._media_capture is not None:
            self._media_capture = None

    async def pause(self):
        """暂停捕获（不关闭程序）"""
        if self._frame_reader is not None:
            await self._frame_reader.stop_async()

    async def resume(self):
        """恢复捕获"""
        if self._frame_reader is not None:
            await self._frame_reader.start_async()

    def get_frame(self):
        """获取最新帧"""
        try:
            return self._frame_queue.get_nowait()
        except Empty:
            return self._last_frame

    # ==================== 帧处理 ====================

    def _on_frame_arrived(self, reader, args):
        """帧到达回调"""
        if not self._running:
            return
            
        with self._lock:
            try:
                self._process_frame(reader)
            except Exception:
                pass

    def _process_frame(self, reader):
        """处理帧数据"""
        media_frame = reader.try_acquire_latest_frame()
        if media_frame is None:
            return
        
        try:
            video_frame = media_frame.video_media_frame
            if video_frame is None:
                return
            
            # 检查照明状态
            self._check_illumination(video_frame)
            
            # 应用帧过滤
            if not self._should_display_frame():
                return
            
            # 处理位图
            bitmap = video_frame.software_bitmap
            if bitmap is not None:
                frame = self._convert_bitmap_to_frame(bitmap)
                if frame is not None:
                    self._update_frame(frame)
        finally:
            media_frame.close()

    def _check_illumination(self, video_frame):
        """检查帧是否为照明帧"""
        try:
            ir_frame = video_frame.infrared_media_frame
            if ir_frame is not None:
                self._is_illuminated = ir_frame.is_illuminated
        except:
            self._is_illuminated = False

    def _should_display_frame(self) -> bool:
        """根据过滤器判断是否显示当前帧"""
        if self._frame_filter == IRFrameFilter.NONE:
            return True
        if self._frame_filter == IRFrameFilter.RAW:
            return not self._is_illuminated
        if self._frame_filter == IRFrameFilter.ILLUMINATED:
            return self._is_illuminated
        return True

    def _convert_bitmap_to_frame(self, bitmap):
        """将 SoftwareBitmap 转换为 numpy 数组"""
        try:
            converted = SoftwareBitmap.convert(bitmap, BitmapPixelFormat.BGRA8)
            buffer = converted.lock_buffer(BitmapBufferAccessMode.READ)
            reference = buffer.create_reference()
            
            data = bytes(reference)
            frame = np.frombuffer(data, dtype=np.uint8).copy()
            frame = frame.reshape((converted.pixel_height, converted.pixel_width, 4))
            
            buffer.close()
            converted.close()
            bitmap.close()
            
            return frame
        except:
            return None

    def _update_frame(self, frame):
        """更新帧队列"""
        # 应用颜色映射
        frame = self._apply_color_mapping(frame)
        
        # 保存最后一帧
        self._last_frame = frame.copy()
        
        # 录像
        if self._is_recording and self._video_writer is not None:
            record_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            self._video_writer.write(record_frame)
        
        # 更新队列
        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except Empty:
                break
        
        try:
            self._frame_queue.put_nowait(frame)
        except:
            pass

    def _apply_color_mapping(self, frame):
        """应用颜色映射"""
        if self._mapping_mode == IRMappingMode.NONE:
            return frame
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
        
        if self._mapping_mode == IRMappingMode.GREEN:
            result = np.zeros_like(frame)
            result[:, :, 1] = gray  # 绿色通道
            result[:, :, 3] = 255   # Alpha
            return result
        
        elif self._mapping_mode == IRMappingMode.HEAT:
            colored = cv2.applyColorMap(gray, cv2.COLORMAP_HOT)
            return cv2.cvtColor(colored, cv2.COLOR_BGR2BGRA)
        
        elif self._mapping_mode == IRMappingMode.JET:
            colored = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
            return cv2.cvtColor(colored, cv2.COLOR_BGR2BGRA)
        
        return frame

    # ==================== 拍照和录像 ====================

    def take_photo(self, save_dir: str = "photos") -> str:
        """拍照保存，返回文件路径"""
        if self._last_frame is None:
            return None
        
        os.makedirs(save_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(save_dir, f"IR_Photo_{timestamp}.jpg")
        
        save_frame = cv2.cvtColor(self._last_frame, cv2.COLOR_BGRA2BGR)
        cv2.imwrite(filepath, save_frame)
        
        return filepath

    def start_recording(self, save_dir: str = "videos", base_fps: int = 15) -> str:
        """开始录像，返回文件路径
        
        Args:
            save_dir: 保存目录
            base_fps: 基础帧率，默认 15fps（红外摄像头无过滤时的帧率）
                      当使用 RAW 或 ILLUMINATED 过滤时，帧率自动减半
        """
        if self._is_recording:
            return None
        
        os.makedirs(save_dir, exist_ok=True)
        
        # 根据帧过滤模式调整帧率
        # RAW 或 ILLUMINATED 模式下只保存一半的帧，所以帧率减半
        if self._frame_filter == IRFrameFilter.NONE:
            actual_fps = base_fps
        else:
            actual_fps = max(base_fps // 2, 7)  # 最低 7fps，避免太慢
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filter_suffix = self._frame_filter.display_name
        self._video_path = os.path.join(save_dir, f"IR_Video_{timestamp}_{filter_suffix}.avi")
        
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self._video_writer = cv2.VideoWriter(
            self._video_path, fourcc, actual_fps,
            (self._frame_width, self._frame_height)
        )
        
        self._is_recording = True
        return self._video_path

    def stop_recording(self) -> str:
        """停止录像，返回文件路径"""
        if not self._is_recording:
            return None
        
        self._is_recording = False
        
        if self._video_writer is not None:
            self._video_writer.release()
            self._video_writer = None
        
        path = self._video_path
        self._video_path = None
        return path
