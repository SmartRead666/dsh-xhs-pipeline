# -*- coding: utf-8 -*-
"""
浏览器启动兜底：Chrome → Edge → Playwright 自带 Chromium
- 不需要用户非装 Chrome；Windows 自带 Edge 也能跑
- 可用环境变量 XHS_CHANNEL 强制指定：chrome / msedge / chromium
"""
import os

_ARGS = ["--disable-blink-features=AutomationControlled"]
_CACHE = {"channel": None}


def channel_candidates():
    forced = os.environ.get("XHS_CHANNEL", "").strip()
    if forced:
        return [None if forced in ("chromium", "bundled", "none") else forced]
    # 已探测成功过的优先
    if _CACHE["channel"] is not None:
        return [_CACHE["channel"], "chrome", "msedge", None]
    return ["chrome", "msedge", None]


async def launch_persistent(p, profile, **kw):
    """带 profile 的持久化上下文（登录态保存在 profile 目录）"""
    args = kw.pop("args", None) or list(_ARGS)
    last = None
    for ch in channel_candidates():
        opts = dict(kw)
        opts["args"] = args
        if ch:
            opts["channel"] = ch
        try:
            ctx = await p.chromium.launch_persistent_context(profile, **opts)
            _CACHE["channel"] = ch
            return ctx
        except Exception as e:
            last = e
    raise RuntimeError(
        "没有可用的浏览器：装 Chrome 或 Edge 任一即可，或运行 `python -m playwright install chromium`。\n最后错误：%s" % last)


async def launch(p, **kw):
    """普通（非持久化）浏览器，用于出图渲染"""
    last = None
    for ch in channel_candidates():
        opts = dict(kw)
        if ch:
            opts["channel"] = ch
        try:
            b = await p.chromium.launch(**opts)
            _CACHE["channel"] = ch
            return b
        except Exception as e:
            last = e
    raise RuntimeError("没有可用的浏览器（Chrome / Edge / playwright chromium 都没有）：%s" % last)
