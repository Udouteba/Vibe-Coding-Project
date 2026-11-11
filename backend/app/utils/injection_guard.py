"""提示词注入特征过滤：检测检索内容中的注入指令特征。"""

# 给排水规范为客观技术条文，不使用第二人称指令语气，误伤率极低
INJECTION_KEYWORDS = (
    "忽略指令",
    "忽略上述",
    "忽略之前",
    "忽略系统",
    "系统提示词",
    "系统提示",
    "输出你的提示",
    "你现在是",
    "扮演",
    "泄露系统",
    "越狱",
    "忽略以上所有",
)


def filter_injection(text: str) -> bool:
    """检测文本是否含注入特征词；命中返回 True（应丢弃该 chunk）。"""
    return any(kw in text for kw in INJECTION_KEYWORDS)
