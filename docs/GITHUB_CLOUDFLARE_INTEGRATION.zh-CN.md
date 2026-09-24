# GitHub–Cloudflare 基础设施集成

**Reviewed:** 2026-09-24

PPF 项目在 `project.infrastructure.json` 中声明基础设施期望状态；GitHub / Cloudflare API 响应与 HTTP probe 才是 actual state。Provider adapter 先读现状，planner 生成最小幂等协调计划，只有授权和 publication gate 通过后才允许写入。

新项目自动配置还必须读取 [AGENT_PROVISIONED_EXTERNAL_CI.zh-CN.md](AGENT_PROVISIONED_EXTERNAL_CI.zh-CN.md)；网页 Agent 使用 [WEB_AGENT_GITHUB_CLOUDFLARE_ONBOARDING.zh-CN.md](WEB_AGENT_GITHUB_CLOUDFLARE_ONBOARDING.zh-CN.md)。

## 可见性与安全默认值

Repository visibility 与 application visibility 始终分开。

新项目默认：

- private GitHub repository；
- account-wide Access 后面的 private/restricted Worker；
- 没有 public bypass；
- Preview 在受保护验收前默认关闭；
- 不配置 Custom Domain；
- 不启用付费服务；
- public release 前必须有明确人类授权。

`release.state: public` 只是期望状态，不构成批准。Repository 公开与 Website 公开使用两个独立 gate。

## 每项目引导式 bootstrap 与高级平台 Provisioning

默认运行模型现在是**每项目一次引导式 bootstrap**。

个人 GitHub 账号下的普通新项目：

1. 创建或确认 private repository；
2. 通过 Cloudflare 原生 Git integration 连接 Workers Builds；
3. 在 GitHub / Cloudflare 提示时为当前 repository 完成授权；
4. 给生成的 Worker 启用 Worker-scoped Cloudflare Access，或复用已经验证的 account-wide Access；
5. 验证第一次部署，并再做一次 push 证明后续自动部署。

这条路线明确允许每个项目一次短人工配置；不要求先建设账户级 Project Provisioner、Trusted Secret Broker 或 account-owned deployment token。

`agent-provisioned-external-ci` 仍保留为高级可选 Profile；项目明确选择时，仍可使用原有的平台 authority 分离、Provisioner、Secret Broker 与 scoped-token 设计。

Public release 在两条路线里都不属于默认授权。

操作者流程见 `docs/PER_PROJECT_GITHUB_CLOUDFLARE_SETUP.zh-CN.md`。

## 文件与命令

- `schema/project.infrastructure.schema.json` 定义基础设施 desired state。
- `templates/quarto-book/project.infrastructure.json` 是 private-by-default v2 示例。
- `schema/integration-state.schema.json` 定义非秘密 Provider 状态。
- `providers/infrastructure/manifest.py` 校验 desired state 与 security-profile invariant。
- `providers/infrastructure/plan.py` 生成只读 reconciliation plan。
- `providers/infrastructure/provisioning.py` 实现新项目 `plan / apply / verify-restricted` 状态机。
- `providers/infrastructure/github.py` 读取/创建 repository，并且只读取 Actions Secret metadata。
- `providers/infrastructure/cloudflare.py` 读取/创建 Worker metadata，并读取 Workers Builds / Access 状态。
- `providers/infrastructure/coordinator.py` 在 provisioning 后提供 `doctor / plan / apply / verify / rollback`。
- `providers/infrastructure/state.py` 在使用该 CLI 实现时只保存非秘密 ID / audit event。

示例：

```sh
python providers/infrastructure/manifest.py project.infrastructure.json
python -m providers.infrastructure.provisioning plan project.infrastructure.json
python -m providers.infrastructure.provisioning apply project.infrastructure.json
python -m providers.infrastructure.provisioning verify-restricted project.infrastructure.json --url https://example.workers.dev

python -m providers.infrastructure.coordinator doctor project.infrastructure.json
python -m providers.infrastructure.coordinator plan project.infrastructure.json
python -m providers.infrastructure.coordinator apply project.infrastructure.json
python -m providers.infrastructure.coordinator verify project.infrastructure.json
python -m providers.infrastructure.coordinator rollback project.infrastructure.json
```

## Credential 边界

Provider credential 只进入受保护执行环境或 Provider connection，绝不进入 repository 数据。

对于 `agent-provisioned-external-ci`，Provisioner **有意不创建也不返回**项目 token 值，只返回非秘密 `ppf/secret-broker-request/v1`。

Trusted broker 执行：

```text
创建 account-owned Cloudflare token
-> 限定 individual Worker / Editor
-> 加密写入 GitHub Actions Secret
-> 丢弃明文
```

语言模型只能看到状态和非秘密 ID。

GitHub adapter 可以列出 Secret **名称**判断 readiness，但从不读取 Secret 值。

## Provider 行为

### Cloudflare Access

private 项目可以采用两种经过验证的 Access 模式：

- `worker-scoped-access` —— 默认引导式配置，直接保护目标 Worker；
- `account-wide-access` —— 可选，一次保护账户中当前与未来 Workers。

Coordinator 与 reconciliation planner 会记录项目实际期望的模式。只有对应保护已经观察到、且匿名访问真实被 challenge / deny 后，才能声称 private readiness。

默认 Worker-scoped 模式下，如果 Worker 已存在但缺少 Worker-level Access，reconciliation 返回项目级 Access Gate，而不是强制要求账户级 bootstrap。

### Agent-Provisioned External CI

平台 Cloudflare principal 可用 Workers product-level Admin 创建 Worker metadata。日常 deployment 随后切换为只限制到该 Worker 的 account-owned `Editor` token。

Installable template 通过 GitHub Actions 执行 `wrangler deploy`。

### Workers Builds Native

Workers Builds Native 现在是普通新项目的**默认 Profile**。每个项目完成一次 repository connection 后，后续 push 由 Cloudflare 自动构建并部署。

Workers Builds 使用 immutable Worker tag、repository connection、trigger 与 Provider 管理的 user-token build credential。Worker name、Provider ID 与 secret 值必须分开。

不得把 Workers Builds build credential 描述成 one-Worker least privilege。默认引导式路线接受这一取舍，因为使用者会明确批准该项目连接。

### Agent-Provisioned External CI

平台 Cloudflare principal 可以使用 Workers product-level Admin 创建 Worker metadata；日常 deployment 再切换为只限制到该 Worker 的 account-owned `Editor` token。

Installable template 继续保留 GitHub Actions deployment workflow 供这个高级可选 Profile 使用，但它不再是默认项目接入路线。

## Human gate

默认路线明确允许每个项目一次短人工 bootstrap。

需要时返回人类完成：

- 创建/确认个人账号下的 private repository；
- 为该 repository 授权 Cloudflare Git integration；
- 启用 Worker-scoped Access 或选择已批准的 Access policy；
- 确认第一次 restricted deployment。

项目 bootstrap 完成以后，普通 push 不应再要求重新授权 GitHub / Cloudflare。

这些动作始终必须回到人类：

- public publication；
- source repository public / open-source transition；
- 扩大 reader audience；
- Custom Domain / DNS authority；
- 扩大 Provider permission scope；
- paid-plan / billing change；
- 高级 Profile 无法完成可信 secret transfer 时的 direct secret input。

## 验证

默认引导式项目部署完成必须同时满足：

- desired 与 actual repository / Worker identity 一致；
- repository 仍为 private；
- Cloudflare Git connection 指向正确 repository；
- production branch 正确；
- Worker-scoped Access（或已验证 account-wide Access）保护项目；
- 部署 revision 正确；
- 匿名访问 production 被拒绝或 challenge；
- 已启用 Preview 时匿名 Preview 也被拒绝 / challenge；
- direct asset 不能绕过 Access；
- 第二次 source push 能自动触发部署且无需重新授权；
- rollback / restore 证据已记录；
- Git、log、PR、issue 与 chat 中不存在 credential value。

Repository CI 与模拟测试不能替代真实项目 live verification。

## 当前实现边界

经过真实 pilot 验证的 Workers Builds Native 路线现在是默认接入 Profile，因为它已经有运行证据，而且 Cloudflare 原生 Git workflow 能减少每项目配置量。

Infrastructure schema 现在同时表达 Worker-scoped 与 account-wide Access；reference template 默认 `workers-builds-native`、private source、Worker-scoped Access，并在显式启用与保护之前关闭 preview。

External-CI 实现继续保留在 schema、可选 GitHub Actions workflow、provider adapter、Provisioner、reconciliation planner、原子 Secret Broker 编排、安全 Broker result schema 与测试中。其 Provider-specific Cloudflare granular-token issuer 仍是 live-acceptance-pending。



当前 Provider reference 于 2026-09-24 重新核对：

- Cloudflare Workers authorization/roles：<https://developers.cloudflare.com/workers/platform/authorization/>
- Cloudflare Workers Access：<https://developers.cloudflare.com/workers/configuration/cloudflare-access/>
- Cloudflare Workers Builds API：<https://developers.cloudflare.com/workers/ci-cd/builds/api-reference/>
- Cloudflare GitHub Actions deployment：<https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/>
- GitHub repository API：<https://docs.github.com/en/rest/repos/repos>
- GitHub Actions secrets API：<https://docs.github.com/en/rest/actions/secrets>
