"""泡茶模拟器：对比同步与异步方式完成泡茶流程的耗时。

泡茶流程包含三个步骤：
- boil_water()      烧水，耗时 3 秒
- prepare_teapot()  准备茶壶，耗时 1 秒
- add_tea_leaves()  添加茶叶，耗时 0.5 秒

同步方式：三个步骤依次执行，总耗时约为各步骤之和（3 + 1 + 0.5 = 4.5 秒）。
异步方式：三个步骤并发执行，总耗时约为最长步骤的耗时（约 3 秒）。
"""

import asyncio
import time

# 各步骤模拟耗时（秒）
BOIL_WATER_TIME = 3
PREPARE_TEAPOT_TIME = 1
ADD_TEA_LEAVES_TIME = 0.5


# ---------- 同步版本：使用 time.sleep 阻塞等待 ----------

def boil_water_sync():
    """同步烧水：阻塞等待 3 秒。"""
    print("  [1/3] 开始烧水...")
    time.sleep(BOIL_WATER_TIME)
    print("  [1/3] 水烧开了！")


def prepare_teapot_sync():
    """同步准备茶壶：阻塞等待 1 秒。"""
    print("  [2/3] 开始准备茶壶...")
    time.sleep(PREPARE_TEAPOT_TIME)
    print("  [2/3] 茶壶准备好了！")


def add_tea_leaves_sync():
    """同步添加茶叶：阻塞等待 0.5 秒。"""
    print("  [3/3] 开始添加茶叶...")
    time.sleep(ADD_TEA_LEAVES_TIME)
    print("  [3/3] 茶叶加好了！")


def make_tea_sync():
    """同步泡茶：依次执行三个步骤，期间无法做其他事情。

    :return: 同步泡茶总耗时（秒）
    """
    print("=== 同步泡茶开始 ===")
    start = time.perf_counter()
    boil_water_sync()
    prepare_teapot_sync()
    add_tea_leaves_sync()
    elapsed = time.perf_counter() - start
    print(f"=== 同步泡茶完成，耗时 {elapsed:.2f} 秒 ===\n")
    return elapsed


# ---------- 异步版本：使用 asyncio.sleep 非阻塞等待 ----------

async def boil_water():
    """异步烧水：非阻塞等待 3 秒，等待期间事件循环可调度其他任务。"""
    print("  [烧水] 开始烧水...")
    await asyncio.sleep(BOIL_WATER_TIME)
    print("  [烧水] 水烧开了！")


async def prepare_teapot():
    """异步准备茶壶：非阻塞等待 1 秒。"""
    print("  [备壶] 开始准备茶壶...")
    await asyncio.sleep(PREPARE_TEAPOT_TIME)
    print("  [备壶] 茶壶准备好了！")


async def add_tea_leaves():
    """异步添加茶叶：非阻塞等待 0.5 秒。"""
    print("  [加茶] 开始添加茶叶...")
    await asyncio.sleep(ADD_TEA_LEAVES_TIME)
    print("  [加茶] 茶叶加好了！")


async def make_tea_async():
    """异步泡茶：通过 asyncio.gather 并发执行三个步骤。

    烧水、备壶、加茶互不依赖，可以同时进行，
    总耗时取决于耗时最长的步骤（烧水 3 秒）。

    :return: 异步泡茶总耗时（秒）
    """
    print("=== 异步泡茶开始 ===")
    start = time.perf_counter()
    await asyncio.gather(boil_water(), prepare_teapot(), add_tea_leaves())
    elapsed = time.perf_counter() - start
    print(f"=== 异步泡茶完成，耗时 {elapsed:.2f} 秒 ===\n")
    return elapsed


async def main():
    """主函数：分别执行同步与异步泡茶流程，并打印时间对比结果。"""
    sync_time = make_tea_sync()
    async_time = await make_tea_async()

    print("=" * 46)
    print("泡茶时间对比")
    print("=" * 46)
    print(f"同步方式耗时: {sync_time:.2f} 秒 (顺序执行 3 + 1 + 0.5 = 4.5 秒)")
    print(f"异步方式耗时: {async_time:.2f} 秒 (并发执行，约等于最长的 3 秒)")
    print(f"异步比同步快: {sync_time - async_time:.2f} 秒")
    print("=" * 46)


if __name__ == "__main__":
    asyncio.run(main())
