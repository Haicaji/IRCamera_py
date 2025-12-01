# IR Camera Viewer - 红外摄像头查看器

使用 Windows Media Foundation API 访问红外摄像头的 Python GUI 应用。

## 功能

- **实时预览**: 显示红外摄像头画面
- **多设备支持**: 自动检测并可切换多个红外摄像头
- **帧过滤**: 区分照明帧和非照明帧，消除闪烁
- **颜色映射**: 灰度、绿色、热力图、Jet 等多种显示模式
- **拍照**: 保存当前帧为 JPG 图片
- **录像**: 录制视频并保存为 AVI 格式

## 项目结构

```
python_demo/
├── main.py              # 主程序入口
├── camera_controller.py # 摄像头控制器
├── gui_components.py    # GUI 组件
├── constants.py         # 常量和枚举定义
├── requirements.txt     # 依赖清单
└── README.md
```

## 环境要求

- Windows 10/11
- Python 3.9+
- 兼容的红外摄像头 (如 Windows Hello 摄像头)

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 界面操作

所有操作通过鼠标点击按钮完成：

| 按钮 | 功能 |
|------|------|
| **Photo** | 拍照保存到 `photos/` 目录 |
| **Record** | 开始/停止录像，保存到 `videos/` 目录 |
| **Filter** | 切换帧过滤 (OFF → RAW → ILLUM) |
| **Color** | 切换颜色映射 (OFF → GREEN → HEAT → JET) |
| **Device** | 切换设备（多设备时显示）|
| **Exit** | 退出程序 |

## 帧过滤说明

红外摄像头通常会交替发送两种帧：

| 模式 | 说明 |
|------|------|
| **OFF** | 显示所有帧（可能看到亮度交替） |
| **RAW** | 仅显示原始帧（LED 关闭时捕获） |
| **ILLUM** | 仅显示照明帧（LED 开启时捕获） |

使用 RAW 或 ILLUM 模式可以消除画面闪烁。

## 潜在问题

由于红外摄像头的帧数不同, 录制出的视频可能存在速度不一致问题

## 参考项目

- [ir_camera_sample_win32](https://github.com/andresbeltranc/ir_camera_sample_win32) - C++ 原版
- [IRCameraView](https://github.com/Iemand005/IRCameraView) - C# WinUI 版本
