# Expensify/App#106035 · proposal 草稿（待用户点头后 posting）

**issue**: https://github.com/Expensify/App/issues/106035
**标题**: `[$175] Chat - Cleared Composer draft reappears after refresh`
**报价**: $175　**工期**: 3 个工作日

## 根因（阿烛逐行核对 main 分支确认，win的marvis 复核）

1. `src/pages/inbox/report/useDebouncedSaveDraft.ts:40-42`
   `cancelSaveDraft` 只置 `isSavePending.current = false`，**没有 cancel 定时器**。
   更深一层：内部用的默认导出 `useDebounce`（`src/hooks/useDebounce.ts`）**只返回 `.invoke`**，
   把 `useDebounceWithControls` 的 `cancel` 丢了 —— 所以现在的 cancel 形同虚设。
2. `src/pages/inbox/report/ReportActionCompose/ComposerWithSuggestions.tsx`
   - `onClear`（921 行）→ `updateComment('', true)` → 走 debounce 分支（543 行 `debouncedSaveComment`）
   - 同步分支本来就有（545 行 `saveReportDraftComment(reportID, ...)`），只是清空场景没走它
   - 1000ms 定时器还没跑就刷新 → IndexedDB 里是旧草稿 → 刷新后复现
   - 补充：`useDebounce` 默认导出只返回 `.invoke`，把 `useDebounceWithControls` 的 `cancel` 丢了，
     所以 `cancelSaveDraft` 只能清 flag、cancel 不到定时器
   - 补充：即使改成同步保存，**不**取消挂起的那次写入，它 1 秒后仍带着旧文本参数落库 → 旧草稿照样回来

## 修法（按现有代码写法，不新造轮子）

1. `useDebouncedSaveDraft.ts`：改用已导出的 `useDebounceWithControls`（返回 `{invoke, cancel}`），
   解构成 `{invoke: debouncedSaveDraft, cancel: cancelDebouncedSaveDraft}`，
   并在 `cancelSaveDraft` 里调用 `cancelDebouncedSaveDraft()`，让它真正取消挂起的保存。
2. `ComposerWithSuggestions.tsx`：解构出 `cancelSaveDraft: cancelSaveComment`；
   在 `updateComment` 里，当新内容为空时 —— 先 `cancelSaveComment()` 取消挂起写入，
   再同步 `saveReportDraftComment(reportID, '')`（走现成的同步分支，不新造写法）。

**补丁已在 245 那台 Windows 上落地，并提交到本地分支 `fix/106035-cleared-composer-draft`**
（3 个文件，+34/-4；diff 已用 base64 逐字核对一致）。

## 测试

`tests/unit/hooks/useDebouncedSaveDraft.test.ts` 新增回归用例
`cancelSaveDraft drops the pending debounced timer`：
挂起写入后调 `cancelSaveDraft`，`jest.getTimerCount()` 从 >0 变成 0（证明定时器被真正取消，
而不是只翻了 flag）。原有 #98580 的用例保留。

**本地没跑测试**：245 那台没有 `node_modules`，按规程不装依赖；由 Expensify CI 验证。

## 要贴到 issue 评论里的 proposal（英文，147 词）

> ## Proposal
>
> **Problem.** Clearing the Composer and refreshing within ~1s resurrects the previous draft: the debounced save never fires before the page tears down.
>
> **Root cause.** In `ComposerWithSuggestions.tsx`, `updateComment` routes the empty-string save through `debouncedSaveComment` (1000ms timer), so the empty draft is never committed before the page unloads and the stale IndexedDB draft reappears on reload. On top of that, `cancelSaveDraft` in `useDebouncedSaveDraft.ts` cannot cancel anything: the default `useDebounce` export only exposes `.invoke`, so the `cancel` of `useDebounceWithControls` is dropped, and a queued write of the old composer content can still land afterwards.
>
> **Plan.**
> 1. `useDebouncedSaveDraft.ts`: use `useDebounceWithControls` and destructure `{invoke, cancel}`; `cancelSaveDraft` now cancels the pending debounced write instead of only flipping a flag.
> 2. `ComposerWithSuggestions.tsx`: when the converted comment is empty, cancel the pending debounced write and then save the empty draft synchronously via `saveReportDraftComment(reportID, '')`.
>
> **Tests.** Regression test in `tests/unit/hooks/useDebouncedSaveDraft.test.ts`: after `cancelSaveDraft` the pending debounced timer is gone (`jest.getTimerCount() === 0`), so a stale draft can no longer land.
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
