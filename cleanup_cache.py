#!/usr/bin/env python3
"""
缓存清理脚本 - 安全删除临时文件
只删除真正的缓存，不影响持久化数据
"""
import os
import time
import glob
from pathlib import Path

# 配置
CACHE_DIR = "cache_data"
MAX_AGE_DAYS = 7  # 保留最近 7 天的临时文件

# 可以安全删除的临时文件模式
TEMP_PATTERNS = [
    "tmp*.wav",           # TTS 临时音频
    "input.wav",          # ASR 输入音频
    "asr_uploads/*.wav",  # ASR 上传的临时文件
]

# 绝对不能删除的目录和文件
PROTECTED = [
    "backgrounds",
    "avatars",
    "images",
    "chromadb_yueshen",
    "chromadb_yueshen_clean",
    "config.json",
    "window_captures",
]


def is_old_file(filepath, max_age_days):
    """检查文件是否超过指定天数"""
    file_time = os.path.getmtime(filepath)
    age_seconds = time.time() - file_time
    age_days = age_seconds / (24 * 3600)
    return age_days > max_age_days


def cleanup_temp_files(dry_run=True):
    """清理临时文件"""
    total_size = 0
    deleted_count = 0

    print(f"{'[DRY RUN] ' if dry_run else ''}开始清理 cache_data 目录...")
    print(f"保留最近 {MAX_AGE_DAYS} 天的文件\n")

    for pattern in TEMP_PATTERNS:
        pattern_path = os.path.join(CACHE_DIR, pattern)
        files = glob.glob(pattern_path)

        for filepath in files:
            # 检查是否是受保护的路径
            is_protected = any(protected in filepath for protected in PROTECTED)
            if is_protected:
                continue

            # 检查文件年龄
            if is_old_file(filepath, MAX_AGE_DAYS):
                file_size = os.path.getsize(filepath)
                total_size += file_size
                deleted_count += 1

                print(f"{'[模拟] ' if dry_run else ''}删除: {filepath} ({file_size / 1024:.1f} KB)")

                if not dry_run:
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        print(f"  错误: {e}")

    print(f"\n{'[模拟] ' if dry_run else ''}共{'将'if dry_run else '已'}删除 {deleted_count} 个文件")
    print(f"{'[模拟] ' if dry_run else ''}释放空间: {total_size / (1024 * 1024):.2f} MB")

    if dry_run:
        print("\n[警告] 这是模拟运行，未实际删除文件")
        print("运行 python cleanup_cache.py --execute 执行实际清理")


def show_cache_status():
    """显示缓存状态"""
    print("=== 缓存目录状态 ===\n")

    # 统计临时文件
    temp_files = []
    for pattern in TEMP_PATTERNS:
        temp_files.extend(glob.glob(os.path.join(CACHE_DIR, pattern)))

    temp_size = sum(os.path.getsize(f) for f in temp_files)

    print(f"临时文件数量: {len(temp_files)}")
    print(f"临时文件大小: {temp_size / (1024 * 1024):.2f} MB")

    # 显示最老的文件
    if temp_files:
        oldest = min(temp_files, key=os.path.getmtime)
        oldest_age = (time.time() - os.path.getmtime(oldest)) / (24 * 3600)
        print(f"最老的临时文件: {os.path.basename(oldest)} ({oldest_age:.1f} 天前)")

    print()


if __name__ == "__main__":
    import sys

    show_cache_status()

    # 检查是否是实际执行模式
    execute = "--execute" in sys.argv or "-e" in sys.argv

    cleanup_temp_files(dry_run=not execute)
