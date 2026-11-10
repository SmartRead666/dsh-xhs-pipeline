# -*- coding: utf-8 -*-
"""
一键初始化（新同事第一次用，跑这一次就行）
支持 Windows / macOS / Linux
- 建工作目录：photos / fonts / profiles / output / _work / content
- 检查 playwright，缺了自动 pip 安装
- 浏览器探测：Chrome → Edge → Playwright 自带 Chromium（**不需要非装 Chrome**）
- 下载得意黑字体（失败不影响出图，会回退系统字体）
- 生成 config.json
用法: python setup.py [--home D:/xhs-workspace]
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

DEFAULT_CONFIG = {
    "home": "",
    "fonts_dir": "",
    "default_time": "17:30",
    "accounts": [{
        "slug": "me",
        "name": "我的小红书号",
        "handle": "我的小红书号",
        "brand": "我的内容品牌",
        "default_time": "17:30",
    }],
}


def say(msg):
    print("[setup]", msg, flush=True)


def ensure_dirs(home):
    for d in ["photos", "fonts", "profiles", "output", "_work", "content"]:
        os.makedirs(os.path.join(home, d), exist_ok=True)
    say("工作目录就绪：" + home)


def ensure_playwright():
    try:
        import playwright  # noqa
        say("playwright 已安装")
        return True
    except ImportError:
        say("安装 playwright（约 30 秒）...")
        cmds = [
            [sys.executable, "-m", "pip", "install", "playwright"],
            [sys.executable, "-m", "pip", "install", "--user", "playwright"],
            [sys.executable, "-m", "pip", "install", "--user", "--break-system-packages", "playwright"],
        ]
        err = ""
        for cmd in cmds:
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0:
                say("playwright 安装成功")
                return True
            err = (r.stderr or "")[-400:]
        say("playwright 安装失败：\n" + err)
        say("   macOS 上可试：brew install python && python3 -m pip install playwright")
        return False


def find_browser():
    """Chrome → Edge → Playwright 自带 Chromium，任一可用即可"""
    cands = [
        ("Chrome", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        ("Chrome", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        ("Chrome", os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")),
        ("Edge", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        ("Edge", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        ("Chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ("Edge", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
        ("Chrome", "/usr/bin/google-chrome"),
        ("Edge", "/usr/bin/microsoft-edge"),
    ]
    for name, c in cands:
        if os.path.exists(c):
            say("找到浏览器：%s" % name)
            say("   " + c)
            return name

    say("没找到 Chrome / Edge，正在安装 Playwright 自带 Chromium（约 120MB，1-2 分钟）...")
    r = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        say("Chromium 已装好，脚本会自动使用它")
        return "Chromium"
    say("⚠ 自动安装失败，请手动装 Chrome 或 Edge 任一个")
    say("   " + (r.stderr or "")[-300:])
    return None


def ensure_smiley(fonts_dir):
    target = os.path.join(fonts_dir, "SmileySans-Oblique.ttf")
    if os.path.exists(target):
        say("封面字体已存在")
        return
    url = "https://github.com/atelier-anchor/smiley-sans/releases/download/v2.0.1/smiley-sans-v2.0.1.zip"
    say("下载封面字体（得意黑）...")
    try:
        tmp = tempfile.mkdtemp()
        zp = os.path.join(tmp, "smiley.zip")
        urllib.request.urlretrieve(url, zp)
        with zipfile.ZipFile(zp) as z:
            for n in z.namelist():
                if n.endswith("SmileySans-Oblique.ttf"):
                    with z.open(n) as f, open(target, "wb") as o:
                        o.write(f.read())
                    break
        say("字体已装到 " + target)
    except Exception as e:
        say("字体下载失败（不影响出图，会回退系统字体）：%s" % e)


def ensure_config(home):
    cfg_path = os.path.join(home, "config.json")
    if os.path.exists(cfg_path):
        say("config.json 已存在：" + cfg_path)
        return cfg_path
    data = dict(DEFAULT_CONFIG)
    example = os.path.join(ROOT, "config.example.json")
    if os.path.exists(example):
        try:
            data = json.load(open(example, encoding="utf-8"))
        except Exception:
            pass
    data["home"] = home
    data["fonts_dir"] = os.path.join(home, "fonts")
    json.dump(data, open(cfg_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    say("已生成 config.json：" + cfg_path)
    say("   ⚠ 打开它，把 accounts 里的 name / handle / brand 改成你自己的账号")
    return cfg_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--home", default="")
    a = ap.parse_args()
    home = os.path.expanduser(a.home or os.path.join(os.path.expanduser("~"), "xhs-workspace"))
    say("开始初始化，工作目录：" + home)
    ensure_dirs(home)
    ok_pw = ensure_playwright()
    browser = find_browser()
    ensure_smiley(os.path.join(home, "fonts"))
    cfg = ensure_config(home)
    say("")
    say("初始化完成。下一步：")
    say("  1. 改 %s 里的账号信息（name / handle / brand）" % cfg)
    say("  2. 在 DSH 里说「帮我登录小红书账号」，用手机扫码")
    say("  3. 说「用示例内容出一张封面」，确认能出图")
    if not ok_pw or not browser:
        say("  ⚠ 有依赖没就绪（playwright=%s, 浏览器=%s），先补上再做第 2 步" % (ok_pw, browser))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
