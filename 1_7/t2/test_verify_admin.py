"""题目 2：写你的第一个测试

被测函数：verify_admin（本目录 admin_auth.py，复制自练习 5 的 API Key 依赖函数）
它是 async 函数，从同步测试里用标准库 asyncio.run() 调用即可。

运行：cd 1_7/t2 && ../../.venv/Scripts/python -m pytest -v
"""
import asyncio

import pytest

from admin_auth import VALID_ADMIN_KEY, AdminAccessDenied, verify_admin


def test_verify_admin_with_valid_key():
    """正常情况：正确的 Admin Key 鉴权通过，原样返回"""
    assert asyncio.run(verify_admin(VALID_ADMIN_KEY)) == VALID_ADMIN_KEY


def test_verify_admin_with_empty_key():
    """边界情况（空输入）：空字符串 Key 是输入域的边界，鉴权必须失败"""
    with pytest.raises(AdminAccessDenied):
        asyncio.run(verify_admin(""))


def test_verify_admin_with_wrong_key_raises():
    """预期异常：错误的 Key 抛 AdminAccessDenied，用 match 校验异常信息"""
    with pytest.raises(AdminAccessDenied, match="无效的 Admin Key"):
        asyncio.run(verify_admin("wrong-key"))
