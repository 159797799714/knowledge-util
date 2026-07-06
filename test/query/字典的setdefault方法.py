my_dict = {}

# 方式一：传统写法
# if "name" not in my_dict:
#     my_dict["name"] = "Lingma"
# value = my_dict["name"]




# 方式二：使用 setdefault (更简洁)
value = my_dict.setdefault("name", "Lingma")
value = my_dict.setdefault("name", "Lingma 222222")
print(value)
