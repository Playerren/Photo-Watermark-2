#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.enums import TA_CENTER

# 创建PDF文件
def create_github_pdf(output_path):
    # 创建PDF文档对象
    doc = SimpleDocTemplate(output_path, pagesize=letter, 
                           rightMargin=72, leftMargin=72, 
                           topMargin=72, bottomMargin=72)
    
    # 创建内容列表
    content = []
    
    # 获取样式
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['BodyText']
    centered_style = styles['BodyText']
    centered_style.alignment = TA_CENTER
    
    # 添加标题
    title = Paragraph("图片水印工具 - GitHub 仓库信息", title_style)
    content.append(title)
    
    # 添加说明文本
    description = Paragraph("这是图片水印工具的项目信息文档。您可以通过以下链接访问项目的GitHub仓库并下载最新的Release版本。", normal_style)
    content.append(description)
    
    # 添加仓库URL
    repo_url = Paragraph("<b>GitHub 仓库地址:</b><br/><a href='https://github.com/Playerren/Photo-Watermark-2.git'>https://github.com/Playerren/Photo-Watermark-2.git</a>", normal_style)
    content.append(repo_url)
    
    # 添加Release页面URL
    release_url = Paragraph("<b>最新Release页面:</b><br/><a href='https://github.com/Playerren/Photo-Watermark-2/releases/latest'>https://github.com/Playerren/Photo-Watermark-2/releases/latest</a>", normal_style)
    content.append(release_url)
    
    # 添加使用说明
    usage_title = Paragraph("<b>使用方法:</b>", normal_style)
    content.append(usage_title)
    
    usage_step1 = Paragraph("1. 访问GitHub Release页面下载最新版本的应用程序", normal_style)
    content.append(usage_step1)
    
    usage_step2 = Paragraph("2. 解压下载的文件", normal_style)
    content.append(usage_step2)
    
    usage_step3 = Paragraph("3. 将应用程序拖动到您的应用程序文件夹中", normal_style)
    content.append(usage_step3)
    
    usage_step4 = Paragraph("4. 双击打开应用程序即可开始使用", normal_style)
    content.append(usage_step4)
    
    # 构建PDF
    doc.build(content)
    
    print(f"PDF文件已成功创建: {output_path}")

if __name__ == "__main__":
    output_file = "GitHub_Repository_Photo_Watermark.pdf"
    create_github_pdf(output_file)