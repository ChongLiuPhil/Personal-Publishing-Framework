# 每项目 GitHub → Cloudflare 配置指南

**状态：** 个人 GitHub 项目新建后的默认接入流程  
**默认交付 Profile：** `workers-builds-native`  
**默认源仓库：** private GitHub repository  
**默认网页：** restricted / authenticated Cloudflare Worker  
**UI 复核日期：** 2026-09-25

本指南**不再假定账户级零人工 Provisioning 已经完成**。每个项目允许一次少量人工配置；该项目完成 bootstrap 后，正常的源文件 push 应自动构建并部署。

`agent-provisioned-external-ci` + Trusted Secret Broker 仍作为可选的高级强化/自动化方案保留，但不再是普通新项目的默认前置条件。

## 人工操作与 Write-Back 规则

如果项目采用完整 Starter 栈，人工配置状态由 `project-bootstrap-state.yaml` 与 AHICP Working Memory 持久记录。

Agent 在要求人类打开 Provider UI 前，必须先把对应步骤写成 `waiting-human`；人类返回后，Agent 先验证 actual Provider state，再把步骤写成 completed。

| 人工步骤 | 当前 UI 路径 | 完成证据 | Bootstrap State 写回 |
| --- | --- | --- | --- |
| 创建 private repo | GitHub → **+** → **New repository** | `ChongLiuPhil` 下目标 repo 存在、Private、工作默认分支为 `main` | `source.repository_state: verified-private` |
| 连接 / Import repo | Cloudflare → **Workers & Pages** → **Create application** → import existing Git repository | 目标 repo 已选中并创建/连接 Worker | `cloudflare.git_connection: verified` |
| 修复 Git repo access | Worker → **Settings > Builds** → **Git Repository > Manage** → GitHub App settings | 目标 private repo 可以被 Cloudflare 选择 | `human_steps.authorize_repository_access: completed` |
| 首次启用 Zero Trust（如需要） | Cloudflare → **Zero Trust** onboarding | Zero Trust organization 已存在 | `cloudflare.zero_trust: verified` |
| 保护 Worker | **Workers & Pages** → Worker → **Access** → **Protect this Worker behind Access** → **All traffic** | Access 显示启用，匿名请求被 challenge / deny | `cloudflare.access_state: verified-private` |
| 第一次部署验证 | Cloudflare build/deployment + Git revision 核验 | 预期 revision 已部署且保持 private | `cloudflare.first_deployment: verified` |
| 第二次 push 验证 | 对 `main` push 无害改动 | 自动新 build/deploy，且无需重新授权 | `cloudflare.second_push_auto_deploy: verified` |

Bootstrap State、Git 与聊天中都不得保存 password、token value、OAuth code、OTP、recovery code、private key、cookie 或 reader credential。

当前 UI 路径的官方参考：[GitHub 新建仓库](https://docs.github.com/zh/repositories/creating-and-managing-repositories/creating-a-new-repository)、[Cloudflare Git integration](https://developers.cloudflare.com/workers/ci-cd/builds/git-integration/)、[Cloudflare Worker Access](https://developers.cloudflare.com/workers/configuration/cloudflare-access/)。

## Private 项目 CI 成本默认

本接入流程采用 [CI_COST_POLICY.zh-CN.md](CI_COST_POLICY.zh-CN.md) 中的 `private-project-quota-saver`。

连接 Cloudflare 前保持：

- content-only 改动：不自动启动 GitHub Actions；
- 配置类 Pull Request：只运行一个轻量 contract check；
- push 到 `main`：不自动启动 GitHub Actions Web build；
- heavy Web / Cloudflare contract validation：手动；
- Cloudflare Workers Builds：唯一自动 production Web build；
- Cloudflare 非 production build 与 Preview：默认关闭。

Agent 必须先批量编辑并完成可用 preflight，再创建 PR / push。不得把 GitHub Actions 当作迭代调试器。

如果 private repository 的 Actions allowance 已耗尽，可选 GitHub heavy workflow 保持未运行；不要持续制造会被 blocked 的 workflow。普通 Web deployment 可以继续通过 Workers Builds。

## 1. 创建项目仓库

在个人 GitHub 账号下创建项目仓库。

当前 GitHub UI 的人工创建步骤：

1. 登录 GitHub。
2. 右上角选择 **+** → **New repository**。
3. **Owner** 选择 `ChongLiuPhil`。
4. Repository name 填写 `project-provisioning.yaml` 声明的准确项目仓库名。
5. **Visibility** 选择 **Private**。
6. 如果后续由 Agent / Starter 写入完整项目文件，除非项目已经另有决定，先不要勾选 README / .gitignore / license 初始化，避免产生不必要的初始 merge conflict。
7. 选择 **Create repository**。
8. 在仓库页确认准确 identity 为 `ChongLiuPhil/<repository>`，并显示 **Private**。
9. 项目文件 push 后，确认实际工作默认分支为 `main`。

当前体系默认：

```text
Owner: ChongLiuPhil
Visibility: Private
Default branch: main
```

验证后，把 `source.repository_state: verified-private` 与非秘密 repository URL 写回项目状态。不要记录 GitHub session credential。

然后把 Starter / PPF 项目文件写入该仓库，并先通过 repository contract 检查，再连接 Cloudflare。

## 2. 在 Cloudflare Workers Builds 连接 GitHub 仓库

进入 Cloudflare Dashboard：

1. 打开 **Workers & Pages**。
2. 选择 **Create application**。
3. 在 **Import a repository** 下选择 **Get started**。
4. 选择 GitHub 账号。如果这个 Git account 已经连接到 Cloudflare，直接复用；Cloudflare 当前文档明确说明，初次连接后的 Git account 可以继续用于未来项目。
5. 如果目标 private repository 还不可见，只为该 repository 批准或扩大 Cloudflare GitHub App 的 repository access；条件允许时优先 selected-repository access。已有 Git account connection 正常时，不要仅因为这是新项目就重复 OAuth。
6. 选择刚创建的 private 项目仓库。
7. 配置项目：
   - Worker / application name：必须与 `wrangler.jsonc` 中的 `name`（以及项目声明的 Cloudflare Worker target）完全一致
   - production branch：`main`
   - root directory：`/`
   - build command：`bash scripts/cloudflare_build.sh`
   - deploy command：`npx wrangler deploy`
   - 非 production branch build / preview：默认关闭
8. 选择 **Save and Deploy**。

如果看不到仓库：打开目标 Worker → **Settings > Builds**；在 **Git Repository** 下选择 **Manage**。GitHub 应打开 **Cloudflare Workers and Pages** App installation 设置；把 repository access 调整为包含这个准确的 private repository，保存后回到 Cloudflare 再次选择。该动作属于 repository-access 扩展，不意味着重建已经正常工作的 Git-account connection。Repository 可见后，把 repository-access 步骤写回 completed；不要保存 OAuth/session material。

默认 Profile 不需要把 Cloudflare API token 复制进仓库或聊天。Workers Builds 使用 Provider 管理的 build credential。

## 3. 把 Worker 设为私人访问

默认 Web 状态是 restricted。

Cloudflare Access 要求账户先启用 Zero Trust。如果这是第一个受保护 Worker，而账户尚未启用，进入 Cloudflare Dashboard → **Zero Trust** 完成一次 onboarding。如果项目政策是继续使用 Free plan，在接受任何 billing 变化以前先确认界面仍明确显示预期的 Free / $0 计划；如果实际界面要求付费升级或其他实质 billing 决定，停止并把决定交还人类。Zero Trust 启用后写回 `cloudflare.zero_trust: verified`。这个账户级前置条件后续项目可以复用，不是每项目授权。

Worker 创建后：

1. 打开 **Workers & Pages**。
2. 选择该 Worker。
3. 打开 **Access** 标签。
4. 选择 **Protect this Worker behind Access**。
5. 选择 **All traffic**，使 production 与 preview 都受保护。
6. 已有批准的 reusable authentication policy 时直接选择；只有账户还没有目标 policy 时才新建/配置。
7. Apply Access。

如果账户已经启用并验证了 **Protect all Workers**，可以跳过逐 Worker 的这一步。项目应记录实际采用的 Access 模式：

```text
worker-scoped-access
或
account-wide-access
```

private 项目不得为了方便而创建 public bypass。

## 4. 验证第一次部署

Cloudflare 显示 deployment success 还不够。

必须核验：

- GitHub repository 仍为 private；
- Worker 连接的是正确的 repository；
- Cloudflare Worker / application name 与 `wrangler.jsonc.name` 一致；
- production branch 为 `main`；
- 部署的是预期 source revision；
- 匿名访问会被 Cloudflare Access challenge / deny；
- 获准读者完成认证后可以正常访问；
- 直接访问静态 asset 不能绕过 Access；
- credential value 没有出现在 Git、Issue、PR 文本、日志或模型/聊天上下文。

只记录非秘密的 Provider ID、URL、状态和验证证据。

## 5. 验证以后真的自动

对源内容做一次无害改动并 push 到 `main`。

预期：

```text
Git push
-> Workers Builds 自动启动
-> 执行项目 build command
-> 执行 wrangler deploy
-> 新 revision 成为 production
-> Access 继续有效
```

第二次部署不应再要求使用者重新连接 Git account、重新授权 Cloudflare GitHub App，或重新连接同一个 repository。

这一项通过以后，该项目后续普通 source change 可以持续复用同一条连接。

## 6. 仍保留给人的决定

每项目 bootstrap 不授权：

- GitHub repository private → public；
- Web restricted → public；
- 新增或扩大 reader audience；
- 新建 custom domain 或改变 DNS；
- 扩大 Provider permission scope；
- 开启付费计划或发生 billing change。

这些仍必须由人明确决定。

## 7. 可选高级 External-CI Profile

确实需要 project-scoped Cloudflare Worker credential 的项目，可以显式选择：

```text
agent-provisioned-external-ci
```

该 Profile 使用 GitHub Actions、Trusted Secret Broker 与 scoped deployment credential。它的凭据隔离更强，但基础设施要求也更高，因此不作为普通新项目默认路线。

绝不能要求使用者把 deployment token 粘贴到聊天里。

## 8. 持久项目记忆 Write-Back

对完整 Starter / AHICP 项目，人类交接结束后不能只留一句聊天消息。

每个步骤验证后：

- 更新 `project-bootstrap-state.yaml`；
- blocker / next action 变化时更新 AHICP Task Plan / Current Focus；
- Bootstrap 有实质推进时在 Work Log 追加里程碑；
- Working Memory 与已验证 Bootstrap State 尚未同步时，`memory_writeback.last_sync` 保持 `pending`；
- 只有仓库记忆同步完成后才改为 `synchronized`。

Provider 已经工作但仓库记忆仍 stale 时，项目不算 operationally complete。

## 9. 完成状态

默认项目 bootstrap 完成时，应能真实报告：

```text
github_repository: private
cloudflare_git_connection: verified
workers_builds: verified
worker_access: verified-private
second_push_auto_deploy: verified
public_release: NOT AUTHORIZED
```

这是“每项目一次配置”的运行契约，不是账户级零人工 Provisioning 的声明。
