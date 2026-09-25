# 每项目 GitHub → Cloudflare 配置指南

**状态：** 个人 GitHub 项目新建后的默认接入流程  
**默认交付 Profile：** `workers-builds-native`  
**默认源仓库：** private GitHub repository  
**默认网页：** restricted / authenticated Cloudflare Worker

本指南**不再假定账户级零人工 Provisioning 已经完成**。每个项目允许一次少量人工配置；该项目完成 bootstrap 后，正常的源文件 push 应自动构建并部署。

`agent-provisioned-external-ci` + Trusted Secret Broker 仍作为可选的高级强化/自动化方案保留，但不再是普通新项目的默认前置条件。

## 1. 创建项目仓库

在个人 GitHub 账号下创建项目仓库。

当前体系默认：

```text
Owner: ChongLiuPhil
Visibility: Private
Default branch: main
```

仓库可以由使用者在 GitHub 界面手动创建，也可以由已经获得授权的 Agent / connector 创建。关键约束是：**新项目起始状态必须 private**。

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
   - production branch：`main`
   - root directory：`/`
   - build command：`bash scripts/cloudflare_build.sh`
   - deploy command：`npx wrangler deploy`
   - 非 production branch build / preview：默认关闭
8. 选择 **Save and Deploy**。

如果看不到仓库，可在 Worker 的 **Settings > Builds > Git Repository > Manage** 管理 Cloudflare Git installation，或者去 GitHub 的 Installed GitHub Apps 设置，为 Cloudflare App 增加该仓库访问权，然后重试。这属于 repository access 扩展，不意味着需要重建已经正常工作的 Git-account connection。

默认 Profile 不需要把 Cloudflare API token 复制进仓库或聊天。Workers Builds 使用 Provider 管理的 build credential。

## 3. 把 Worker 设为私人访问

默认 Web 状态是 restricted。

Worker 创建后：

1. 打开 **Workers & Pages**。
2. 选择该 Worker。
3. 打开 **Access** 标签。
4. 选择 **Protect this Worker behind Access**。
5. 选择 **All traffic**，使 production 与 preview 都受保护。
6. 选择或创建已经批准的认证策略。
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

## 8. 完成状态

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
