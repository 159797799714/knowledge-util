from dataclasses import dataclass, field


@dataclass
class User:
    # 1. 必需字段：没有默认值，创建实例时必须提供
    username: str

    # 2. 简单默认值：适用于不可变类型 (str, int, float等)
    age: int = 18

    # 3. 动态默认值：适用于可变类型 (list, dict等)，防止实例间共享状态
    tags: list = field(default_factory=list)


print("测试1：只提供必须字段")
user1 = User("小美")
print(f"user1 > {user1}")

print("测试2：只提供必须字段")
user2 = User("小帅", 20, ["程序员", "学生"])
print(f"user2 > {user2}")

user3 = User("李华")
user4 = User("韩梅梅")

user4.tags.append("学生")

print(f"user3 > {user3}")
print(f"user4 > {user4}")