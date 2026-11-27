#!/usr/bin/env python3
"""Bounty Radar - 扫 GitHub / Opire 上的悬赏单，按能不能真收到钱排序.

用法:
    python3 radar.py
    python3 radar.py --min 50

筛选逻辑（踩过坑换来的，别删）:
    1. repo 僵尸过滤  - N 天没 push 的 repo 不接
    2. issue 热度过滤 - 没人回复的 issue 不接
    3. 竞争过滤      - 竞争 PR 太多说明抢不到
    4. 垃圾过滤      - 0 star + 空 body + 没人评论 = 测试仓库
    5. 灰色过滤      - 博彩/验证码/刷量不接
    6. 金额过滤      - 没标金额的排后面
"""

import argparse
import json
import re
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

GH = "gh"
OUR_SKILLS = {"python", "typescript", "javascript", "swift", "rust", "go"}
SKILL_HINTS = (
    "mlx", "apple", "macos", "onnx", "inference", "llm", "model", "quant",
    "video", "image", "audio", "music", "diffusion", "server", "sdk", "cli",
    "api", "agent", "mcp", "swiftui", "desktop",
)
GRAY_WORDS = (
    "hcaptcha", "recaptcha", "captcha", "casino", "gambl", "betting", "airdrop",
    "click farm", "bot farm", "proxy list", "vpn list",
)
SPAM_WORDS = ("usdt", "token reward", "presale", "telegram bot")
MONEY = re.compile(
    r"(\$|USDC|USD|EUR|SOL|RTC|OPRE|¥)\s*(\d{1,6}(?:\.\d{1,4})?)"
    r"|(\d{1,6}(?:\.\d{1,4})?)\s*(USDC|USD|EUR|SOL|RTC|OPRE)\b",
    re.I,
)


def gh(*args, default=None):
    """跑 gh，失败不炸。"""
    try:
        p = subprocess.run([GH, *args], capture_output=True, text=True, timeout=60)
        if p.returncode != 0:
            return default
        out = p.stdout.strip()
        if not out:
            return default
        return json.loads(out) if out[0] in "[{" else out
    except Exception:
        return default


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "bounty-radar"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception:
        return []


def days_ago(ts):
    if not ts:
        return 9999
    if isinstance(ts, str):
        try:
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
        except Exception:
            return 9999
    return (time.time() - float(ts)) / 86400


def parse_amount(text):
    """从标题/label 里抠金额。

    只认带货币标记的（$100 / 100 USDC / 0.12 SOL），裸数字一律不算 ——
    否则 issue 里的日期 2026-11-27 会被当成 2026 美元。
    """
    if not text:
        return 0.0
    best = 0.0
    for m in MONEY.finditer(text):
        if m.group(2) is not None:
            v = float(m.group(2))
            unit = (m.group(1) or "").upper()
        else:
            v = float(m.group(3))
            unit = (m.group(4) or "").upper()
        if v < 5 or v > 50000:
            continue
        if unit == "SOL":
            v *= 150
        elif unit == "RTC":
            v *= 0.01
        best = max(best, v)
    return best


def repo_meta(full_name):
    d = gh("api", "repos/" + full_name)
    if not isinstance(d, dict):
        return None
    return {
        "stars": d.get("stargazers_count", 0),
        "archived": d.get("archived", False),
        "pushed": d.get("pushed_at"),
        "created": d.get("created_at"),
        "desc": d.get("description") or "",
        "lang": d.get("language") or "",
    }


def competition(full_name, number):
    """这个 issue 上已经有多少个开着的 PR。"""
    q = "repo:" + full_name + " is:pr is:open " + chr(34) + str(number) + chr(34)
    d = gh("api", "-X", "GET", "search/issues", "-f", "q=" + q, "-f", "per_page=1")
    if isinstance(d, dict):
        return d.get("total_count", 0)
    return 0


def looks_gray(text):
    t = (text or "").lower()
    return any(w in t for w in GRAY_WORDS)


def looks_spam(text):
    t = (text or "").lower()
    return any(w in t for w in SPAM_WORDS)


def score(item):
    """金额 x 新鲜度 x 热度 / 竞争 x 技能加成."""
    fresh = max(0.15, 1.0 - item["issue_age"] / 30.0)
    heat = max(0.2, min(1.0, item["comments"] / 8.0))
    comp = 1.0 + item["competitors"] * 1.6
    skill = 1.25 if item["skill_match"] else 1.0
    rail = 1.3 if item.get("cash_rail") else 1.0
    taken = 0.4 if item.get("taken") else 1.0
    return item["amount"] * fresh * heat / comp * skill * rail * taken


def collect_github():
    """GitHub 上的悬赏单：label:bounty / Algora 的标签 / issue 里 /bounty $ 的评论。"""
    out = []
    queries = [
        "label:bounty is:open",
        'label:"Bounty" is:open',
        '"/bounty $" in:comments is:open',
        "label:reward is:open",
        'label:"💰" is:open',
        "bounty in:title is:open",
        '"reward" in:title is:open',
    ]
    seen = set()
    for q in queries:
        d = gh(
            "api", "-X", "GET", "search/issues",
            "-f", "q=" + q, "-f", "per_page=100",
            "-f", "sort=updated", "-f", "order=desc",
        )
        if not isinstance(d, dict):
            continue
        for it in d.get("items", []):
            if it.get("pull_request"):
                continue
            full = it.get("repository_url", "").split("repos/")[-1]
            num = it.get("number")
            if not full or not num or (full, num) in seen:
                continue
            seen.add((full, num))
            out.append({
                "source": "github",
                "repo": full,
                "number": num,
                "title": it.get("title", ""),
                "url": it.get("html_url", ""),
                "body": (it.get("body") or "")[:1500],
                "labels": [l.get("name", "") for l in (it.get("labels") or [])],
                "comments": it.get("comments", 0),
                "updated": it.get("updated_at"),
                "amount": 0.0,
                "langs": [],
            })
    return out


def bounty_marker(cand):
    """去 issue 评论里找金额标记。

    Algora 的金额写在 bot 评论里（/bounty $500），Opire 的在 bot 评论里
    （opire.dev 链接 + 金额）。标题里没有金额的，多半是这种。
    """
    comments = gh(
        "api", "repos/" + cand["repo"] + "/issues/" + str(cand["number"])
        + "/comments?per_page=100",
        default=[],
    )
    if not isinstance(comments, list):
        return 0.0, None, [], False
    best = 0.0
    ev = None
    rails = set()
    taken = False
    for c in comments:
        body = c.get("body") or ""
        low = body.lower()
        if "/bounty" in low or "opire.dev" in low:
            amt = parse_amount(body)
            if amt > best:
                best = amt
                ev = c.get("html_url")
        for rail in ("upwork", "paypal", "stripe", "wise", "bank transfer", "usdc", "usdt", "sol ", "token"):
            if rail in low:
                rails.add(rail.strip())
        if any(k in low for k in (
            "already assigned", "auto assignment to", "assigned to @",
            "i will be working on", "i'm working on", "working on this issue",
        )):
            taken = True
    return best, ev, sorted(rails), taken


CASH_RAILS = ("upwork", "paypal", "stripe", "wise", "bank transfer")


def collect_opire():
    """Opire 公开 API，能直接抓全平台在挂的单。"""
    out = []
    for r in fetch("https://api.opire.dev/rewards"):
        price = (r.get("pendingPrice") or {}).get("value", 0) / 100
        url = r.get("url", "")
        m = re.search(r"github\.com/([^/]+/[^/]+)/issues/(\d+)", url)
        repo, num = (m.group(1), m.group(2)) if m else ("", "")
        try:
            comp = len(r.get("claimerUsers") or []) + len(r.get("tryingUsers") or [])
        except Exception:
            comp = 0
        out.append({
            "source": "opire",
            "repo": repo,
            "number": num,
            "title": r.get("title", ""),
            "url": url,
            "body": "",
            "labels": [],
            "comments": comp,
            "updated": None,
            "created": r.get("createdAt"),
            "amount": price,
            "langs": r.get("programmingLanguages") or [],
        })
    return out


def enrich(cand, args):
    """补全候选单；不合格的直接丢掉。"""
    if not cand.get("repo"):
        return None
    meta = repo_meta(cand["repo"])
    if not meta or meta["archived"]:
        return None

    issue_age = days_ago(cand.get("updated") or cand.get("created"))
    repo_age = days_ago(meta["pushed"])
    repo_new = days_ago(meta["created"])
    blob = " ".join([
        cand["title"], cand.get("body") or "", " ".join(cand["labels"]), meta["desc"],
    ]).lower()

    if looks_gray(blob) or looks_spam(blob):
        return None

    amount = cand.get("amount") or parse_amount(
        " ".join([cand["title"]] + list(cand["labels"]))
    )
    ev = None
    rails = []
    taken = False
    if not amount:
        amount, ev, rails, taken = bounty_marker(cand)
    else:
        _, ev, rails, taken = bounty_marker(cand)
    if amount < args.min:
        return None
    if repo_age > args.repo_days:
        return None
    if issue_age > args.days:
        return None
    # 新建仓库（刷单农场）+ 0 star 的直接扔
    if cand.get("source") == "github" and (meta["stars"] < 3 or repo_new < 7):
        return None

    comp = competition(cand["repo"], cand["number"])
    if comp >= args.max_comp and amount < 200:
        return None
    if meta["stars"] == 0 and cand["comments"] <= 1 and not (cand.get("body") or "").strip():
        return None

    langs = set(cand.get("langs") or [])
    if meta["lang"]:
        langs.add(meta["lang"].lower())
    skill = bool(langs & OUR_SKILLS) or any(h in blob for h in SKILL_HINTS)

    item = dict(cand)
    item.update({
        "amount": amount,
        "evidence": ev,
        "rails": rails,
        "taken": taken,
        "cash_rail": bool([r for r in rails if r in CASH_RAILS]),
        "issue_age": issue_age,
        "repo_age": repo_age,
        "competitors": comp,
        "stars": meta["stars"],
        "desc": meta["desc"],
        "lang": meta["lang"],
        "skill_match": skill,
    })
    item["score"] = score(item)
    return item


def render(items):
    now = datetime.now(timezone.utc).astimezone()
    out = []
    out.append("# Bounty Radar - " + now.strftime("%Y-%m-%d %H:%M"))
    out.append("")
    out.append("候选 " + str(len(items)) + " 单，已按 金额 x 新鲜度 x 热度 / 竞争 排序")
    out.append("")
    if not items:
        out.append("> 今天没单子值得接。先歇着，或者自己开池子。")
        out.append("")
        return "\n".join(out)

    out.append("| # | 金额 | 单 | repo 活跃 | 竞争 | 匹配 | 收款 | 状态 | 链接 |")
    out.append("|---|-----:|---|---|---:|:---:|:---:|---|---|")
    for i, it in enumerate(items, 1):
        out.append(
            "| " + str(i)
            + " | $" + format(it["amount"], ".0f")
            + " | " + it["title"][:46]
            + " | " + format(it["repo_age"], ".0f") + "d 前 / "
            + format(it["issue_age"], ".0f") + "d | "
            + str(it["competitors"]) + " | "
            + ("Y" if it["skill_match"] else "-") + " | "
            + ("cash" if it.get("cash_rail") else ("token" if it.get("rails") else "-"))
            + " | " + ("已有人抢" if it.get("taken") else "可接") + " | ["
            + it["repo"] + "#" + str(it["number"]) + "](" + it["url"] + ") |"
        )
    out.append("")
    for i, it in enumerate(items[:8], 1):
        out.append("### " + str(i) + ". $" + format(it["amount"], ".0f") + " - " + it["title"])
        out.append(
            "- 仓库: `" + it["repo"] + "` stars " + str(it["stars"])
            + " - 语言 " + (it["lang"] or "?")
            + " - 最后 push " + format(it["repo_age"], ".0f") + " 天前"
        )
        out.append(
            "- issue " + format(it["issue_age"], ".0f") + " 天前有更新 - "
            + str(it["comments"]) + " 条评论 - "
            + str(it["competitors"]) + " 个竞争 PR"
        )
        if it.get("rails"):
            out.append("- 收款通道: " + ", ".join(it["rails"]) + ("（可现金）" if it.get("cash_rail") else ""))
        if it.get("evidence"):
            out.append("- 金额出处: " + it["evidence"])
        out.append("- 链接: " + it["url"])
        out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=float, default=20, help="最低金额（美元）")
    ap.add_argument("--days", type=int, default=21, help="issue 最多多少天没动静")
    ap.add_argument("--repo-days", type=int, default=45, help="repo 最多多少天没 push")
    ap.add_argument("--max-comp", type=int, default=8, help="竞争 PR 超过这个数就跳过")
    ap.add_argument("--rail", default="",
                    help="只要这些收款通道的（逗号分隔），例: paypal,usdc,upwork")
    ap.add_argument("--out", default="board.md")
    args = ap.parse_args()

    cands = collect_github() + collect_opire()
    # 同一个仓库挂几十个 bounty issue 的，多半是批量刷 label 的农场，整仓跳过
    per_repo = {}
    for c in cands:
        per_repo[c.get("repo", "")] = per_repo.get(c.get("repo", ""), 0) + 1
    farms = {r for r, n in per_repo.items() if n > 15}

    items = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(enrich, c, args) for c in cands if c.get("repo") not in farms]
        for f in futs:
            it = f.result()
            if it:
                items.append(it)
    items.sort(key=lambda x: x["score"], reverse=True)

    if args.rail:
        want = [r.strip().lower() for r in args.rail.split(",") if r.strip()]
        items = [it for it in items
                 if any(w in r.lower() for r in it.get("rails") or [] for w in want)]

    board = render(items)
    print(board)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(board + "\n")


if __name__ == "__main__":
    main()
