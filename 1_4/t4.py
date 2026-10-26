"""多模型竞速：同时调用 3 个"模型"，采用最先返回的结果并取消其余调用。

题目要求：实现 race_models(prompt: str) 函数，
- 同时调用 3 个"模型"（模拟，用不同时长的 asyncio.sleep()）；
- 哪个模型先返回就用哪个结果；
- 取消其余还在等待的模型调用。

知识点：
- asyncio.wait(tasks, return_when=FIRST_COMPLETED) 在第一个任务完成时立即返回，
  通过 done / pending 两个集合区分已完成与未完成任务；
- task.cancel() 只是发出取消请求，还需 await 让取消真正落地，
  用 asyncio.gather(*pending, return_exceptions=True) 吸收 CancelledError。
"""

import asyncio
import time

# 模拟各模型的响应耗时（秒）：同名请求，快模型先返回
MODEL_LATENCY = {
    "flash-0.5s": 0.5,
    "balanced-1.5s": 1.5,
    "pro-3s": 3,
}


async def call_model(model: str, latency: float, prompt: str) -> str:
    """模拟调用一个模型：等待 latency 秒后返回带模型名的回复。

    :param model: 模型名称
    :param latency: 模拟的响应耗时（秒）
    :param prompt: 用户输入
    :return: 模型的回复文本
    """
    print(f"  [{model}] 开始处理 ...")
    await asyncio.sleep(latency)
    reply = f"{model} 回答：{prompt}"
    print(f"  [{model}] 完成")
    return reply


async def race_models(prompt: str) -> str:
    """多模型竞速：并发调用全部模型，采用最先返回的结果，取消其余调用。

    :param prompt: 发给模型的用户输入
    :return: 最快返回的那个模型的回复
    """
    # 1. 同时调用 3 个"模型"：为每个调用创建 Task，放入事件循环立刻并发执行
    tasks = [
        asyncio.create_task(call_model(name, latency, prompt), name=name)
        for name, latency in MODEL_LATENCY.items()
    ]

    # 2. 哪个先返回就用哪个：FIRST_COMPLETED 让 wait 在首个任务完成时立即返回
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    winner = next(iter(done))
    result = winner.result()
    print(f"  最先返回的是 {winner.get_name()}，采用其结果")

    # 3. 取消其余还在等待的模型调用
    for task in pending:
        print(f"  取消 {task.get_name()}")
        task.cancel()
    # await 让取消请求真正落地；return_exceptions=True 吞掉 CancelledError
    await asyncio.gather(*pending, return_exceptions=True)

    return result


async def main():
    """主函数：演示多模型竞速，打印采用的回复与实际耗时。"""
    prompt = "用一句话解释什么是异步编程"
    models = ", ".join(f"{name}(模拟耗时 {latency}s)" for name, latency in MODEL_LATENCY.items())
    print(f"提示词: {prompt}")
    print(f"参赛模型: {models}")
    print("=" * 46)

    start = time.perf_counter()
    result = await race_models(prompt)
    elapsed = time.perf_counter() - start

    print("=" * 46)
    print(f"采用结果: {result}")
    print(f"实际耗时: {elapsed:.2f} 秒 (约等于最快模型的 0.5 秒，慢模型已被取消，无需等满 3 秒)")


if __name__ == "__main__":
    asyncio.run(main())
