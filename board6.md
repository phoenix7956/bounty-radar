# 赏金板子 2026-11-27（第 3 轮后）

## 可投（今天就要动）

| 金额 | 单 | 状态 | 说明 |
|---|---|---|---|
| $175 | Expensify/App#106035 | 可投（补丁已就绪） | 清空 Composer 刷新后草稿复现。指派者 Uzaifm127 11-18 报"马上做"但没开 PR，维护者已降级 Weekly。已有 4 个外部 proposal 同一根因。**补丁已在 245 那台 Windows 落地并提交**：分支 `fix/106035-cleared-composer-draft`，commit `03ca813`，3 文件 +34/-4，diff 逐字核对一致，未 push。根因：`useDebounce` 默认导出不暴露 cancel → `cancelSaveDraft` 形同虚设；清空草稿走 debounce 不会在卸载前落库 → 旧草稿复活；且挂起的那次写入不取消的话 1 秒后照样把旧文本写回去。proposal 稿见 proposal_106035.md，待用户拍板 posting。 |

## 已排除

| 金额 | 单 | 排除原因 |
|---|---|---|
| $175 | Expensify/App#106153 | assignee 在内部拆子 issue 推进中 |
| $175 | Expensify/App#105698 | 维护者明说无 Help Wanted 不要 proposal，内部 PR 在审 |
| $250 | Expensify/App#107895 | 已指派 JS00001/ikevin127/mukhrr，终审中 |
| $250 | Expensify/App#107177 | 已选定 proposal 并指派 lakchote |
| $250 | Expensify/App#100368 | 逾期 8 天但优先级已降、3 人已占 |
| $250 | Expensify/App#106793 | 一晚 20+ proposal，最凶 |
| $600 | UbiquityOS/text-conversation-rewards#301 | 机器人门禁只允许 collaborator，23 个外部 PR 全灭 |
| $200 | solved-conjectures#223 | 非 PR 单，钱挂在"解数学问题"上 |
| $250 | Expensify/App#105145 | 已有人提 proposal |

## 结构性事实

- Expensify 开放带价单 **201 条，assignees 无一为空** → 只能靠 proposal 被选中，剩下 25 条是"指派了但 7 天以上没动"的逾期单。
- 开放带价档位只有 $50 / $175 / $250 / $1000，$200/$300/$500 档当前无开放单。
- Expensify **只走 Upwork 打款**，且提交 proposal 前要贴 Contributor details（含 Upwork profile 链接）→ **没有 Upwork 账号就拿不到钱**。
- Opire 全平台公开单只有 3 条、合计 $162。

## 卡点（要人做）

1. **Upwork 账号**：Expensify 唯一的付款通道，需要注册 + 绑 PayPal（164069345@qq.com）。
2. **发 proposal 的授权**：草稿已好，贴到 #106035 是公开动作，要用户点头。
3. **245 上阿烛的桥接实例卡死**：连 ping 都超时（同一台机器的 win的marvis 正常）→ 需要在 Windows 上重启它。
4. **桥接 timeout 420 秒太紧**：Windows 端 Codex 启动开销就吃掉 3-4 分钟，任务必须拆到 3 分钟以内。
