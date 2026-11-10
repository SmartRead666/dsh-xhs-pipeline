# -*- coding: utf-8 -*-
"""
小红书内容合规自检
用法：
  python compliance_check.py <内容JSON或publish.json>
  from compliance_check import check, format_report
规则来源：小红书《社区规范》《社区公约》处罚记录实测（诱导互动、站外导流、承诺收益、硬营销）
"""
import json
import os
import re
import sys

# (编号, 级别, 规则名, 正则, 修改建议)
RULES = [
    ("R1", "block", "诱导互动·评论换资源",
     r"评论[\u4e00-\u9fa5A-Za-z0-9【】\[\]「」\"']{0,16}(领取|领走|领一份|拿|获取|送|发给你|发你)",
     "删掉「评论关键词领资源」结构。改成纯讨论引导，例如「你手上项目卡在哪一步？」"),
    ("R2", "block", "诱导互动·关键词回复",
     r"(评论区|留言)[\u4e00-\u9fa5A-Za-z0-9【】\[\]「」\"']{0,12}(领取|领走|送|发你)",
     "不要用关键词换资源。送模板只能放置顶评论或私信，且不能要求回复特定词"),
    ("R3", "block", "诱导互动·关注/点赞/收藏换利益",
     r"(关注|点赞|收藏|点个赞|三连|转发)[\u4e00-\u9fa5]{0,10}(领取|领走|送|抽|解锁|获取)",
     "删除以关注/点赞/收藏为条件的资源交换"),
    ("R4", "block", "诱导互动·扣字暗号",
     r"(扣1|扣个1|评论区扣|回复[\"'「]?[0-9A-Za-z]{1,4}[\"'」]?(领|拿|送))",
     "删除扣字、暗号式互动"),
    ("R5", "block", "抽奖/福利噱头",
     r"(抽奖|随机抽|中奖|福利放送|免费领|0元领|白送|免费送)",
     "非官方活动的抽奖/送福利属于高风险，删除"),
    ("R6", "block", "承诺就业/接单/收入",
     r"(包就业|包分配|保证就业|保offer|接到单|接单月入|月入|年入|稳赚|躺赚|带你赚钱|保证收入|薪资翻倍)",
     "禁止承诺就业、接单与收入，改为能力与方法的描述"),
    ("R7", "block", "站外导流",
     r"(加微信|加我微信|微信[：:]|vx[：:]?|V信|薇信|公众号|二维码|扫码加|手机号|电话[：:]|QQ群|群号|链接在评论)",
     "小红书禁止站外导流，删除联系方式与二维码引导"),
    ("R8", "block", "硬营销·价格班期",
     r"(原价|优惠价|限时价|团报|开班|班期|报名费|价格[：:]|元/人|早鸟价|立减|折扣)",
     "非官方号不写价格、班期、团报信息，指向官方账号"),
    ("R9", "warn", "绝对化用语",
     r"(最好|最强|第一(?!版|步|次|条|层|周|天|件|行|阶段|格|个)|唯一|100%|全网最|绝对|史上最|顶级|天花板)",
     "删除绝对化用语，改为条件化表述（「在X前提下」）"),
    ("R10", "warn", "夸大效果",
     r"(必然|一定能|保证(能|会|有效|成功)|瞬间见效|立刻见效|三天见效|一周见效|几天搞定|稳赚)",
     "避免效果承诺，改为「通常」「在……前提下」"),
    ("R11", "warn", "引导去图片找资源",
     r"(配图|图片|图里|第[0-9一二三四五六]页)[^\n。]{0,20}(领取|领走|拿去|取走|获取|下载)",
     "不要引导用户去图片里领资源，这是判定违规的直接依据"),
    ("R12", "warn", "悬念式诱导",
     r"(评论区告诉你|答案在评论区|点赞过百|过[0-9]{2,}赞|解锁)",
     "删除悬念式诱导互动"),
    ("R13", "warn", "敏感行业承诺",
     r"(治疗|疗效|稳赚不赔|保本|收益率[0-9]|合规资质保证)",
     "医疗、金融类表述需回避"),
]

# 末页 CTA 专用：这里出现「评论+关键词+领取」是最容易直接判违规的结构
CTA_BAN = [
    (r"评论[^。\n]{0,12}(领取|领走|送|发你|获取|拿)", "末页不要写「评论换资源」，改成方法收束或行动建议"),
    (r"领取|领走", "末页不要写「领取/领走」，改成「直接对着项目走一遍」"),
    (r"关键词|暗号", "末页不要出现「关键词/暗号」，这是诱导互动的直接证据"),
    (r"私信领取|私信发你", "不要用私信换资源，可写「不方便公开的可以私信聊具体场景」"),
]


def scan(text, rules=None):
    hits = []
    for rid, level, name, pat, advice in (rules or RULES):
        for m in re.finditer(pat, text):
            s = max(0, m.start() - 10)
            hits.append({
                "id": rid, "level": level, "rule": name,
                "match": text[s:m.end() + 10].replace("\n", " "),
                "advice": advice,
            })
    return hits


def check(day):
    """day: 内容 JSON（含 post / cta）或 publish.json（含 title / body / pinned_comment）"""
    post = day.get("post") or {}
    title = post.get("title") or day.get("title") or ""
    body = post.get("body") or day.get("body") or ""
    pinned = post.get("pinned") or day.get("pinned_comment") or ""

    hits = []
    for label, text in (("标题", title), ("正文", body), ("置顶评论", pinned)):
        for h in scan(text):
            h["where"] = label
            hits.append(h)

    cta = day.get("cta") or {}
    if cta:
        cta_text = " ".join([str(cta.get(k, "")) for k in ("kicker", "lead", "hook", "note")]
                            + list(cta.get("title") or []))
        for pat, advice in CTA_BAN:
            for m in re.finditer(pat, cta_text):
                hits.append({"id": "R14", "level": "block", "rule": "末页 CTA 违规结构",
                             "where": "第6页", "match": cta_text[max(0, m.start() - 8):m.end() + 8],
                             "advice": advice})

    # 话题数量与正文长度
    tags = post.get("tags") or day.get("tags") or []
    if len(tags) > 10:
        hits.append({"id": "R15", "level": "warn", "rule": "话题过多", "where": "话题",
                     "match": "%d 个话题" % len(tags), "advice": "控制在 5-8 个，过多像营销号"})
    if len(body) > 1000:
        hits.append({"id": "R16", "level": "warn", "rule": "正文超长", "where": "正文",
                     "match": "%d 字" % len(body), "advice": "小红书正文上限 1000 字"})
    if len(title) > 20:
        hits.append({"id": "R17", "level": "warn", "rule": "标题超长", "where": "标题",
                     "match": "%d 字" % len(title), "advice": "标题建议 ≤20 字"})
    return hits


def format_report(hits):
    if not hits:
        return "合规自检：通过（0 处风险）"
    lines = ["合规自检：发现 %d 处风险" % len(hits)]
    for h in hits:
        lines.append("  [%s] %s @%s：…%s…" % (h["level"].upper(), h["rule"], h.get("where", ""), h["match"][:60]))
        lines.append("        建议：%s" % h["advice"])
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("用法: python compliance_check.py <内容JSON或publish.json>")
        return 2
    p = sys.argv[1]
    data = json.load(open(p, encoding="utf-8"))
    hits = check(data)
    print(format_report(hits))
    return 1 if any(h["level"] == "block" for h in hits) else 0


if __name__ == "__main__":
    sys.exit(main())
