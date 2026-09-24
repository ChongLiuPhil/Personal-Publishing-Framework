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

## Platform bootstrap 与 project provisioning 分离

低人工目标依赖“长期平台 authority”和“项目日常 deployment authority”分离。

### Platform bootstrap

在受限范围内一次授权：

- GitHub provisioning principal；
- Cloudflare provisioning principal；
- trusted secret broker；
- 覆盖 `all_workers` 的 Cloudflare Access baseline。

项目级 workflow 不得自行创建、关闭或放宽 account-wide Access baseline。

### Project provisioning

每个新项目中，Provisioner 可以：

1. 创建 private repository；
2. 验证 account-wide Access 后创建 Worker metadata；
3. 请求项目专属 Cloudflare token；
4. 由 trusted broker 把 deployment credential 写入 GitHub Actions secrets；
5. 让 repository CI 完成已授权部署；
6. 验证 restricted runtime 与 revision；
7. 只写回非秘密 provider state。

Public release 不属于这项 standing project-creation authority。

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

Account-level `all_workers` destination 可以保护现有和未来 Workers。Provisioner 无法验证该 baseline 时必须 fail closed。

生产站公开表现为明确例外，而不是删除 baseline。Preview 除非另行批准，否则继续受保护。

### Agent-Provisioned External CI

平台 Cloudflare principal 可用 Workers product-level Admin 创建 Worker metadata。日常 deployment 随后切换为只限制到该 Worker 的 account-owned `Editor` token。

Installable template 通过 GitHub Actions 执行 `wrangler deploy`。

### Workers Builds Native

Provider-native Profile 继续支持。Workers Builds 使用 immutable Worker tag、repository connection、trigger 与 user-token build credential。Worker name、Provider ID 与 secret 值必须分开。

不得把 Workers Builds build credential 描述成 one-Worker least privilege。

## Human gate

平台 bootstrap 已完成后，在已经批准范围内新增普通项目不应重复要求账户级 authorization。

这些情况才返回人类：

- 新 GitHub organization / App installation scope；
- 新 Cloudflare permission scope；
- 缺少 account-wide Access baseline；
- public publication；
- 扩大 reader audience；
- Custom Domain / DNS authority；
- paid-plan change；
- trusted broker 无法执行时的 direct secret input。

## 验证

Restricted deployment 完成必须同时满足：

- desired 与 actual repository / Worker identity 一致；
- repository 仍为 private；
- account-wide Access 继续启用；
- GitHub Actions deployment Secret metadata 已安装，但没有读取 Secret 值；
- 部署 revision 正确；
- 匿名访问 production 被拒绝或 challenge；
- 已启用 Preview 时匿名 Preview 也被拒绝/challenge；
- direct asset 不能绕过 Access；
- rollback 已记录；
- Git、log、PR、issue 与 chat 中不存在 credential value。

Repository CI 和模拟测试不能替代真实新项目 live acceptance。

## 当前实现边界

External-CI 实现现已进入 schema、Quarto template、GitHub Actions workflow、provider adapter、Provisioner、reconciliation planner、原子 Secret Broker 编排、安全 Broker result schema 与测试。Provider-specific Cloudflare granular-token issuer adapter 仍是 live-acceptance-pending，因为 PPF 不会硬编码未经验证的 Specified-Worker policy-resource encoding。

现有真实 pilot 证明的是 Workers Builds Native 路线。新的 External-CI 路线仍需一个全新项目端到端 pilot，之后才能标记为 production-accepted。

当前 Provider reference 于 2026-09-24 重新核对：

- Cloudflare Workers authorization/roles：<https://developers.cloudflare.com/workers/platform/authorization/>
- Cloudflare Workers Access：<https://developers.cloudflare.com/workers/configuration/cloudflare-access/>
- Cloudflare Workers Builds API：<https://developers.cloudflare.com/workers/ci-cd/builds/api-reference/>
- Cloudflare GitHub Actions deployment：<https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/>
- GitHub repository API：<https://docs.github.com/en/rest/repos/repos>
- GitHub Actions secrets API：<https://docs.github.com/en/rest/actions/secrets>
