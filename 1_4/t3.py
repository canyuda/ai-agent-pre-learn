"""超时控制：用 asyncio.wait_for() 为异步任务设置超时，超时后返回默认值。

题目要求：调用一个耗时 5 秒的异步任务，限时 2 秒；
超时后返回默认值"请求超时，使用缓存数据"。

知识点：
- asyncio.wait_for(coro, timeout) 在超时后会取消内部任务并抛出 asyncio.TimeoutError；
- 捕获该异常即可返回兜底的缓存数据，而不会等待任务真正跑完。
"""

import asyncio
import time

# 超时时间（秒）
TIMEOUT = 2
# 超时时返回的默认值
DEFAULT_RESULT = "请求超时，使用缓存数据"


async def slow_task():
    """模拟耗时 5 秒的异步任务（如响应缓慢的远程接口）。"""
    await asyncio.sleep(5)
    return "真实数据"


async def quick_task():
    """模拟耗时 1 秒的异步任务（对照组：不会触发超时）。"""
    await asyncio.sleep(1)
    return "真实数据"


async def fetch_with_timeout(coro, timeout: float) -> str:
    """调用异步任务并限时执行，超时则返回默认的缓存数据。

    :param coro: 要执行的协程对象
    :param timeout: 超时时间（秒）
    :return: 任务结果；若超时则为 DEFAULT_RESULT
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        # wait_for 超时后已自动取消内部任务，这里直接返回兜底数据
        print(f"  等待超过 {timeout} 秒，触发 TimeoutError")
        return DEFAULT_RESULT


async def main():
    """主函数：演示超时与不超时两种场景，打印返回值与实际耗时。"""
    # 场景一：任务 5 秒 > 超时 2 秒，必然超时
    print("=== 场景一：5 秒任务，限时 2 秒（触发超时）===")
    start = time.perf_counter()
    result = await fetch_with_timeout(slow_task(), timeout=TIMEOUT)
    elapsed = time.perf_counter() - start
    print(f"  返回结果: {result}")
    print(f"  实际耗时: {elapsed:.2f} 秒 (任务本身需 5 秒，超时后立即返回默认值)\n")

    # 场景二：任务 1 秒 < 超时 2 秒，正常完成
    print("=== 场景二：1 秒任务，限时 2 秒（正常完成）===")
    start = time.perf_counter()
    result = await fetch_with_timeout(quick_task(), timeout=TIMEOUT)
    elapsed = time.perf_counter() - start
    print(f"  返回结果: {result}")
    print(f"  实际耗时: {elapsed:.2f} 秒 (任务在限时内完成，拿到真实数据)")


if __name__ == "__main__":
    asyncio.run(main())
