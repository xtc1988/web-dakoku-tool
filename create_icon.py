#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def create_clock_icon(output_path, size=(64, 64), bg_color=(52, 152, 219), fg_color=(255, 255, 255)):
    """時計アイコンを作成する"""
    # 画像の作成
    img = Image.new('RGBA', size, color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 円の描画（時計の外枠）
    margin = 2
    draw.ellipse(
        [(margin, margin), (size[0] - margin, size[1] - margin)],
        fill=bg_color
    )
    
    # 時計の中心
    center_x, center_y = size[0] // 2, size[1] // 2
    
    # 時計の針（時針）
    hour_hand_length = size[0] // 3
    draw.line(
        [(center_x, center_y), 
         (center_x, center_y - hour_hand_length)],
        fill=fg_color, width=3
    )
    
    # 時計の針（分針）
    minute_hand_length = size[0] // 2.5
    draw.line(
        [(center_x, center_y), 
         (center_x + minute_hand_length * 0.7, center_y + minute_hand_length * 0.7)],
        fill=fg_color, width=2
    )
    
    # 時計の中心点
    center_dot_radius = size[0] // 20
    draw.ellipse(
        [(center_x - center_dot_radius, center_y - center_dot_radius),
         (center_x + center_dot_radius, center_y + center_dot_radius)],
        fill=fg_color
    )
    
    # 画像の保存
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    
    return output_path

def main():
    # アイコンの保存先
    icon_dir = Path(__file__).parent / "icons"
    icon_dir.mkdir(exist_ok=True)
    
    # 通常アイコンの作成
    normal_icon_path = icon_dir / "clock_icon.png"
    create_clock_icon(normal_icon_path)
    
    print(f"アイコンを作成しました: {normal_icon_path}")

if __name__ == "__main__":
    main() 