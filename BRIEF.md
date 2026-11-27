# GitHub 赏金单作业书（给 Windows 上的 Codex 阿烛）

## 你要干的活

每天在 GitHub / Opire 上找**能真收到现金**的悬赏单，提 PR 领钱。
不是找热闹，是找**能被合并、能打钱**的单子。

## 工具

```bash
git clone https://github.com/phoenix7956/bounty-radar.git
cd bounty-radar
python3 radar.py            # 出今天的清单（board.md）
python3 radar.py --min 100  # 只看 >= $100
```

`radar.py` 吃两个源：Opire 公开 API + GitHub `label:bounty` 搜索。
它已经内置下面这些过滤，跑一次约 55 秒。

## 硬规则（都是上一轮踩出来的，别自己发明新标准）

1. **不接僵尸仓库** —— 45 天没 push 的 repo 直接跳过。
   上一轮在 `claude-builders-bounty` 上耗了 6 个月、5 个单子、$575 潜在收入，
   那个仓库 2026-03 之后就没人动过，PR 到 11 月被批量关掉，**一分钱没拿到**。
2. **不接灰色** —— 博彩、验证码破解、刷量、爬虫绕过、赌博。直接跳过，别犹豫。
3. **不接自家发币** —— MRG / XTR 这种项目内部代币，值钱的是币不是钱，不算收入。
4. **金额必须带货币标记** —— `$250` / `250 USDC` / `0.12 SOL` 才算；
   标题里的裸数字、日期里的 `2026` 一律忽略。
5. **优先现金通道** —— Upwork / PayPal / Stripe / Wise / 银行转账优先；
   只有 crypto 内币的单，除非金额很大否则不接。
6. **竞争 PR ≥ 5 的先别上** —— 除非金额过 $200 或那单很冷门。
7. **提 PR 前先读 CONTRIBUTING** —— 有的仓库明令禁止 AI 生成的 PR
   （Ghostty 直接封了 AI 贡献），先读再动手，别白干。
8. **先 claim 再提 PR** —— 在 issue 下评论 `I claim this bounty`，
   Algora 还要去 `/bounty $X` 那条评论下留痕。claim 帖要写清**你的方案**，
   不要只写 "I claim this bounty"。
9. **一次只做 1~2 单** —— 上一轮同时铺开 6 个单子，结果一个都没合。
   这轮宁可一周一单，也不要铺开。
10. **收款信息** —— 贴在 PR / claim 评论里（**私钥绝对不贴**）：
    - PayPal：`164069345@qq.com`（首选）
    - USDC（BNB Chain）：`0x4A4dBD326735C8b9722c3BDd0808FC2271bF8A90`
    - Opire 攒钱包 $1,000 → 走澳门开户那条线

## 我们的差异化（挑单的时候往这边靠）

**MLX / Apple Silicon / 本地推理 / Swift 桌面端 / 多媒体引擎**。
GitHub 上这类单几乎没人做 —— 满地都是 Python web 项目和 crypto 农场，
那边挤满了人和 agent，我们不要去挤。换到冷门方向才是我们的优势。

## 每次干完要回报的东西

在 OpenBot 对话里回报这 5 条，缺一条都算没交：

1. PR 链接
2. 金额 + 收款通道
3. claim 帖链接
4. 当前状态（等审 / 已合并 / 被关 / 已被抢）
5. 这单学到什么、下次怎么改选单

## 今天的板子（2026-11-27 跑出来的，供参考，别当成唯一目标）

| 金额 | 单 | repo | 竞争 | 收款 | 状态 |
|---|---|---|---|---|---|
| $200 | Paid mathematical problems with Lean | 179★ | 0 | Wise/USDC | 可接 |
| $250 | Expensify App · Android UI bug | 5108★ | 1 | Upwork 现金 | 已有人提 proposal |
| $200 | AncientBeast demo mode | 1893★ | 1 | XTR 内币 | 不值当 |
| $300 | microg Nearby Share | 15k★ | 5 | 未标 | 大活，别硬啃 |

**Opire 那边现在几乎是空的** —— 全平台只有 3 个开放单、合计 $162，
其中两个是测试仓库/灰色单。真正有量的在 GitHub 上。

## 一句话记住上一轮的教训

**输不在不会写代码，输在接了僵尸仓库的单。**
写代码有我们（和 agent）更快，选单得自己长眼。
