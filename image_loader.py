"""后台图像加载器"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from image_cache import is_very_large, load_thumbnail


class ImageLoader(QObject):
    finished = Signal(object, str)
    info_ready = Signal(object)
    progress = Signal(int)

    def __init__(self, file_path: str, performance_settings: Dict[str, Any]) -> None:
        """初始化加载器"""
        super().__init__()
        self.file_path = file_path
        self.performance_settings = performance_settings
        self.canceled = False

    def run(self) -> None:
        """执行加载任务"""
        try:
            if self.canceled:
                return

            if is_very_large(self.file_path):
                pixmap = load_thumbnail(self.file_path, max_edge=4096)
                if self.canceled:
                    return
                if pixmap.isNull():
                    raise RuntimeError("Thumbnail generation failed")
            else:
                pixmap = QPixmap(self.file_path)
                if self.canceled:
                    return
                if pixmap.isNull():
                    raise RuntimeError("Failed to load image")

            self.progress.emit(30)
            image_info = self.collect_image_info(self.file_path)
            if self.canceled:
                return
            self.progress.emit(70)

            self.finished.emit(pixmap, self.file_path)
            self.info_ready.emit(image_info)
            self.progress.emit(100)

        except Exception as e:
            if not self.canceled:
                self.finished.emit(None, f"Error: {str(e)}")

    def collect_image_info(self, file_path: str) -> Dict[str, Any]:
        """收集图像元信息"""
        info: Dict[str, Any] = {"file_info": {}, "image_info": {}, "exif_info": {}}

        try:
            info["file_info"] = {
                "File Name": os.path.basename(file_path),
                "Path": file_path,
                "Size": f"{os.path.getsize(file_path) / 1024:.2f} KB",
                "Modified": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S"),
            }

            if self.performance_settings["skip_exif"]:
                return info

            with Image.open(file_path) as img:
                info["image_info"] = {
                    "Format": img.format or "Unknown",
                    "Color Mode": img.mode,
                    "Dimensions": f"{img.width} x {img.height} pixels",
                    "DPI": f"{img.info.get('dpi', (72, 72))[0]} x {img.info.get('dpi', (72, 72))[1]}",
                }

                if not self.performance_settings["skip_exif"]:
                    exif = self._get_exif_data(img)
                    if exif:
                        info["exif_info"] = exif

        except Exception as e:
            info["error"] = f"Could not read image info: {str(e)}"

        return info

    def _get_exif_data(self, image: Image.Image) -> Optional[Dict[str, Any]]:
        """提取 EXIF 数据"""
        try:
            exif_data: Dict[str, Any] = {}
            raw = image.getexif()
            if not raw:
                return None

            for tag_id, value in raw.items():
                tag = TAGS.get(tag_id, tag_id)
                if isinstance(value, bytes):
                    try:
                        value = value.decode("utf-8", errors="replace")
                    except Exception:
                        value = "Binary data"

                if tag == "GPSInfo":
                    gps_data = {GPSTAGS.get(t, t): raw[tag_id][t] for t in raw[tag_id]}
                    exif_data[tag] = gps_data
                else:
                    exif_data[tag] = value

            return exif_data

        except Exception:
            return None

    def cancel(self) -> None:
        """取消加载任务"""
        self.canceled = True