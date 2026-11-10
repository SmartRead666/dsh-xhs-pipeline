from browser_launch import launch_persistent, launch
# -*- coding: utf-8 -*-
"""
互动监测（按账号）：评论/@ / 私信 / 赞藏 / 关注 的未读变化

用法:
  python monitor.py --account peter

输出: <home>/output/<slug>/互动监测/latest.md + history.jsonl + state.json
标准输出末行: NEW 或 NONE
"""
import argparse, asyncio, json, os, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from xcfg import load_config, find_account, home_of, profile_of  # noqa

RULES = [
    ("价格", ["多少钱", "价格", "费用", "收费", "优惠", "团报", "折扣", "报名费", "学费"]),
    ("质疑", ["割韭菜", "骗人", "骗钱", "智商税", "靠谱吗", "有用吗", "真的假的", "水军"]),
    ("同行", ["同行", "我也是做", "机构", "合作", "渠道", "代理", "招生"]),
    ("企业", ["公司", "团队", "我们企业", "部门", "团报", "采购", "老板让我"]),
    ("个人转型", ["35岁", "38岁", "40岁", "转行", "转型", "零基础", "能不能做", "适合吗", "怎么切", "怎么学"]),
    ("领模板", ["模板", "资料", "清单", "领取", "发我", "求", "想要", "表格"]),
    ("无效", ["沙发", "哈哈", "路过", "顶", "666"]),
]

REPLY = {
    "领模板": "评论区先给框架，再引导私信：「可以，我发你模板框架。你顺手写一个真实场景，我帮你看先看哪几个字段。」",
    "个人转型": "「你先发我三句：现在做什么｜手上有什么资源｜想解决哪件事。我先给切入判断。」不承诺就业/接单/收入。",
    "企业": "「方便说下企业类型｜参与岗位｜现在卡在哪一段？我先给组织诊断。」",
    "价格": "统一指向官方号：「价格和班期以官方号当期通知为准，私信【报名】获取最新口径。」本号不报价。",
    "质疑": "不争辩，给边界：「你的谨慎是对的。这门课不承诺就业、接单或收入，更适合想做企业 AI 落地、愿意带真实场景训练的人。」",
    "同行": "礼貌回应，不透露内部信息，不评论同行。",
    "无效": "可不回，或点个赞维持互动。",
}


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


async def run(cfg, acc):
    from playwright.async_api import async_playwright
    home = home_of(cfg)
    prof = profile_of(cfg, acc)
    os.makedirs(prof, exist_ok=True)
    outdir = os.path.join(home, "output", acc["slug"], "互动监测")
    os.makedirs(outdir, exist_ok=True)
    cap = []

    async with async_playwright() as p:
        ctx = await launch_persistent(p, 
            prof, headless=True,
            viewport={"width": 1440, "height": 940},
            args=["--disable-blink-features=AutomationControlled"])
        await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        pg = ctx.pages[0] if ctx.pages else await ctx.new_page()

        async def on_resp(resp):
            u = resp.url
            if "edith.xiaohongshu.com/api" not in u:
                return
            try:
                if "json" not in (resp.headers or {}).get("content-type", ""):
                    return
                cap.append({"url": u.split("?")[0], "data": await resp.json()})
            except Exception:
                pass

        pg.on("response", lambda r: asyncio.create_task(on_resp(r)))
        await pg.goto("https://www.xiaohongshu.com/notification",
                      wait_until="domcontentloaded", timeout=60000)
        await pg.wait_for_timeout(6500)
        if "/login" in pg.url:
            print("⚠️ 主站登录态失效，需要重新扫码登录：" )
            print("   python scripts/login.py --account %s --main" % acc["slug"])
            await ctx.close()
            return "NEED_LOGIN"
        try:
            await pg.get_by_text("消息", exact=True).first.click(timeout=6000)
            await pg.wait_for_timeout(5000)
        except Exception:
            pass
        await ctx.close()

    counts = {}
    for item in cap:
        u, d = item["url"], item["data"]
        dd = d.get("data") if isinstance(d, dict) else None
        if u.endswith("/unread_count") and isinstance(dd, dict):
            counts.update({"评论和@": dd.get("mentions", dd.get("unread_count", 0)),
                           "赞和收藏": dd.get("likes", 0),
                           "新增关注": dd.get("connections", 0)})
        if "get_unread" in u and isinstance(dd, dict):
            n = 0
            for k in ("user_chat_unread_counts", "group_chat_unread_counts"):
                v = dd.get(k) or {}
                if isinstance(v, dict):
                    n += sum(x for x in v.values() if isinstance(x, int))
            counts["私信"] = n

    state_path = os.path.join(outdir, "state.json")
    prev = {}
    if os.path.exists(state_path):
        try:
            prev = json.load(open(state_path, encoding="utf-8"))
        except Exception:
            prev = {}
    changes = {}
    for k, v in counts.items():
        old = (prev.get("counts") or {}).get(k, 0)
        if v != old:
            changes[k] = v - old

    ts = now_str()
    has_new = any(v > 0 for v in changes.values())
    lines = ["# 互动监测 · %s · %s" % (ts, acc["name"]), "",
             "| 项目 | 未读 | 变化 |", "|---|---|---|"]
    for k in ["评论和@", "私信", "赞和收藏", "新增关注"]:
        c = changes.get(k)
        lines.append("| %s | %s | %s |" % (k, counts.get(k, 0), ("+%s" % c) if c else "—"))
    if has_new:
        lines += ["", "## 有新增"]
        for k, c in changes.items():
            if c > 0:
                lines.append("- **%s** +%d" % (k, c))
    else:
        lines += ["", "无新增互动。"]
    open(os.path.join(outdir, "latest.md"), "w", encoding="utf-8").write("\n".join(lines))
    with open(os.path.join(outdir, "history.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": ts, "counts": counts, "changes": changes}, ensure_ascii=False) + "\n")
    json.dump({"time": ts, "counts": counts}, open(state_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("【互动监测 %s · %s】" % (ts, acc["name"]))
    for k in ["评论和@", "私信", "赞和收藏", "新增关注"]:
        c = changes.get(k)
        print("- %s: %s%s" % (k, counts.get(k, 0), ("(+%s)" % c) if c else ""))
    print("NEW" if has_new else "NONE")
    return "OK"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--config", default="")
    a = ap.parse_args()
    cfg, root = load_config(a.config)
    acc = find_account(cfg, a.account)
    asyncio.run(run(cfg, acc))


if __name__ == "__main__":
    main()
