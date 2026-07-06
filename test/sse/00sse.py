import time


def get_numbers_return():
    result = []
    for i in range(5):
        result.append(i)
    return result

nums = get_numbers_return()
print(nums)


def get_numbers_yield():

    for i in range(5):
        # 休眠
        time.sleep(1)
        yield i

# 生成器
gen = get_numbers_yield()
print(next(gen))
print(next(gen))
print(next(gen))
print(next(gen))
print(next(gen))