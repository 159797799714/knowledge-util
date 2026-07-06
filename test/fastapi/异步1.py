import asyncio
import time


async def download_file(name):
    print(f"开始下载：{name}")
    await asyncio.sleep(2)  # 模拟下载耗时 2 秒（让出控制权2秒，非阻塞）
    print(f"下载完成：{name}")

# task1 = asyncio.create_task(download_file("文件 1"))
async def main():
    await asyncio.gather(
        download_file("文件 1"),
        download_file("文件 1"),
        download_file("文件 1")
    )

time_begin = time.time()
asyncio.run(main())
time_end = time.time()
print(f"耗时：{time_end - time_begin}")
