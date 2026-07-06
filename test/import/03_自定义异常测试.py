from processor.import_processor.exceptions import ValidationError, StateFieldError

print("我要开始测试自定义异常了")


try:
    # 可能失败的操作
    raise StateFieldError("状态值错误")
except Exception as e:
    raise StateFieldError(
        node_name="一个节点",
        field_name="第一个字段",
        expected_type=str
    )