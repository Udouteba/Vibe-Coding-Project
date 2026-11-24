"""内联 LaTeX 片段清洗：把 OCR 正文里混入的 $...$ 数学片段转为可读 Unicode 文本。

独立公式块（formula）保留完整 LaTeX，这里只清洗正文文本里内联的短小数学符号/单位，
如 $d_{\\mathrm{j}}$ → dⱼ、$\\left(\\mathrm{m/s^{2}}\\right)$ → (m/s²)。
"""

import re

_GREEK = {
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ",
    r"\epsilon": "ε", r"\varepsilon": "ε", r"\zeta": "ζ", r"\eta": "η",
    r"\theta": "θ", r"\iota": "ι", r"\kappa": "κ", r"\lambda": "λ",
    r"\mu": "μ", r"\nu": "ν", r"\xi": "ξ", r"\pi": "π", r"\rho": "ρ",
    r"\sigma": "σ", r"\tau": "τ", r"\upsilon": "υ", r"\phi": "φ",
    r"\varphi": "φ", r"\chi": "χ", r"\psi": "ψ", r"\omega": "ω",
    r"\Gamma": "Γ", r"\Delta": "Δ", r"\Theta": "Θ", r"\Lambda": "Λ",
    r"\Xi": "Ξ", r"\Pi": "Π", r"\Sigma": "Σ", r"\Phi": "Φ",
    r"\Psi": "Ψ", r"\Omega": "Ω",
}

_OPERATORS = {
    r"\leqslant": "≤", r"\leq": "≤", r"\geqslant": "≥", r"\geq": "≥",
    r"\times": "×", r"\cdot": "·", r"\pm": "±", r"\mp": "∓",
    r"\approx": "≈", r"\neq": "≠", r"\equiv": "≡", r"\infty": "∞",
    r"\lg": "lg", r"\ln": "ln", r"\log": "log",
    r"\sum": "∑", r"\prod": "∏", r"\int": "∫", r"\partial": "∂",
    r"\circ": "°",
}

_SUB = str.maketrans({
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    "a": "ₐ", "e": "ₑ", "h": "ₕ", "i": "ᵢ", "j": "ⱼ", "k": "ₖ",
    "l": "ₗ", "m": "ₘ", "n": "ₙ", "o": "ₒ", "p": "ₚ", "r": "ᵣ",
    "s": "ₛ", "t": "ₜ", "u": "ᵤ", "v": "ᵥ", "x": "ₓ",
})

_SUP = str.maketrans({
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ", "f": "ᶠ",
    "g": "ᵍ", "h": "ʰ", "i": "ⁱ", "j": "ʲ", "k": "ᵏ", "l": "ˡ",
    "m": "ᵐ", "n": "ⁿ", "o": "ᵒ", "p": "ᵖ", "r": "ʳ", "s": "ˢ",
    "t": "ᵗ", "u": "ᵘ", "v": "ᵛ", "w": "ʷ", "x": "ˣ", "y": "ʸ", "z": "ᶻ",
})

_FORMAT_PATTERN = re.compile(
    r"\\(?:mathrm|text|operatorname|mathbf|mathit|mathsf|mathtt|mbox)\{([^{}]*)\}"
)


def _latex_to_text(s: str) -> str:
    """单个 $...$ 内联 LaTeX 片段 → 可读文本。"""
    # 迭代消除嵌套（上下标 + 格式命令），从内到外，每轮处理一层花括号
    for _ in range(6):
        before = s
        s = re.sub(r"_\{([^{}]*)\}", lambda m: m.group(1).translate(_SUB), s)
        s = re.sub(r"\^\{([^{}]*)\}", lambda m: m.group(1).translate(_SUP), s)
        s = re.sub(r"_([0-9a-zA-Z])", lambda m: m.group(1).translate(_SUB), s)
        s = re.sub(r"\^([0-9a-zA-Z])", lambda m: m.group(1).translate(_SUP), s)
        s = _FORMAT_PATTERN.sub(r"\1", s)
        if s == before:
            break
    # 去掉成对括号命令 \left \right 等，及各种间距命令
    s = re.sub(r"\\(?:left|right|big|Big|bigg|Bigg|bigl|bigr|Bigl|Bigr)", "", s)
    s = s.replace(r"\,", "").replace(r"\;", "").replace(r"\!", "").replace(r"\ ", " ")
    # \frac{a}{b} → a/b
    s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"\1/\2", s)
    # \sqrt[n]{x} → ⁿ√(x)；\sqrt{x} → √(x)
    s = re.sub(
        r"\\sqrt\[([^\]]*)\]\{([^{}]*)\}",
        lambda m: m.group(1).translate(_SUP) + "√(" + m.group(2) + ")",
        s,
    )
    s = re.sub(r"\\sqrt\{([^{}]*)\}", r"√(\1)", s)
    # 希腊字母与运算符（消费命令后的分隔空格）
    for k, v in _GREEK.items():
        s = re.sub(re.escape(k) + r" ?", v, s)
    for k, v in _OPERATORS.items():
        s = re.sub(re.escape(k) + r" ?", v, s)
    # 残留的未知命令 \xyz → xyz；去掉花括号与美元号
    s = re.sub(r"\\([a-zA-Z]+)", r"\1", s)
    return s.replace("{", "").replace("}", "").replace("$", "")


def clean_inline_latex(text: str) -> str:
    """清洗正文里所有 $...$ 内联 LaTeX 片段，非 $ 部分原样保留。"""
    if "$" not in text:
        return text
    return re.sub(r"\$(.+?)\$", lambda m: _latex_to_text(m.group(1)), text)
