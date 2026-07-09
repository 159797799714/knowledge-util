from typing import Dict, List

from .redis_utils import (
    set_task_status as redis_set_task_status,
    get_task_status as redis_get_task_status,
    add_running_task as redis_add_running_task,
    remove_running_task as redis_remove_running_task,
    get_running_tasks as redis_get_running_tasks,
    add_done_task as redis_add_done_task,
    get_done_tasks as redis_get_done_tasks,
    set_task_result as redis_set_task_result,
    get_task_result as redis_get_task_result,
    clear_task as redis_clear_task,
)
from .sse_utils import push_to_session

TASK_STATUS_PENDING = "pending"
TASK_STATUS_PROCESSING = "processing"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"

_NODE_NAME_TO_CN: Dict[str, str] = {
    "upload_file": "开始上传文件",
    "node_entry": "检查文件",
    "node_pdf_to_md": "PDF转Markdown",
    "node_md_img": "Markdown图片处理",
    "node_item_name_recognition": "主体名称识别",
    "node_document_split": "文档切分",
    "node_bge_embedding": "向量生成",
    "node_import_milvus": "导入向量库",
    "__end__": "处理完成",
    "END": "处理完成",
    "node_item_name_confirm": "确认问题产品",
    "node_answer_output": "生成答案",
    "node_rerank": "重排序",
    "node_rrf": "倒排融合",
    "node_web_search_mcp": "网络搜索",
    "node_search_embedding": "切片搜索",
    "node_search_embedding_hyde": "切片搜索(假设性文档)",
    "node_multi_search": "多路搜索",
    "node_join": "多路搜索合并",
}


def _to_cn(node_name: str) -> str:
    return _NODE_NAME_TO_CN.get(node_name, node_name)


def add_running_task(task_id: str, node_name: str, is_stream: bool = False) -> None:
    redis_add_running_task(task_id, node_name)
    if is_stream:
        task_push_queue(task_id)


def add_done_task(task_id: str, node_name: str, is_stream: bool = False) -> None:
    redis_remove_running_task(task_id, node_name)
    done_list = get_done_task_list(task_id)
    if node_name not in done_list:
        redis_add_done_task(task_id, node_name)
    if is_stream:
        task_push_queue(task_id)


def set_task_result(task_id: str, key: str, value: str) -> None:
    redis_set_task_result(task_id, key, value)


def get_task_result(task_id: str, key: str, default: str = "") -> str:
    return redis_get_task_result(task_id, key, default)


def get_task_status(task_id: str) -> str:
    return redis_get_task_status(task_id)


def get_done_task_list(task_id: str) -> List[str]:
    done = redis_get_done_tasks(task_id)
    return [_to_cn(n) for n in done]


def get_running_task_list(task_id: str) -> List[str]:
    running = redis_get_running_tasks(task_id)
    return [_to_cn(n) for n in running]


def update_task_status(task_id: str, status_name: str, push_queue: bool = False) -> None:
    redis_set_task_status(task_id, status_name)
    if push_queue:
        task_push_queue(task_id)


def task_push_queue(task_id: str):
    push_to_session(task_id, "progress", {
        "status": get_task_status(task_id),
        "done_list": get_done_task_list(task_id),
        "running_list": get_running_task_list(task_id),
    })


def clear_task(task_id: str):
    redis_clear_task(task_id)