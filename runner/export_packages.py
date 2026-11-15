# -*- coding: utf-8 -*-
"""
把发布包导出成「人工上传用」的文件夹
结构:
  <home>/待发布/<序号>_<日期>_<标题>/
      1_封面.png ... 6_结尾.png
      标题.txt / 正文.txt / 话题.txt / 置顶评论.txt
      复制这段.txt        ← 按顺序复制粘贴用
输出后直接把这个文件夹传到手机，用小红书 App 手动发。
"""
import glob
import io
import json
import os
import re

HOME = r"D:\下载\小红书分发"
OUT = os.path.join(HOME, "待发布")

NAME_MAP = {
    "_01_封面": "1_封面",
    "_02_问题": "2_问题",
    "_03_方法": "3_方法",
    "_04_判据": "4_判据",
    "_05_一句话": "5_一句话",
    "_06_领取": "6_结尾",
}


def safe(name):
    return re.sub(r'[\\/:*?"<>|]', "", name).strip()


def export_folder(folder, idx):
    pj = os.path.join(folder, "publish.json")
    if not os.path.exists(pj):
        return None
    d = json.load(io.open(pj, encoding="utf-8"))
    title = d.get("title", "")
    date = d.get("date", "")
    imgs = d.get("images") or []
    if not imgs:
        return None

    target = os.path.join(OUT, "%02d_%s_%s" % (idx, date, safe(title)[:24]))
    os.makedirs(target, exist_ok=True)

    # 图片：按顺序改名复制
    for i, name in enumerate(imgs, 1):
        src = os.path.join(folder, name)
        if not os.path.exists(src):
            continue
        ext = os.path.splitext(name)[1].lower()
        label = "封面" if i == 1 else ("结尾" if i == len(imgs) else "内页")
        dst = os.path.join(target, "%d_%s%s" % (i, label, ext))
        with open(src, "rb") as f, open(dst, "wb") as o:
            o.write(f.read())

    tags = d.get("tags") or []
    body = d.get("body", "")
    pinned = d.get("pinned_comment", "")

    def w(name, text):
        io.open(os.path.join(target, name), "w", encoding="utf-8", newline="\n").write(text)

    w("标题.txt", title)
    w("正文.txt", body)
    w("话题.txt", " ".join("#" + t for t in tags))
    w("置顶评论.txt", pinned)

    copy_block = []
    copy_block.append("【标题】\n" + title)
    copy_block.append("\n【正文】\n" + body)
    copy_block.append("\n【话题】\n" + " ".join("#" + t for t in tags))
    if pinned:
        copy_block.append("\n【发布后置顶评论】\n" + pinned)
    w("复制这段.txt", "\n".join(copy_block))

    w("怎么发.txt",
      "1. 手机打开小红书 → 发布 → 图文\n"
      "2. 依次选择本文件夹里的 6 张图（1_封面 必须是第一张）\n"
      "3. 复制「标题.txt」内容到标题栏\n"
      "4. 复制「正文.txt」内容到正文框\n"
      "5. 复制「话题.txt」内容追加到正文末尾\n"
      "6. 发布后，把自己发的「置顶评论.txt」内容发在自己的评论区并置顶\n"
      "\n注意：不要直接粘贴整段带格式的内容，逐段复制更稳。\n")
    return target, len(imgs)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default="", help="只导出指定发布包目录")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.day:
        folders = [a.day if os.path.isabs(a.day) else os.path.join(HOME, "output", "peter", a.day)]
    else:
        folders = sorted(glob.glob(os.path.join(HOME, "output", "peter", "*")))
    idx = 0
    done = []
    for folder in folders:
        idx += 1
        r = export_folder(folder, idx)
        if r:
            done.append(r)
    print("已导出 %d 个文件夹到：%s" % (len(done), OUT))
    for t, n in done:
        print("  %s（%d 张图）" % (os.path.basename(t), n))


if __name__ == "__main__":
    main()
