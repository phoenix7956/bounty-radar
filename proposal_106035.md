# Expensify/App#106035 · proposal 草稿（待用户点头后 posting）

**issue**: https://github.com/Expensify/App/issues/106035
**标题**: `[$175] Chat - Cleared Composer draft reappears after refresh`
**报价**: $175　**工期**: 3 个工作日

## 根因（阿烛逐行核对 main 分支确认）

1. `src/pages/inbox/report/useDebouncedSaveDraft.ts:40-42`
   `cancelSaveDraft` 只置 `isSavePending.current = false`，**没有 cancel 定时器**。
   更深一层：内部用的默认导出 `useDebounce`（`src/hooks/useDebounce.ts`）**只返回 `.invoke`**，
   把 `useDebounceWithControls` 的 `cancel` 丢了 —— 所以现在的 cancel 形同虚设。
2. `src/pages/inbox/report/ReportActionCompose/ComposerWithSuggestions.tsx`
   - `onClear`（921 行）→ `updateComment('', true)` → 走 debounce 分支（543 行 `debouncedSaveComment`）
   - 同步分支本来就有（545 行 `saveReportDraftComment(reportID, ...)`），只是清空场景没走它
   - 1000ms 定时器还没跑就刷新 → IndexedDB 里是旧草稿 → 刷新后复现

## 修法（按现有代码写法，不新造轮子）

1. `useDebouncedSaveDraft.ts`：改用已导出的 `useDebounceWithControls`（返回 `{invoke, cancel}`），
   把 `cancel` 句柄挂进 `cancelSaveDraft`，让它真正取消挂起的保存。
2. `ComposerWithSuggestions.tsx`：清空草稿时走**同步**保存 —— 让 `onClear` 调 `updateComment('', false)`，
   或在 `updateComment` 里对空串强制同步，落到现成的 `saveReportDraftComment(reportID, '')`
   （`saveReportActionDraft` / `saveReportDraftComment` 已在 51 行 import）。

## 测试

`tests/unit/ReportActionComposeTest.ts`：
- 清空 composer 后立刻保存 → 落库的是空草稿
- 挂起的非空 debounce 保存被 cancel → 刷新后不复活

## 要贴到 issue 评论里的 proposal（英文，147 词）

> ## Proposal
>
> **Problem.** Clearing the Composer and refreshing within ~1s resurrects the previous draft: the debounced save never fires before the page tears down.
>
> **Root cause.** In `ComposerWithSuggestions.tsx`, `updateComment` routes the empty-string save through `debouncedSaveComment` (1000ms timer), and `cancelSaveDraft` in `useDebouncedSaveDraft.ts` only flips a flag — it never calls `debouncedSaveDraft.cancel()`. So the empty-draft `Onyx.merge` cannot commit in time, and the stale draft in IndexedDB reappears on reload.
>
> **Plan.**
> 1. `useDebouncedSaveDraft.ts`: `cancelSaveDraft` also invokes `debouncedSaveDraft.cancel()`.
> 2. `ComposerWithSuggestions.tsx`: when the converted comment is empty (or save is not debounced), cancel any pending debounced save, then call `saveReportDraftComment(reportID, '')` / `saveReportActionDraft(...)` synchronously.
>
> **Tests.** Unit test in `tests/unit/ReportActionComposeTest.ts`: clearing the composer immediately triggers a committed empty draft; a pending non-empty debounced save is cancelled and cannot resurrect after reload.
>
> **Quote & timeline.** $175, 3 business days to PR.

## 风险

- **同根因已有 4 个外部 proposal**（vanshshah11 / jeffrey-graham / zaidrain06 / TassioSales），
  我们不是第一个，赢面靠速度。
- 前序单 #85907（`[$250] Chat - Emojis pasted from Slack render as images`）仍 open，
  其 follow-up PR #106943 正在评审 —— 那边如果先合，这单就作废。**投之前再扫一眼 #85907。**
- assignee Uzaifm127 11-18 已说"马上开工"，维护者同日把优先级降到 `Weekly`。
  要投就当天投，别拖。
- 提交 proposal 前要贴 Contributor details（含 Expensify 邮箱 + **Upwork profile 链接**）。

## 前置条件

1. **Upwork 账号** —— Expensify 唯一的付款通道，缺它拿不到钱（也能影响 proposal 是否被受理）。
2. **用哪个 GitHub 账号发** —— 当前可用 `phoenix7956`。
3. CLA 随 PR 签，不前置。
