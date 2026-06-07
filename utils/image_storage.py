# -*- coding: utf-8 -*-
"""
图片存储管理器
支持按用户+日期隔离、自动清理、空间监控
"""

import os
import json
import time
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from utils import util


class ImageStorage:
    """
    图片存储管理器

    目录结构：
    cache_data/images/
    ├── User/
    │   └── 2026-06-06/
    │       ├── abc123.jpg
    │       └── .metadata.json
    ├── 张三/
    │   └── 2026-06-06/
    └── ...
    """

    def __init__(self, base_dir: str = "cache_data/images"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def get_user_image_dir(self, username: str, date: str = None) -> str:
        """
        获取用户图片目录

        Args:
            username: 用户名
            date: 日期 (YYYY-MM-DD)，默认今天

        Returns:
            目录路径
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        user_dir = os.path.join(self.base_dir, username, date)
        os.makedirs(user_dir, exist_ok=True)
        return user_dir

    def save_image(
        self,
        file_content: bytes,
        filename: str,
        username: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        保存图片并返回访问信息

        Args:
            file_content: 文件内容
            filename: 文件名
            username: 用户名
            metadata: 额外元数据

        Returns:
            {
                "path": 绝对路径,
                "relative_path": 相对路径,
                "url": 访问URL,
                "filename": 文件名,
                "username": 用户名,
                "date": 日期,
                "timestamp": 时间戳
            }
        """
        # 获取用户目录
        user_dir = self.get_user_image_dir(username)

        # 保存文件
        file_path = os.path.join(user_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # 构建返回信息
        date = datetime.now().strftime("%Y-%m-%d")
        relative_path = os.path.join(username, date, filename)

        result = {
            "path": file_path,
            "relative_path": relative_path,
            "url": f"/api/get-image/{username}/{date}/{filename}",
            "filename": filename,
            "username": username,
            "date": date,
            "timestamp": int(time.time())
        }

        # 保存元数据
        if metadata:
            result.update(metadata)

        self._save_metadata(user_dir, filename, result)

        return result

    def _save_metadata(self, user_dir: str, filename: str, data: dict):
        """
        保存图片元数据到 .metadata.json
        """
        metadata_file = os.path.join(user_dir, ".metadata.json")

        # 读取现有元数据
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except:
                metadata = {}
        else:
            metadata = {}

        # 添加新记录
        metadata[filename] = data

        # 写回文件
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def get_image_info(self, username: str, date: str, filename: str) -> Optional[Dict]:
        """
        获取图片元数据
        """
        user_dir = os.path.join(self.base_dir, username, date)
        metadata_file = os.path.join(user_dir, ".metadata.json")

        if not os.path.exists(metadata_file):
            return None

        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            return metadata.get(filename)
        except:
            return None

    def list_user_images(
        self,
        username: str,
        date: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        列出用户的图片

        Args:
            username: 用户名
            date: 日期，None 表示所有日期
            limit: 最大数量

        Returns:
            图片信息列表
        """
        user_base_dir = os.path.join(self.base_dir, username)

        if not os.path.exists(user_base_dir):
            return []

        images = []

        # 确定要扫描的日期目录
        if date:
            date_dirs = [date]
        else:
            try:
                date_dirs = sorted(os.listdir(user_base_dir), reverse=True)
            except:
                return []

        for date_dir in date_dirs:
            metadata_file = os.path.join(user_base_dir, date_dir, ".metadata.json")
            if not os.path.exists(metadata_file):
                continue

            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                for filename, info in metadata.items():
                    images.append(info)
                    if len(images) >= limit:
                        return images
            except:
                continue

        return images

    def cleanup_old_images(
        self,
        days: int = 7,
        username: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, any]:
        """
        清理超过指定天数的图片

        Args:
            days: 保留天数（默认 7 天）
            username: 指定用户名，None 表示所有用户
            dry_run: 预览模式，不实际删除

        Returns:
            清理结果
        """
        util.log(1, f"开始清理图片：保留 {days} 天，用户={'所有' if not username else username}，{'预览' if dry_run else '实际删除'}")

        # 计算截止日期
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")

        util.log(1, f"截止日期：{cutoff_str}，早于此日期的图片将被清理")

        result = {
            "deleted_dirs": [],
            "deleted_files": 0,
            "freed_space_mb": 0.0,
            "skipped_dirs": [],
            "errors": []
        }

        # 确定要扫描的用户列表
        if username:
            users_to_scan = [username] if os.path.exists(os.path.join(self.base_dir, username)) else []
        else:
            try:
                users_to_scan = [u for u in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, u))]
            except:
                users_to_scan = []

        util.log(1, f"扫描 {len(users_to_scan)} 个用户目录")

        # 遍历每个用户
        for user in users_to_scan:
            user_dir = os.path.join(self.base_dir, user)

            if not os.path.isdir(user_dir):
                continue

            # 遍历该用户的日期目录
            try:
                date_dirs = os.listdir(user_dir)
            except:
                continue

            for date_dir_name in date_dirs:
                date_dir_path = os.path.join(user_dir, date_dir_name)

                if not os.path.isdir(date_dir_path):
                    continue

                # 尝试解析日期
                try:
                    date_obj = datetime.strptime(date_dir_name, "%Y-%m-%d")
                except ValueError:
                    result["skipped_dirs"].append(f"{user}/{date_dir_name}")
                    continue

                # 判断是否需要删除
                if date_obj < cutoff_date:
                    relative_path = f"{user}/{date_dir_name}"

                    try:
                        # 统计文件数量和大小
                        file_count = 0
                        dir_size = 0

                        for root, dirs, files in os.walk(date_dir_path):
                            file_count += len(files)
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    dir_size += os.path.getsize(file_path)
                                except OSError:
                                    pass

                        dir_size_mb = dir_size / (1024 * 1024)

                        util.log(1, f"{'[预览]' if dry_run else '[删除]'} {relative_path}：{file_count} 个文件，{dir_size_mb:.2f} MB")

                        # 实际删除（非预览模式）
                        if not dry_run:
                            shutil.rmtree(date_dir_path)

                        # 更新统计
                        result["deleted_dirs"].append(relative_path)
                        result["deleted_files"] += file_count
                        result["freed_space_mb"] += dir_size_mb

                    except Exception as e:
                        error_msg = f"删除失败 {relative_path}: {e}"
                        util.log(1, f"错误：{error_msg}")
                        result["errors"].append(error_msg)
                else:
                    result["skipped_dirs"].append(f"{user}/{date_dir_name}")

        # 输出清理报告
        util.log(1, "=" * 60)
        util.log(1, f"图片清理完成{'（预览模式）' if dry_run else ''}")
        util.log(1, f"删除目录数：{len(result['deleted_dirs'])}")
        util.log(1, f"删除文件数：{result['deleted_files']}")
        util.log(1, f"释放空间：{result['freed_space_mb']:.2f} MB")
        util.log(1, f"保留目录数：{len(result['skipped_dirs'])}")
        util.log(1, f"错误数：{len(result['errors'])}")
        util.log(1, "=" * 60)

        return result

    def get_storage_stats(self, username: Optional[str] = None) -> Dict[str, any]:
        """
        获取存储统计信息
        """
        stats = {
            "total_dirs": 0,
            "total_files": 0,
            "total_size_mb": 0.0,
            "by_user": {},
            "oldest_date": None,
            "newest_date": None
        }

        if username:
            users_to_scan = [username]
        else:
            try:
                users_to_scan = [u for u in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, u))]
            except:
                users_to_scan = []

        all_dates = []

        for user in users_to_scan:
            user_dir = os.path.join(self.base_dir, user)
            user_stats = {"dirs": 0, "files": 0, "size_mb": 0.0}

            try:
                date_dirs = os.listdir(user_dir)
            except:
                continue

            for date_dir_name in date_dirs:
                date_dir_path = os.path.join(user_dir, date_dir_name)

                if not os.path.isdir(date_dir_path):
                    continue

                try:
                    date_obj = datetime.strptime(date_dir_name, "%Y-%m-%d")
                    all_dates.append(date_obj)
                except ValueError:
                    continue

                # 统计
                dir_size = 0
                file_count = 0

                for root, dirs, files in os.walk(date_dir_path):
                    file_count += len(files)
                    for file in files:
                        try:
                            dir_size += os.path.getsize(os.path.join(root, file))
                        except OSError:
                            pass

                user_stats["dirs"] += 1
                user_stats["files"] += file_count
                user_stats["size_mb"] += dir_size / (1024 * 1024)

            if user_stats["dirs"] > 0:
                stats["by_user"][user] = user_stats
                stats["total_dirs"] += user_stats["dirs"]
                stats["total_files"] += user_stats["files"]
                stats["total_size_mb"] += user_stats["size_mb"]

        if all_dates:
            stats["oldest_date"] = min(all_dates).strftime("%Y-%m-%d")
            stats["newest_date"] = max(all_dates).strftime("%Y-%m-%d")

        return stats


# 全局实例
_image_storage = None


def get_image_storage() -> ImageStorage:
    """获取图片存储管理器单例"""
    global _image_storage
    if _image_storage is None:
        _image_storage = ImageStorage()
    return _image_storage
