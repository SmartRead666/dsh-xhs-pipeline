# -*- coding: utf-8 -*-
"""配置读取小工具"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load_config(path=None):
    cfg_path = path or os.environ.get("XHS_CONFIG") or os.path.join(ROOT, "config.json")
    if not os.path.exists(cfg_path):
        raise SystemExit("找不到 config.json，先运行 scripts/setup.py")
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    return cfg, os.path.dirname(os.path.abspath(cfg_path))


def find_account(cfg, slug):
    for a in cfg.get("accounts", []):
        if a.get("slug") == slug:
            return a
    raise SystemExit("配置里没有账号 slug=%s，可选：%s"
                     % (slug, ", ".join(a.get("slug", "?") for a in cfg.get("accounts", []))))


def home_of(cfg):
    return os.path.expanduser(cfg.get("home") or "~/xhs-workspace")


def profile_of(cfg, acc):
    """每个账号独立浏览器目录，避免串号"""
    if acc.get("profile"):
        return os.path.expanduser(acc["profile"])
    return os.path.join(home_of(cfg), "profiles", acc["slug"])
