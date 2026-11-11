# -*- coding: utf-8 -*-
"""
草稿箱清理
小红书草稿存在浏览器本地（IndexedDB: draft-database-v1 / image-draft），
每次脚本发布都会自动留下一份，跑多了就会堆一大堆。

用法:
  python clean_drafts.py --account peter                    # 只看，不删
  python clean_drafts.py --account peter --title "标题" --keep 0   # 删掉该标题的所有草稿（发布成功后用）
  python clean_drafts.py --account peter --title "标题" --keep 1   # 同名只留最新一份
  python clean_drafts.py --account peter --dedupe           # 每个标题只留最新一份
"""
import argparse
import asyncio
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from xcfg import load_config, find_account, profile_of  # noqa
from browser_launch import launch_persistent  # noqa

READ_JS = """async () => {
    const db = await new Promise((ok, no) => { const r = indexedDB.open('draft-database-v1'); r.onsuccess = () => ok(r.result); r.onerror = () => no(r.error); });
    const st = db.transaction('image-draft', 'readonly').objectStore('image-draft');
    const all = await new Promise((ok) => { const q = st.getAll(); q.onsuccess = () => ok(q.result || []); q.onerror = () => ok([]); });
    return all.map(r => {
        const c = r.content || {};
        const ps = c.publishStore || {}, ds = c.draftStore || {}, as = c.articleStore || {};
        return { id: r.draftId, title: (ps.title || ds.title || as.title || '').trim(), ts: Number(r.timeStamp || 0) };
    });
}"""

DELETE_JS = """async (ids) => {
    const db = await new Promise((ok, no) => { const r = indexedDB.open('draft-database-v1'); r.onsuccess = () => ok(r.result); r.onerror = () => no(r.error); });
    const tx = db.transaction('image-draft', 'readwrite');
    const st = tx.objectStore('image-draft');
    let n = 0;
    for (const id of ids) { try { st.delete(id); n++; } catch (e) {} }
    await new Promise((ok) => { tx.oncomplete = ok; tx.onerror = ok; });
    return n;
}"""


async def run(cfg, acc, args):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        ctx = await launch_persistent(p, profile_of(cfg, acc), headless=True,
                                      viewport={"width": 1560, "height": 1000})
        pg = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await pg.goto("https://creator.xiaohongshu.com/publish/publish",
                      wait_until="domcontentloaded", timeout=60000)
        await pg.wait_for_timeout(6000)
        rows = await pg.evaluate(READ_JS)

        by_title = defaultdict(list)
        for r in rows:
            by_title[r["title"] or "(无标题)"].append(r)

        drop = []
        if args.title:
            wanted = args.title.strip()
            items = sorted(by_title.get(wanted, []), key=lambda r: r["ts"])
            keep_n = max(0, args.keep)
            drop = [r["id"] for r in items[:max(0, len(items) - keep_n)]] if keep_n < len(items) else []
        elif args.dedupe:
            for t, items in by_title.items():
                items = sorted(items, key=lambda r: r["ts"])
                if len(items) > max(1, args.keep):
                    drop += [r["id"] for r in items[:len(items) - max(1, args.keep)]]
        elif args.all:
            drop = [r["id"] for r in rows]

        print("草稿总数: %d" % len(rows))
        if args.verbose:
            for t, items in sorted(by_title.items(), key=lambda kv: -len(kv[1])):
                print("  %-28s %d" % (t[:28], len(items)))
        print("计划删除: %d" % len(drop))

        if drop and not args.dry_run:
            n = await pg.evaluate(DELETE_JS, drop)
            print("CLEANED %d" % n)
        else:
            print("DRY_RUN" if drop else "NOTHING_TO_DO")
        await ctx.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--keep", type=int, default=0)
    ap.add_argument("--dedupe", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--config", default="")
    a = ap.parse_args()
    cfg, _ = load_config(a.config)
    acc = find_account(cfg, a.account)
    asyncio.run(run(cfg, acc, a))


if __name__ == "__main__":
    main()
