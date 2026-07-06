import time

star_time = time.time()
time.sleep(5)
elapsed_time = time.time() - star_time

print( f"处理中...... 已耗时: {elapsed_time}s")