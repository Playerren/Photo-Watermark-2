# 图片水印工具

这是一个基于MacOS的图片水印本地应用程序，可以方便地为图片添加自定义水印。

## 快速开始（推荐）

最简单的使用方式是直接下载打包好的应用程序：

1. 访问 [GitHub Release页面](https://github.com/Playerren/Photo-Watermark-2/releases/latest)
2. 下载最新版本的 `图片水印工具.app.zip` 文件
3. 解压下载的文件
4. 将 `图片水印工具.app` 拖动到您的应用程序文件夹中
5. 双击打开应用程序即可开始使用

## 功能特点

### 文件处理
- **导入图片**：
  - 支持单张图片拖拽或通过文件选择器导入
  - 支持批量导入，可一次性选择多张图片或直接导入整个文件夹
  - 在界面上显示已导入图片的列表（缩略图和文件名）

- **支持格式**：
  - 输入格式：支持 JPEG, PNG, BMP, TIFF 等主流图片格式
  - PNG格式支持透明通道
  - 输出格式：用户可选择输出为 JPEG 或 PNG

- **导出图片**：
  - 用户可指定一个输出文件夹
  - 为防止覆盖原图，默认禁止导出到原文件夹
  - 提供导出文件命名规则选项：
    - 保留原文件名
    - 添加自定义前缀（如 wm_）
    - 添加自定义后缀（如 _watermarked）

### 水印设置
- 支持自定义水印文本或使用图片拍摄日期作为水印
- 可调整字体大小
- 可选择水印位置（左上角、右上角、左下角、右下角、中心）
- 可设置水印颜色（支持预定义颜色和HEX颜色代码）
- 可调整水印透明度

## 安装说明

1. 确保您的系统已安装Python 3.6或更高版本

2. 安装依赖包：

```bash
cd Photo-Watermark-2
pip install -r requirements.txt
```

3. 运行应用程序：

```bash
python watermark_app.py
```

## 使用方法

### 图形界面模式

1. **导入图片**：
   - 点击"导入图片"按钮选择单个或多个图片文件
   - 点击"导入文件夹"按钮选择包含图片的文件夹
   - 直接拖拽图片或文件夹到应用窗口中

2. **设置水印**：
   - 在"水印设置"区域输入水印文本，或勾选"使用拍摄日期作为水印"
   - 选择合适的字体大小、水印位置、颜色和透明度

3. **设置导出选项**：
   - 点击"浏览"按钮选择输出文件夹
   - 选择输出格式（JPEG或PNG）
   - 选择命名规则（保留原文件名、添加前缀或添加后缀）

4. **应用水印并导出**：
   - 点击"应用水印"或"导出图片"按钮开始处理
   - 等待处理完成，查看处理结果提示

### 命令行模式

该工具也支持在命令行模式下运行，方便批量处理图片：

```bash
python watermark_app.py <图片路径> [选项]
```

可用选项：
- `--font-size`：水印字体大小（默认：30）
- `--color`：水印颜色，可以是预定义颜色或HEX代码（默认：white）
- `--opacity`：水印透明度（0-100，默认：80）
- `--position`：水印位置（可选值：top_left, top_right, bottom_left, bottom_right, center，默认：bottom_right）
- `--output-dir`：输出文件夹路径
- `--text`：水印文本
- `--use-date`：使用拍摄日期作为水印

命令行示例：

```bash
# 使用默认设置为单张图片添加水印
python watermark_app.py /path/to/image.jpg

# 为整个文件夹的图片添加自定义水印
python watermark_app.py /path/to/folder --text "我的水印" --color red --position center --output-dir /path/to/output

# 使用拍摄日期作为水印
python watermark_app.py /path/to/image.jpg --use-date --font-size 40
```

## 注意事项

- 为防止意外覆盖原图，应用默认禁止将图片导出到原文件夹
- 对于没有EXIF信息的图片，使用拍摄日期作为水印时将显示文件修改日期
- 在处理大量图片时，可能需要一些时间，请耐心等待

## 系统要求

- 操作系统：MacOS
- Python 版本：3.6或更高
- 必要依赖：Pillow、piexif、PyQt5、matplotlib

## 许可证

[MIT License](LICENSE)