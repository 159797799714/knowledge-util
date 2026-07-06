import re

image_file = "小美.jpg"
print(image_file)
print(re.escape(image_file))

print(r"!\\[.*?\]\(.*?" + re.escape(image_file) + r".*?\)")
print("!\\[.*?\]\(.*?" + re.escape(image_file) + ".*?\)")