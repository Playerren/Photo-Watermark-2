#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import json
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ExifTags
import piexif
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFileDialog, QListWidget, QListWidgetItem, 
    QComboBox, QLineEdit, QCheckBox, QGroupBox, QGridLayout, QFrame,
    QSplitter, QMessageBox, QProgressDialog, QColorDialog, QSlider,
    QMenu, QAction, QMenuBar, QInputDialog, QFormLayout
)
from PyQt5.QtGui import QPixmap, QIcon, QDragEnterEvent, QDropEvent, QColor, QImage, QPainter
from PyQt5.QtCore import Qt, QSize, QUrl, QPoint, QRect

# 确保中文显示正常
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]

class WatermarkApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 支持的图片格式
        self.supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']
        
        # 存储图片路径
        self.image_paths = []
        
        # 当前选中的图片索引
        self.current_image_index = -1
        
        # 水印位置和旋转相关变量
        self.watermark_pos = None  # 手动拖拽的水印位置
        self.watermark_rotation = 0  # 水印旋转角度
        self.dragging = False  # 拖拽状态标志
        self.drag_start_pos = None  # 拖拽开始位置
        
        # 模板相关变量
        self.templates = []
        
        # 创建UI
        self.initUI()
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 加载模板和上次的设置
        self.load_templates()
        self.load_last_settings()
        
        # 启用拖放功能
        self.setAcceptDrops(True)
        
    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('图片水印工具')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧面板：图片列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMinimumWidth(200)
        
        # 顶部按钮布局
        top_layout = QHBoxLayout()
        
        # 添加导入按钮
        self.import_btn = QPushButton('导入图片')
        self.import_btn.clicked.connect(self.import_images)
        top_layout.addWidget(self.import_btn)
        
        # 添加导入文件夹按钮
        self.import_folder_btn = QPushButton('导入文件夹')
        self.import_folder_btn.clicked.connect(self.import_folder)
        top_layout.addWidget(self.import_folder_btn)
        
        left_layout.addLayout(top_layout)
        
        # 创建图片列表
        self.image_list = QListWidget()
        self.image_list.setViewMode(QListWidget.IconMode)
        self.image_list.setIconSize(QSize(120, 120))
        self.image_list.setResizeMode(QListWidget.Adjust)
        self.image_list.setMovement(QListWidget.Static)
        self.image_list.itemClicked.connect(self.on_image_item_clicked)
        
        # 设置拖放功能
        self.image_list.setAcceptDrops(True)
        self.setAcceptDrops(True)
        
        left_layout.addWidget(self.image_list)
        
        # 添加清空按钮
        self.clear_btn = QPushButton('清空列表')
        self.clear_btn.clicked.connect(self.clear_list)
        left_layout.addWidget(self.clear_btn)
        
        # 中间面板：图片预览
        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        middle_panel.setMinimumWidth(600)
        
        # 预览标签
        self.preview_label = QLabel("图片预览")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        self.preview_label.mousePressEvent = self.on_preview_mouse_press
        self.preview_label.mouseMoveEvent = self.on_preview_mouse_move
        self.preview_label.mouseReleaseEvent = self.on_preview_mouse_release
        
        middle_layout.addWidget(self.preview_label)
        
        # 水印旋转控制
        rotate_layout = QHBoxLayout()
        rotate_layout.addWidget(QLabel("水印旋转:"))
        self.rotate_slider = QSlider(Qt.Horizontal)
        self.rotate_slider.setRange(-180, 180)
        self.rotate_slider.setValue(0)
        self.rotate_slider.setTickInterval(15)
        self.rotate_slider.setTickPosition(QSlider.TicksBelow)
        self.rotate_slider.valueChanged.connect(self.on_rotate_value_changed)
        rotate_layout.addWidget(self.rotate_slider)
        self.rotate_value = QLabel("0°")
        rotate_layout.addWidget(self.rotate_value)
        middle_layout.addLayout(rotate_layout)
        
        # 右侧面板：设置
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setMinimumWidth(350)
        
        # 创建水印设置面板
        watermark_group = QGroupBox("水印设置")
        watermark_layout = QFormLayout()
        
        # 水印文本输入
        self.watermark_text = QLineEdit("水印")
        self.watermark_text.textChanged.connect(self.update_preview)
        watermark_layout.addRow("水印文本:", self.watermark_text)
        
        # 使用日期作为水印
        self.use_date_checkbox = QCheckBox()
        self.use_date_checkbox.stateChanged.connect(self.toggle_watermark_text)
        self.use_date_checkbox.stateChanged.connect(self.update_preview)
        watermark_layout.addRow("使用拍摄日期:", self.use_date_checkbox)
        
        # 字体大小选择
        self.font_size = QComboBox()
        self.font_size.addItems([str(i) for i in range(10, 101, 5)])
        self.font_size.setCurrentText("30")
        self.font_size.currentTextChanged.connect(self.update_preview)
        watermark_layout.addRow("字体大小:", self.font_size)
        
        # 位置选择
        self.position = QComboBox()
        self.position.addItem("左上角", "top_left")
        self.position.addItem("顶部居中", "top_center")
        self.position.addItem("右上角", "top_right")
        self.position.addItem("左侧居中", "left_center")
        self.position.addItem("居中", "center")
        self.position.addItem("右侧居中", "right_center")
        self.position.addItem("左下角", "bottom_left")
        self.position.addItem("底部居中", "bottom_center")
        self.position.addItem("右下角", "bottom_right")
        self.position.setCurrentIndex(8)  # 默认右下角
        self.position.currentIndexChanged.connect(self.on_position_changed)
        watermark_layout.addRow("位置:", self.position)
        
        # 颜色选择
        color_layout = QHBoxLayout()
        self.color = QLineEdit("#FFFFFF")
        self.color.textChanged.connect(self.update_preview)
        color_layout.addWidget(self.color)
        self.color_picker = QPushButton("选择")
        self.color_picker.clicked.connect(self.pick_color)
        color_layout.addWidget(self.color_picker)
        watermark_layout.addRow("颜色:", color_layout)
        
        # 透明度选择
        self.opacity = QComboBox()
        self.opacity.addItems([f"{i}%" for i in range(10, 101, 10)])
        self.opacity.setCurrentText("80%")
        self.opacity.currentTextChanged.connect(self.update_preview)
        watermark_layout.addRow("透明度:", self.opacity)
        
        # 旋转角度控制
        rotate_layout = QHBoxLayout()
        self.rotate_slider = QSlider(Qt.Horizontal)
        self.rotate_slider.setRange(-180, 180)
        self.rotate_slider.setValue(0)
        self.rotate_slider.valueChanged.connect(self.on_rotate_value_changed)
        rotate_layout.addWidget(self.rotate_slider)
        self.rotate_value = QLabel("0°")
        rotate_layout.addWidget(self.rotate_value)
        watermark_layout.addRow("旋转角度:", rotate_layout)
        
        watermark_group.setLayout(watermark_layout)
        right_layout.addWidget(watermark_group)
        
        # 导出设置组
        export_group = QGroupBox("导出设置")
        export_layout = QGridLayout()
        
        # 输出文件夹
        export_layout.addWidget(QLabel("输出文件夹:"), 0, 0)
        self.output_dir = QLineEdit()
        self.output_dir.setReadOnly(True)
        export_layout.addWidget(self.output_dir, 0, 1)
        self.browse_btn = QPushButton('浏览')
        self.browse_btn.clicked.connect(self.browse_output_dir)
        export_layout.addWidget(self.browse_btn, 0, 2)
        
        # 输出格式
        export_layout.addWidget(QLabel("输出格式:"), 1, 0)
        self.output_format = QComboBox()
        self.output_format.addItems(['JPEG (*.jpg)', 'PNG (*.png)'])
        export_layout.addWidget(self.output_format, 1, 1)
        
        # 命名规则
        export_layout.addWidget(QLabel("命名规则:"), 2, 0)
        
        # 保留原文件名
        self.keep_original_name = QRadioButton("保留原文件名")
        self.keep_original_name.setChecked(True)
        export_layout.addWidget(self.keep_original_name, 2, 1)
        
        # 添加前缀
        self.add_prefix = QRadioButton("添加前缀:")
        export_layout.addWidget(self.add_prefix, 3, 0)
        self.prefix_text = QLineEdit("wm_")
        self.prefix_text.setEnabled(False)
        self.add_prefix.toggled.connect(self.prefix_text.setEnabled)
        export_layout.addWidget(self.prefix_text, 3, 1)
        
        # 添加后缀
        self.add_suffix = QRadioButton("添加后缀:")
        export_layout.addWidget(self.add_suffix, 4, 0)
        self.suffix_text = QLineEdit("_watermarked")
        self.suffix_text.setEnabled(False)
        self.add_suffix.toggled.connect(self.suffix_text.setEnabled)
        export_layout.addWidget(self.suffix_text, 4, 1)
        
        export_group.setLayout(export_layout)
        right_layout.addWidget(export_group)
        
        # 添加应用水印按钮
        self.apply_btn = QPushButton('应用水印')
        self.apply_btn.clicked.connect(self.apply_watermark)
        self.apply_btn.setEnabled(False)
        right_layout.addWidget(self.apply_btn)
        
        # 添加导出按钮
        self.export_btn = QPushButton('导出图片')
        self.export_btn.clicked.connect(self.export_images)
        self.export_btn.setEnabled(False)
        right_layout.addWidget(self.export_btn)
        
        # 创建预览区
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel("请添加图片以预览水印效果")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        
        # 设置鼠标跟踪和事件过滤器
        self.preview_label.setMouseTracking(True)
        self.preview_label.mousePressEvent = self.on_preview_mouse_press
        self.preview_label.mouseMoveEvent = self.on_preview_mouse_move
        self.preview_label.mouseReleaseEvent = self.on_preview_mouse_release
        
        preview_layout.addWidget(self.preview_label)
        preview_group.setLayout(preview_layout)
        
        # 添加到主布局
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(preview_group, 2)
        main_layout.addWidget(right_panel, 1)
        
        # 状态栏
        self.statusBar().showMessage('就绪')
        
    def toggle_watermark_text(self, state):
        if state == Qt.Checked:
            self.watermark_text.setEnabled(False)
            if self.current_image_index >= 0:
                self.update_watermark_text()
        else:
            self.watermark_text.setEnabled(True)
        self.update_preview()
    
    def update_watermark_text(self):
        if self.current_image_index >= 0 and self.current_image_index < len(self.image_paths):
            current_image_path = self.image_paths[self.current_image_index]
            date = self.get_image_creation_date(current_image_path)
            # 注意：我们不直接修改watermark_text的值，而是在update_preview中处理日期显示
            pass
        
    def import_images(self):
        options = QFileDialog.Options()
        file_types = "图片文件 (" + " ".join([f"*{ext}" for ext in self.supported_formats]) + ")"
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "", file_types, options=options
        )
        
        if files:
            self.add_images(files)
            
    def import_folder(self):
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(
            self, "选择文件夹", "", options=options
        )
        
        if folder:
            files = []
            for root, _, filenames in os.walk(folder):
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in self.supported_formats:
                        files.append(os.path.join(root, filename))
            
            if files:
                self.add_images(files)
            else:
                QMessageBox.information(self, "提示", "所选文件夹中没有支持的图片文件")
                
    def add_images(self, file_paths):
        # 检查文件是否已经存在
        new_files = [f for f in file_paths if f not in self.image_paths]
        
        if new_files:
            # 添加新文件
            self.image_paths.extend(new_files)
            
            # 更新列表视图
            for file_path in new_files:
                self.add_image_to_list(file_path)
                # 连接点击事件
                self.image_list.itemClicked.connect(self.on_image_item_clicked)
            
            # 如果是第一次添加图片，选中第一张
            if len(self.image_paths) == len(new_files):
                self.image_list.setCurrentRow(0)
                self.current_image_index = 0
                self.update_preview()
        
        # 更新按钮状态
        self.update_button_states()
        self.statusBar().showMessage(f'已导入 {len(self.image_paths)} 张图片')
        
    def add_image_to_list(self, file_path):
        try:
            # 创建列表项
            item = QListWidgetItem()
            
            # 获取图片缩略图
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # 设置图标和文本
            item.setIcon(QIcon(scaled_pixmap))
            item.setText(os.path.basename(file_path))
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            item.setSizeHint(QSize(140, 160))
            
            # 添加到列表
            self.image_list.addItem(item)
        except Exception as e:
            print(f"添加图片失败: {e}")
            
    def clear_list(self):
        self.image_list.clear()
        self.image_paths = []
        self.update_button_states()
        self.statusBar().showMessage('列表已清空')
        
    def update_button_states(self):
        has_images = len(self.image_paths) > 0
        self.export_btn.setEnabled(has_images)
        self.apply_btn.setEnabled(has_images)
        
    def browse_output_dir(self):
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(
            self, "选择输出文件夹", "", options=options
        )
        
        if folder:
            # 检查是否与输入文件夹相同
            for img_path in self.image_paths:
                if os.path.dirname(img_path) == folder:
                    QMessageBox.warning(self, "警告", "禁止导出到原图片所在文件夹，以防止覆盖原图")
                    return
            
            self.output_dir.setText(folder)
            
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def create_menu_bar(self):
        # 创建菜单栏
        menu_bar = self.menuBar()
        
        # 创建模板菜单
        template_menu = menu_bar.addMenu("模板")
        
        # 保存模板动作
        save_template_action = QAction("保存当前设置为模板", self)
        save_template_action.triggered.connect(self.save_template)
        template_menu.addAction(save_template_action)
        
        # 加载模板动作
        load_template_action = QAction("加载模板", self)
        load_template_action.triggered.connect(self.load_template)
        template_menu.addAction(load_template_action)
        
        # 删除模板动作
        delete_template_action = QAction("删除模板", self)
        delete_template_action.triggered.connect(self.delete_template)
        template_menu.addAction(delete_template_action)
    
    def on_image_item_clicked(self, item):
        # 获取选中图片的索引
        self.current_image_index = self.image_list.row(item)
        # 更新预览
        self.update_preview()
    
    def update_preview(self):
        # 检查是否有选中的图片
        if self.current_image_index < 0 or self.current_image_index >= len(self.image_paths):
            return
        
        try:
            # 获取当前图片路径
            image_path = self.image_paths[self.current_image_index]
            
            # 打开图片
            img = Image.open(image_path)
            
            # 深拷贝图片以便不修改原图
            preview_img = img.copy()
            
            # 获取水印文本
            if self.use_date_checkbox.isChecked():
                watermark_text = self.get_image_creation_date(image_path)
            else:
                watermark_text = self.watermark_text.text()
                if not watermark_text:  # 如果文本为空，不添加水印
                    watermark_text = "水印"
            
            # 获取水印设置
            font_size = int(self.font_size.currentText())
            position = self.position.currentData()
            
            # 解析颜色和透明度
            color_str = self.color.text()
            opacity = int(self.opacity.currentText().rstrip('%'))
            color = self.parse_color(color_str, opacity)
            
            # 在预览图上添加水印
            self.draw_watermark_on_preview(preview_img, watermark_text, font_size, color, position)
            
            try:
                # 直接使用QImage转换，避免依赖ImageQt
                width, height = preview_img.size
                
                # 确保图像是RGB模式
                if preview_img.mode != 'RGB':
                    preview_img = preview_img.convert('RGB')
                
                # 转换PIL图像到QImage
                data = preview_img.tobytes('raw', 'RGB')
                q_image = QImage(data, width, height, 3 * width, QImage.Format_RGB888)
                qpixmap = QPixmap.fromImage(q_image)
                
                # 显示缩放后的图像
                scaled_pixmap = qpixmap.scaled(
                    self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
            except Exception as e:
                print(f"更新预览失败: {str(e)}")
            
        except Exception as e:
            print(f"更新预览失败: {e}")
    
    def draw_watermark_on_preview(self, img, text, font_size, color, position):
        # 创建绘图对象
        draw = ImageDraw.Draw(img)
        
        # 尝试加载系统字体，如果失败则使用默认字体
        try:
            font = ImageFont.truetype("Arial.ttf", font_size)
        except IOError:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", font_size)
            except IOError:
                font = ImageFont.load_default()
        
        # 获取文本大小 (使用textbbox替代textsize)
        try:
            # 对于Pillow 9.0.0及以上版本，使用textbbox
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            # 对于旧版本的Pillow，回退到textsize
            text_width, text_height = draw.textsize(text, font=font)
        
        # 确定水印位置
        img_width, img_height = img.size
        
        if self.watermark_pos:
            # 使用手动拖拽的位置
            x, y = self.watermark_pos
        else:
            # 使用预设位置
            if position == 'top_left':
                x, y = 10, 10
            elif position == 'top_center':
                x, y = (img_width - text_width) // 2, 10
            elif position == 'top_right':
                x, y = img_width - text_width - 10, 10
            elif position == 'left_center':
                x, y = 10, (img_height - text_height) // 2
            elif position == 'center':
                x, y = (img_width - text_width) // 2, (img_height - text_height) // 2
            elif position == 'right_center':
                x, y = img_width - text_width - 10, (img_height - text_height) // 2
            elif position == 'bottom_left':
                x, y = 10, img_height - text_height - 10
            elif position == 'bottom_center':
                x, y = (img_width - text_width) // 2, img_height - text_height - 10
            elif position == 'bottom_right':
                x, y = img_width - text_width - 10, img_height - text_height - 10
            else:
                # 默认位置为右下角
                x, y = img_width - text_width - 10, img_height - text_height - 10
        
        # 如果有旋转角度，创建一个新的图像用于旋转
        if self.watermark_rotation != 0:
            # 创建一个透明的新图像来绘制旋转的文本
            txt_img = Image.new('RGBA', (text_width + 20, text_height + 20), (255, 255, 255, 0))
            txt_draw = ImageDraw.Draw(txt_img)
            
            # 绘制文本和阴影到临时图像
            txt_draw.text((10, 10), text, font=font, fill=color)
            txt_draw.text((11, 11), text, font=font, fill=(0, 0, 0, 128))  # 阴影
            
            # 旋转文本图像
            rotated_txt = txt_img.rotate(self.watermark_rotation, expand=True)
            
            # 计算旋转后的位置
            rot_width, rot_height = rotated_txt.size
            rot_x = x - (rot_width - text_width) // 2
            rot_y = y - (rot_height - text_height) // 2
            
            # 粘贴旋转后的文本到原图
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img.paste(rotated_txt, (rot_x, rot_y), rotated_txt)
        else:
            # 直接绘制水印（添加阴影效果增强可读性）
            draw.text((x+1, y+1), text, font=font, fill=(0, 0, 0, 128))  # 阴影
            draw.text((x, y), text, font=font, fill=color)
    
    def on_position_changed(self):
        # 当位置选择变更时，重置手动拖拽的位置
        self.watermark_pos = None
        self.update_preview()
    
    def on_rotate_value_changed(self, value):
        # 更新旋转角度
        self.watermark_rotation = value
        self.rotate_value.setText(f"{value}°")
        self.update_preview()
    
    def on_preview_mouse_press(self, event):
        # 检查是否有选中的图片
        if self.current_image_index < 0 or self.current_image_index >= len(self.image_paths):
            return
        
        # 记录拖动开始的位置
        self.dragging = True
        self.drag_start_pos = event.pos()
    
    def on_preview_mouse_move(self, event):
        # 检查是否在拖动状态
        if not self.dragging:
            return
        
        # 更新预览
        self.update_preview()
    
    def on_preview_mouse_release(self, event):
        # 检查是否在拖动状态
        if not self.dragging:
            return
        
        # 停止拖动
        self.dragging = False
        
        # 获取当前图片路径
        image_path = self.image_paths[self.current_image_index]
        
        # 打开图片获取原始尺寸
        img = Image.open(image_path)
        img_width, img_height = img.size
        
        # 获取标签尺寸
        label_width = self.preview_label.width()
        label_height = self.preview_label.height()
        
        # 计算缩放比例
        scale_x = img_width / label_width
        scale_y = img_height / label_height
        
        # 选择较小的缩放比例以保持宽高比
        scale = min(scale_x, scale_y)
        
        # 计算点击位置相对于图片的实际坐标
        click_x = event.pos().x() * scale
        click_y = event.pos().y() * scale
        
        # 保存手动拖拽的位置
        self.watermark_pos = (int(click_x), int(click_y))
        
        # 更新预览
        self.update_preview()
    
    def save_template(self):
        # 弹出对话框输入模板名称
        template_name, ok = QInputDialog.getText(self, "保存模板", "请输入模板名称:")
        
        if ok and template_name:
            # 创建模板数据
            template = {
                'name': template_name,
                'text': self.watermark_text.text(),
                'use_date': self.use_date_checkbox.isChecked(),
                'font_size': self.font_size.currentText(),
                'position': self.position.currentIndex(),
                'color': self.color.text(),
                'opacity': self.opacity.currentText(),
                'rotation': self.watermark_rotation
            }
            
            # 添加到模板列表
            self.templates.append(template)
            
            # 保存模板到文件
            self.save_templates()
            
            QMessageBox.information(self, "成功", f"模板 '{template_name}' 已保存")
    
    def load_template(self):
        # 检查是否有模板
        if not self.templates:
            QMessageBox.information(self, "提示", "没有可加载的模板")
            return
        
        # 创建模板名称列表
        template_names = [template['name'] for template in self.templates]
        
        # 弹出对话框选择模板
        template_name, ok = QInputDialog.getItem(self, "加载模板", "请选择要加载的模板:", template_names, 0, False)
        
        if ok:
            # 查找选中的模板
            for template in self.templates:
                if template['name'] == template_name:
                    # 应用模板设置
                    self.watermark_text.setText(template['text'])
                    self.use_date_checkbox.setChecked(template['use_date'])
                    self.font_size.setCurrentText(template['font_size'])
                    self.position.setCurrentIndex(template['position'])
                    self.color.setText(template['color'])
                    self.opacity.setCurrentText(template['opacity'])
                    self.rotate_slider.setValue(template['rotation'])
                    self.watermark_rotation = template['rotation']
                    self.rotate_value.setText(f"{template['rotation']}°")
                    
                    # 重置手动位置
                    self.watermark_pos = None
                    
                    # 更新预览
                    self.update_preview()
                    
                    QMessageBox.information(self, "成功", f"模板 '{template_name}' 已加载")
                    break
    
    def delete_template(self):
        # 检查是否有模板
        if not self.templates:
            QMessageBox.information(self, "提示", "没有可删除的模板")
            return
        
        # 创建模板名称列表
        template_names = [template['name'] for template in self.templates]
        
        # 弹出对话框选择模板
        template_name, ok = QInputDialog.getItem(self, "删除模板", "请选择要删除的模板:", template_names, 0, False)
        
        if ok:
            # 查找并删除选中的模板
            for i, template in enumerate(self.templates):
                if template['name'] == template_name:
                    del self.templates[i]
                    
                    # 保存更新后的模板列表
                    self.save_templates()
                    
                    QMessageBox.information(self, "成功", f"模板 '{template_name}' 已删除")
                    break
    
    def save_templates(self):
        # 保存模板到文件
        try:
            template_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates.json')
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存模板失败: {e}")
    
    def load_templates(self):
        # 从文件加载模板
        try:
            template_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates.json')
            if os.path.exists(template_file):
                with open(template_file, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
        except Exception as e:
            print(f"加载模板失败: {e}")
            self.templates = []
    
    def save_last_settings(self):
        # 保存最后一次的设置
        try:
            settings = {
                'text': self.watermark_text.text(),
                'use_date': self.use_date_checkbox.isChecked(),
                'font_size': self.font_size.currentText(),
                'position': self.position.currentIndex(),
                'color': self.color.text(),
                'opacity': self.opacity.currentText(),
                'rotation': self.watermark_rotation
            }
            
            settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'last_settings.json')
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def load_last_settings(self):
        # 加载最后一次的设置
        try:
            settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'last_settings.json')
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                    # 应用设置
                    self.watermark_text.setText(settings.get('text', '水印'))
                    self.use_date_checkbox.setChecked(settings.get('use_date', False))
                    self.font_size.setCurrentText(settings.get('font_size', '30'))
                    self.position.setCurrentIndex(settings.get('position', 8))
                    self.color.setText(settings.get('color', '#FFFFFF'))
                    self.opacity.setCurrentText(settings.get('opacity', '80%'))
                    self.rotate_slider.setValue(settings.get('rotation', 0))
                    self.watermark_rotation = settings.get('rotation', 0)
                    self.rotate_value.setText(f"{settings.get('rotation', 0)}°")
        except Exception as e:
            print(f"加载设置失败: {e}")
    
    def pick_color(self):
        # 获取当前颜色
        current_color = QColor(self.color.text())
        
        # 打开颜色选择对话框
        color = QColorDialog.getColor(current_color, self, "选择水印颜色")
        
        if color.isValid():
            # 更新颜色输入框
            self.color.setText(color.name())
    
    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        
        if files:
            valid_files = []
            for file_path in files:
                if os.path.isdir(file_path):
                    # 处理文件夹
                    for root, _, filenames in os.walk(file_path):
                        for filename in filenames:
                            ext = os.path.splitext(filename)[1].lower()
                            if ext in self.supported_formats:
                                valid_files.append(os.path.join(root, filename))
                else:
                    # 处理单个文件
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in self.supported_formats:
                        valid_files.append(file_path)
            
            if valid_files:
                self.add_images(valid_files)
                
    def apply_watermark(self):
        # 检查输出文件夹是否设置
        if not self.output_dir.text():
            QMessageBox.warning(self, "警告", "请先设置输出文件夹")
            return
        
        # 创建进度对话框
        progress = QProgressDialog("正在处理图片...", "取消", 0, len(self.image_paths), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        
        success_count = 0
        
        for i, image_path in enumerate(self.image_paths):
            if progress.wasCanceled():
                break
            
            try:
                # 获取水印文本
                if self.use_date_checkbox.isChecked():
                    watermark_text = self.get_image_creation_date(image_path)
                else:
                    watermark_text = self.watermark_text.text()
                
                # 获取水印设置
                font_size = int(self.font_size.currentText())
                position = self.position.currentData()
                
                # 解析颜色和透明度
                color_str = self.color.text()
                opacity = int(self.opacity.currentText().rstrip('%'))
                color = self.parse_color(color_str, opacity)
                
                # 创建输出文件路径
                output_path = self.get_output_path(image_path)
                
                # 添加水印
                if self.add_watermark(image_path, output_path, watermark_text, font_size, color, position):
                    success_count += 1
                
            except Exception as e:
                print(f"处理图片失败: {e}")
            
            progress.setValue(i + 1)
            
        progress.close()
        
        QMessageBox.information(
            self, "完成", f"处理完成！成功添加水印 {success_count} 张图片，失败 {len(self.image_paths) - success_count} 张图片"
        )
        
    def get_output_path(self, image_path):
        # 获取基本信息
        base_name = os.path.basename(image_path)
        name_without_ext, ext = os.path.splitext(base_name)
        
        # 获取输出格式
        output_format = self.output_format.currentText().split('.')[-1].lower()
        
        # 应用命名规则
        if self.keep_original_name.isChecked():
            new_name = f"{name_without_ext}.{output_format}"
        elif self.add_prefix.isChecked():
            prefix = self.prefix_text.text()
            new_name = f"{prefix}{name_without_ext}.{output_format}"
        elif self.add_suffix.isChecked():
            suffix = self.suffix_text.text()
            new_name = f"{name_without_ext}{suffix}.{output_format}"
        else:
            new_name = f"{name_without_ext}_watermark.{output_format}"
        
        # 返回完整路径
        return os.path.join(self.output_dir.text(), new_name)
        
    def get_image_creation_date(self, image_path):
        """从图片的EXIF信息中提取拍摄日期时间"""
        try:
            img = Image.open(image_path)
            # 尝试通过piexif库获取EXIF信息
            try:
                exif_dict = piexif.load(img.info['exif'])
                if piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
                    date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
                    # 格式通常是"YYYY:MM:DD HH:MM:SS"
                    try:
                        date_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                        return date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        # 尝试其他常见格式
                        pass
            except (KeyError, AttributeError, piexif.InvalidImageDataError):
                # 如果piexif失败，尝试使用PIL的ExifTags
                exif_data = img._getexif()
                if exif_data:
                    for tag, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag, tag)
                        if tag_name == 'DateTimeOriginal':
                            try:
                                date_obj = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                                return date_obj.strftime('%Y-%m-%d')
                            except ValueError:
                                pass
            
            # 如果无法获取EXIF信息，返回文件的修改时间
            file_mtime = os.path.getmtime(image_path)
            date_obj = datetime.fromtimestamp(file_mtime)
            return date_obj.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"无法获取图片{image_path}的拍摄日期: {e}")
            # 返回当前日期作为后备选项
            return datetime.now().strftime('%Y-%m-%d')
        
    def parse_color(self, color_str, opacity):
        """解析颜色字符串为RGBA元组，应用透明度"""
        # 支持的预定义颜色
        colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255)
        }
        
        # 检查是否是预定义颜色
        if color_str.lower() in colors:
            r, g, b = colors[color_str.lower()]
        # 尝试解析HEX颜色代码
        elif color_str.startswith('#'):
            try:
                # 去除#号
                color_str = color_str.lstrip('#')
                # 解析RGB值
                r = int(color_str[0:2], 16)
                g = int(color_str[2:4], 16)
                b = int(color_str[4:6], 16)
            except ValueError:
                # 默认返回白色
                r, g, b = 255, 255, 255
        else:
            # 默认返回白色
            r, g, b = 255, 255, 255
        
        # 应用透明度
        a = int(255 * opacity / 100)
        return (r, g, b, a)
        
    def add_watermark(self, image_path, output_path, text, font_size, color, position):
        """给图片添加文字水印"""
        try:
            # 打开图片
            img = Image.open(image_path)
            
            # 获取文本大小和位置
            try:
                font = ImageFont.truetype("Arial.ttf", font_size)
            except IOError:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", font_size)
                except IOError:
                    font = ImageFont.load_default()
            
            # 创建绘图对象
            draw = ImageDraw.Draw(img)
            
            # 获取文本大小 (使用textbbox替代textsize)
            try:
                # 对于Pillow 9.0.0及以上版本，使用textbbox
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except AttributeError:
                # 对于旧版本的Pillow，回退到textsize
                text_width, text_height = draw.textsize(text, font=font)
            
            # 确定水印位置
            img_width, img_height = img.size
            
            if self.watermark_pos:
                # 使用手动拖拽的位置
                x, y = self.watermark_pos
            else:
                # 使用预设位置
                if position == 'top_left':
                    x, y = 10, 10
                elif position == 'top_center':
                    x, y = (img_width - text_width) // 2, 10
                elif position == 'top_right':
                    x, y = img_width - text_width - 10, 10
                elif position == 'left_center':
                    x, y = 10, (img_height - text_height) // 2
                elif position == 'center':
                    x, y = (img_width - text_width) // 2, (img_height - text_height) // 2
                elif position == 'right_center':
                    x, y = img_width - text_width - 10, (img_height - text_height) // 2
                elif position == 'bottom_left':
                    x, y = 10, img_height - text_height - 10
                elif position == 'bottom_center':
                    x, y = (img_width - text_width) // 2, img_height - text_height - 10
                elif position == 'bottom_right':
                    x, y = img_width - text_width - 10, img_height - text_height - 10
                else:
                    # 默认位置为右下角
                    x, y = img_width - text_width - 10, img_height - text_height - 10
            
            # 如果有旋转角度，创建一个新的图像用于旋转
            if self.watermark_rotation != 0:
                # 创建一个透明的新图像来绘制旋转的文本
                txt_img = Image.new('RGBA', (text_width + 20, text_height + 20), (255, 255, 255, 0))
                txt_draw = ImageDraw.Draw(txt_img)
                
                # 绘制文本和阴影到临时图像
                txt_draw.text((10, 10), text, font=font, fill=color)
                txt_draw.text((11, 11), text, font=font, fill=(0, 0, 0, 128))  # 阴影
                
                # 旋转文本图像
                rotated_txt = txt_img.rotate(self.watermark_rotation, expand=True)
                
                # 计算旋转后的位置
                rot_width, rot_height = rotated_txt.size
                rot_x = x - (rot_width - text_width) // 2
                rot_y = y - (rot_height - text_height) // 2
                
                # 粘贴旋转后的文本到原图
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                img.paste(rotated_txt, (rot_x, rot_y), rotated_txt)
            else:
                # 直接绘制水印（添加阴影效果增强可读性）
                draw.text((x+1, y+1), text, font=font, fill=(0, 0, 0, 128))  # 阴影
                draw.text((x, y), text, font=font, fill=color)
            
            # 保存图片
            output_format = os.path.splitext(output_path)[1].lower()
            if output_format == '.jpg' or output_format == '.jpeg':
                img.save(output_path, 'JPEG', quality=95)
            else:
                img.save(output_path, 'PNG')
            
            return True
        except Exception as e:
            print(f"处理图片{image_path}时出错: {e}")
            return False
        
    def export_images(self):
        # 这个函数可以简单地调用apply_watermark，因为主要的导出逻辑已经在那里实现了
        self.apply_watermark()

class QRadioButton(QCheckBox):
    def __init__(self, text=''):
        super().__init__(text)
        self.setStyleSheet("QCheckBox::indicator { width: 20px; height: 20px; border-radius: 10px; }")

if __name__ == '__main__':
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        # 如果有参数，使用命令行模式
        parser = argparse.ArgumentParser(description='给图片添加水印')
        parser.add_argument('path', help='图片文件路径或包含图片的目录路径')
        parser.add_argument('--font-size', type=int, default=30, help='水印字体大小（默认：30）')
        parser.add_argument('--color', default='white', help='水印颜色，可以是预定义颜色或HEX代码（默认：white）')
        parser.add_argument('--opacity', type=int, default=80, help='水印透明度（0-100，默认：80）')
        parser.add_argument('--position', choices=['top_left', 'top_right', 'bottom_left', 'bottom_right', 'center', 
                                                  'top_center', 'left_center', 'right_center', 'bottom_center'], 
                            default='bottom_right', help='水印位置（默认：bottom_right）')
        parser.add_argument('--output-dir', help='输出文件夹路径')
        parser.add_argument('--text', help='水印文本')
        parser.add_argument('--use-date', action='store_true', help='使用拍摄日期作为水印')
        parser.add_argument('--rotation', type=int, default=0, help='水印旋转角度（-180到180，默认：0）')
        
        args = parser.parse_args()
        
        # 解析颜色
        def parse_color(color_str, opacity):
            # 支持的预定义颜色
            colors = {
                'black': (0, 0, 0),
                'white': (255, 255, 255),
                'red': (255, 0, 0),
                'green': (0, 255, 0),
                'blue': (0, 0, 255),
                'yellow': (255, 255, 0),
                'cyan': (0, 255, 255),
                'magenta': (255, 0, 255)
            }
            
            # 检查是否是预定义颜色
            if color_str.lower() in colors:
                r, g, b = colors[color_str.lower()]
            # 尝试解析HEX颜色代码
            elif color_str.startswith('#'):
                try:
                    # 去除#号
                    color_str = color_str.lstrip('#')
                    # 解析RGB值
                    r = int(color_str[0:2], 16)
                    g = int(color_str[2:4], 16)
                    b = int(color_str[4:6], 16)
                except ValueError:
                    # 默认返回白色
                    r, g, b = 255, 255, 255
            else:
                # 默认返回白色
                r, g, b = 255, 255, 255
            
            # 应用透明度
            a = int(255 * opacity / 100)
            return (r, g, b, a)
        
        color = parse_color(args.color, args.opacity)
        
        # 设置输出目录
        if not args.output_dir:
            output_dir = f"{args.path}_watermark" if os.path.isfile(args.path) else f"{args.path}_watermark"
        else:
            output_dir = args.output_dir
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取要处理的文件列表
        if os.path.isfile(args.path):
            # 如果输入是单个文件
            files_to_process = [os.path.basename(args.path)]
            input_dir = os.path.dirname(args.path)
            if not input_dir:
                input_dir = '.'
        else:
            # 如果输入是目录
            files_to_process = [f for f in os.listdir(args.path) if os.path.splitext(f)[1].lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']]
            input_dir = args.path
        
        # 创建水印应用实例
        app = WatermarkApp()
        app.watermark_rotation = args.rotation  # 设置旋转角度
        
        # 处理每个文件
        success_count = 0
        for filename in files_to_process:
            file_path = os.path.join(input_dir, filename)
            if not os.path.isfile(file_path):
                continue
            
            # 获取水印文本
            if args.use_date:
                watermark_text = app.get_image_creation_date(file_path)
            elif args.text:
                watermark_text = args.text
            else:
                watermark_text = "水印"
            
            # 创建输出文件路径
            base_name, ext = os.path.splitext(filename)
            output_path = os.path.join(output_dir, f"{base_name}_watermark{ext}")
            
            # 添加水印并保存
            if app.add_watermark(file_path, output_path, watermark_text, args.font_size, color, args.position):
                success_count += 1
        
        print(f"处理完成！成功添加水印 {success_count} 张图片，失败 {len(files_to_process) - success_count} 张图片")
    else:
        # 如果没有参数，启动GUI模式
        app = QApplication(sys.argv)
        window = WatermarkApp()
        window.show()
        # 在应用退出前保存最后一次的设置
        app.aboutToQuit.connect(window.save_last_settings)
        sys.exit(app.exec_())