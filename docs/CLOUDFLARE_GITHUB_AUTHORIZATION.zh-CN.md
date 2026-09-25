# GitHub + Cloudflare 授权指南（PPF Reference）

**Reviewed:** 2026-09-24

PPF 仍支持两条部署路线，但默认路线已经调整。

## 默认：每项目一次引导式 Workers Builds 配置

对于个人 GitHub 账号下的普通新项目，默认使用 **Workers Builds Native**。

允许少量、项目级的人类操作：

1. 创建或确认 private GitHub repository；
2. 把该 repository 连接到 Cloudflare Workers Builds；
3. 如果 GitHub 提示，为 Cloudflare Git integration 授权该 repository；
4. 给生成的 Worker 启用 Cloudflare Access；如果已验证的 account-wide Access 已经覆盖它，则无需重复；
5. 确认第一次 restricted deployment。

完成这次 bootstrap 后，production branch 的后续 push 应自动部署，不需要反复重新连接 GitHub 或 Cloudflare。

详见 [PER_PROJECT_GITHUB_CLOUDFLARE_SETUP.zh-CN.md](PER_PROJECT_GITHUB_CLOUDFLARE_SETUP.zh-CN.md)。

## 为什么改成默认路线

Cloudflare 把 Workers Builds 作为 GitHub / GitLab 用户的集成式 CI/CD 路线，并明确把它定位为配置较少的方案。Repository 连接到 Worker 后，可以在 push 时自动部署。

本仓库也已经有这条 Native 路线的真实 pilot 证据。

它的 credential least-privilege 不如 hardened External-CI Profile。Workers Builds 当前使用 Provider 管理的 user-token 模型。对于“每项目明确授权一次”的默认模式，我们接受这一限制。

## 个人 GitHub Repository 默认值

普通 downstream project 默认放在个人 GitHub 账号下。

参考默认值：

```text
owner: ChongLiuPhil
ownerType: user
repositoryVisibility: private
```

使用者可以先在 GitHub 手动创建 repository，再由 Agent 配置项目。体系不再要求先完成账户级自动建仓授权。

如果某个已授权 connector 能安全地创建 private repository，也可以代为创建；这属于优化，不是默认前置条件。

## Cloudflare Git 授权

Native 路线里，Cloudflare Git integration 就是部署连接。

Cloudflare 当前文档明确说明，Git account 初次连接后可以继续用于未来项目。因此，新项目在 Git account 已经连接时应直接复用，不要机械地重新 OAuth。

只有目标 repository 尚未建立 connection，或 Cloudflare GitHub App 还没有该 private repository 的访问权时，才需要人类批准或扩大 repository access，然后继续当前项目 connection。

这是允许存在的**每项目人工 Gate**，但它不等于每个项目都必须重新做一次 OAuth。

条件允许时优先只给 Cloudflare App 当前目标 repository 的权限。

## 私人 Web Access

新项目 Web 默认 restricted。

推荐项目级配置：

```text
Workers & Pages
-> 选择 Worker
-> Access
-> Protect this Worker behind Access
-> All traffic
-> 选择已批准认证策略
```

如果账户已经启用并验证 **Protect all Workers**，也可以直接复用。

Infrastructure manifest 可以记录：

```text
worker-scoped-access
account-wide-access
```

在匿名请求真实被 challenge / deny 以前，不得声称 Worker 已经 private。

## Project Bootstrap 之后的自动化

Repository connection 与 Access 已验证后，普通运行应是：

```text
source push 到 main
-> Workers Builds
-> project build
-> wrangler deploy
-> 验证目标 revision
```

必须再做一次测试 push，并确认无需重新连接 GitHub 或重新授权 Cloudflare，才能把项目标记为 operationally verified。

## Secret

Native 默认路线不要求使用者把 Cloudflare deployment token 放进 GitHub Actions，更不要求粘贴到聊天。

Credential 由 Provider 管理。

任何 Provider credential 都不得进入 Git、Issue、PR 描述、日志或模型上下文。

## 可选高级 Profile：Agent-Provisioned External CI

已有的 `agent-provisioned-external-ci` 继续保留，供确实需要更强 deployment-credential 隔离的项目显式选择。

该 Profile 使用：

- GitHub Actions；
- project-scoped account-owned Cloudflare token；
- Trusted Secret Broker 编排；
- individual-Worker Editor scope。

它是高级可选 Profile，不是默认项目接入路线。Cloudflare granular-token issuer 仍需完成 live Provider acceptance。

详见：

- [AGENT_PROVISIONED_EXTERNAL_CI.zh-CN.md](AGENT_PROVISIONED_EXTERNAL_CI.zh-CN.md)
- [TRUSTED_SECRET_BROKER.zh-CN.md](TRUSTED_SECRET_BROKER.zh-CN.md)

## 仍保留给人的 Gate

无论使用哪个 Profile，以下动作都必须继续由人明确决定：

- Web 公开发布；
- source repository 公开；
- 扩大 reader audience；
- custom domain / DNS 变化；
- 扩大 Provider permission scope；
- paid plan / billing 变化。

现在的实际目标不再是“以后每个项目完全零人工”。

实际目标是：

> **每个项目只做一次短而明确、可照着执行的 bootstrap；之后普通 push 自动部署。**
