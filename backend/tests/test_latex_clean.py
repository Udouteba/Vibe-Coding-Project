from app.utils.latex_clean import clean_inline_latex


def test_带下标的变量():
    assert clean_inline_latex("$d_{\\mathrm{j}}$ 管道计算内径") == "dⱼ 管道计算内径"


def test_单位带指数():
    assert clean_inline_latex("$\\left(\\mathrm{m/s^{2}}\\right)$") == "(m/s²)"


def test_简单单位():
    assert clean_inline_latex("$\\mathrm{m}/\\mathrm{s}$") == "m/s"


def test_不等式范围():
    assert clean_inline_latex("$1\\leqslant R\\leqslant3.0$") == "1≤R≤3.0"


def test_根号():
    assert clean_inline_latex("$\\sqrt{n}$") == "√(n)"
    assert clean_inline_latex("$\\sqrt[n]{n}$") == "ⁿ√(n)"


def test_希腊字母与雷诺数():
    assert clean_inline_latex("$\\lambda$") == "λ"
    assert clean_inline_latex("$R e$ ——雷诺数") == "R e ——雷诺数"


def test_无美元号原样返回():
    text = "式中：λ沿程阻力系数"
    assert clean_inline_latex(text) == text


def test_混合文本只清洗片段():
    assert clean_inline_latex("流量$q\\left(m^3/s\\right)$。") == "流量q(m³/s)。"
