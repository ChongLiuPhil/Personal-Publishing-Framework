# 私有项目 CI 成本策略

**状态：** private downstream 项目的权威参考策略  
**Profile：** `private-project-quota-saver`  
**Reviewed：** 2026-09-25

本策略的目的，是避免 AI Agent 在 private repository 中把 GitHub Actions 当成反复试错环境。Private GitHub-hosted Actions 会消耗 repository owner 的月度 Actions allowance；标准 GitHub-hosted runner 在 public repository 中不消耗这份 private-repository allowance。Cloudflare Workers Builds 使用另一套独立的 build-minute 配额。

普通 private 研究/出版项目默认采用：

```text
Agent-side preflight
-> 可选轻量 GitHub PR contract check
-> merge 到 main
-> Cloudflare Workers Builds
-> restricted deployment
```

本 Profile 不把 GitHub Actions 当作默认 Web build/deploy provider。

## 1. 当前 Provider 配额背景

截至 reviewed 日期：

- GitHub Free 的 private repository 每月包含 2,000 GitHub Actions 分钟，并包含 500 MB Actions artifact storage（与 GitHub Packages storage 共享）；
- public repository 使用标准 GitHub-hosted runner 当前免费；larger runner 仍会计费；
- Cloudflare Workers Builds Free 当前包含每月 3,000 build minutes。

Provider 限制可能变化。涉及付费或 quota-sensitive 决策前必须重新查阅当前官方文档。

参考：

- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://developers.cloudflare.com/workers/ci-cd/builds/limits-and-pricing/

## 2. Agent 规则：禁止用 Actions 做迭代调试器

Agent **不得**使用“改一点 → push → Actions → 再改一点”的方式调试。

推荐状态机：

```text
EDIT
-> EDIT
-> EDIT
-> AGENT PREFLIGHT
-> COMPLETE DIFF REVIEW
-> ONE PR / PUSH
-> CI
```

CI 失败时：

```text
读完整失败
-> 一次识别相关问题
-> 批量修复
-> Agent-side preflight
-> 一次 retry
```

不得只修第一个错误就立刻再次 push。

## 3. Private 项目自动 GitHub Actions

Installable Quarto template 只保留一条自动 runner 路径：

`.github/workflows/project-check.yml`

而且只有**目标分支为 `main`**、并修改这些基础设施/配置文件的 PR 才运行：

- `_quarto.yml`；
- `publishing.yaml`；
- `cloudflare-builds.yaml`；
- `ci-cost-policy.yaml`；
- `project.infrastructure.json`；
- Wrangler / package / toolchain；
- Makefile / scripts；
- GitHub workflow；
- template manifest。

正文、manuscript、普通 chapter、reference、note 等 content-only 改动不会启动该 workflow。

这个轻量 workflow：

- 只有一个 Ubuntu job；
- hard timeout 为 5 分钟；
- 只跑 contract check；
- 不安装 Quarto、Chromium、Wrangler、Node dependencies 或 TeX；
- 使用 `cancel-in-progress: true`，同一 PR 新 revision 会取消旧的轻量 run。

## 4. Main push 不再自动跑 GitHub Web Build

默认 Native Profile 中，push 到 `main` 不启动 GitHub Actions Web build/deployment。

Production Web build 由 Cloudflare Workers Builds 负责：

```text
main push
-> Cloudflare Workers Builds
-> bash scripts/cloudflare_build.sh
-> make web-publish-check
-> wrangler deploy
```

因此同一个 Web artifact 不会先在 GitHub build 一次，再在 Cloudflare 重复 build 一次。

## 5. Heavy Workflow 全部按需手动

以下 workflow 默认只通过 `workflow_dispatch`：

- `.github/workflows/web.yml`：完整 Web validation；
- `.github/workflows/cloudflare-contract-ci.yml`：锁定 Wrangler / Cloudflare contract validation；
- `.github/workflows/build-publication.yml`：明确请求 EPUB/PDF/DOCX/LaTeX；
- `.github/workflows/deploy-cloudflare.yml`：只供高级 External-CI Profile。

建议只有这些情况才跑 heavy validation：

- publishing contract 改动；
- Cloudflare integration/config 改动；
- workflow/toolchain 改动；
- framework upgrade；
- public-release preparation；
- Agent-side check 无法定位的问题。

普通 manuscript / content 修改不是充分理由。

## 6. Preview / 非 Production Build

Cloudflare Workers Builds 默认保持：

```text
production branch: main
non-production branch builds: disabled
previews: disabled
```

只有项目明确需要并接受对应成本/访问行为时才启用。

这样 Agent feature branch push 不会消耗另一套 Cloudflare build-minute 配额。

## 7. Retry 规则

GitHub Actions：

- 优先 rerun failed job / failed workflow；
- 不能因为一个 job 失败就重跑已经成功的重型 job；
- superseded light PR run 应取消；
- 没有改变底层状态前不要连续 retry。

Cloudflare Builds：

- 不要为了 retry 制造无意义 commit；
- 先理解 failure 原因，再使用 Provider retry/rebuild；
- 一个 source change 正常应只对应一个 production build。

## 8. Artifact 策略

自动 workflow 不上传成功 artifact。

手动 publication artifact 默认只保留 **1 天**。

Downstream 如增加 diagnostic artifact，应：

- 只在 failure 时上传；
- 使用尽可能短的 retention，通常 1 天；
- 不包含 secret 或 Provider private state。

## 9. GitHub Actions 月度配额耗尽时

Private Actions allowance 已用完时：

1. 不要继续用会被 blocked 的 workflow 做 Agent 迭代；
2. 继续 Agent-side validation 和不依赖 GitHub-hosted runner 的 repository 工作；
3. ordinary production Web 继续走 Cloudflare Workers Builds；
4. 可选/手动 GitHub heavy validation 延后到 quota reset，除非使用者明确接受付费 usage；
5. 不自动添加 payment method、提高 budget 或升级套餐。

## 10. CI Profile 分层

Stack 使用三种明确区分的 CI / 成本层，而不是把同一套 workflow 复制到所有仓库：

- 普通 private downstream project：`workers-builds-native` + `private-project-quota-saver`；
- hardened External-CI project：`agent-provisioned-external-ci` + `external-ci-required`；
- public framework repository：`full-validation`（本 Stack 的 full-CI 等价 Profile）。

高级 External-CI Profile 继续保留；节省配额不会删除其 Trusted Secret Broker 或 least-privilege credential model。

## 11. Public Framework Repository

AHICP、PPF、Vault Interface、Starter 是 public framework repo，当前标准 GitHub-hosted runner 免费，因此可以保留更完整的 CI。

不要把 public framework 的完整 CI footprint 原样复制给 private downstream project。

框架仓库负责把可复用机制测透；private downstream 只保留薄验证层。

## 12. Machine Contract

Installable template 用：

`ci-cost-policy.yaml`

记录本策略；`project.infrastructure.json` 记录：

```json
"ciCostProfile": "private-project-quota-saver"
```

如果某个 private 项目明确愿意承担更高 GitHub Actions 成本，可以显式选择 `full-validation`；Agent 不得自行推断。

高级 `agent-provisioned-external-ci` 路线使用：

```text
ciCostProfile: external-ci-required
```

因为 GitHub Actions 是该 Profile 的 deployment architecture 一部分。
