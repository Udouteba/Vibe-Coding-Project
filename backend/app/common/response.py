"""统一响应结构 Response(code, message, data)。"""


def ok(data=None, message: str = "success") -> dict:
    return {"code": 200, "message": message, "data": data}


def fail(message: str = "操作失败", code: int = 400) -> dict:
    return {"code": code, "message": message, "data": None}
