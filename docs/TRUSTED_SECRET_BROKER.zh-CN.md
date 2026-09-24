# Trusted Secret Broker 契约

**状态：** Broker 编排状态机已经可执行；Cloudflare granular-token policy adapter 仍待 live acceptance  
**Request Schema：** `ppf/secret-broker-request/v1`  
**Result Schema：** `ppf/secret-broker-result/v1`

在 `agent-provisioned-external-ci` Profile 中，Secret Broker 是唯一允许接触 project deployment token 明文的边界。

它不是 LLM prompt，也不是 project repository state。

## 1. 为什么需要这条边界

创建 account-owned Cloudflare token 本身是高权限平台操作；最后交给项目日常 CI 的凭据则应该非常窄：只允许一个已经存在的 Worker，角色为 `Editor`，足以执行常规 Wrangler deployment。

因此平台分成：

```text
高权限 token-minting authority
        |
        v
trusted Secret Broker
        |
        +--> project-scoped Worker Editor credential
        |
        +--> GitHub Actions encrypted secret store
```

Project Agent 只能收到非秘密 status / identifier。

## 2. 已实现的状态机

可执行编排位于：

`providers/infrastructure/secret_broker.py`

它接收 PPF Project Provisioner 输出的非秘密 Request，并要求受信环境注入两个 adapter：

- `WorkerTokenIssuer`
- `RepositorySecretWriter`

Broker 自身不会猜 Provider policy JSON。

### 成功路径

1. 校验 Request 与 plaintext-safety rule；
2. 确认两个目标 GitHub Secret 均不存在；
3. 让 trusted token issuer 为指定的既有 Worker 创建 account-owned `Editor` credential；
4. 如果 issuer 返回更宽或不匹配的 scope，则立即拒绝并 revoke；
5. 写入 `CLOUDFLARE_API_TOKEN`；
6. 写入 `CLOUDFLARE_ACCOUNT_ID`；
7. 回读 Secret metadata，确认两个名称都存在；
8. 只返回 `ppf/secret-broker-result/v1` 非秘密结果；
9. 对可变 token buffer 做 best-effort wipe。

### 失败路径

如果 token 已创建后 Secret 写入失败：

1. 只删除本轮 Broker 已写的 Secret；
2. revoke 本轮新建 Cloudflare token；
3. cleanup 全部完成则返回 `ROLLED_BACK`；
4. cleanup 未完全成功则返回 `ROLLBACK_INCOMPLETE` 与经过清洗的非秘密 rollback marker。

Broker 拒绝覆盖已有目标 Secret，从而避免 rollback 时误删先前 credential。

## 3. Request 安全规则

每个 Request 必须同时声明：

```text
plaintextMustNotEnterModelContext = true
plaintextMustNotEnterGit = true
discardPlaintextAfterEncryptedWrite = true
existingSecretsMustNotBeOverwritten = true
rollbackMustRevokeMintedToken = true
```

允许的目标 Secret 名称仅有：

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

## 4. Cloudflare Token Issuer Adapter

Issuer 运行在 trusted Broker boundary 内。

Cloudflare 当前官方文档已经确认：

- account-owned token 通过 `POST /accounts/{account_id}/tokens` 创建；
- 创建 token 需要 Account API Tokens write authority；
- 在 account role 层面，创建/更新 account-owned token 属于 Super Administrator capability；
- account-owned API token 已支持 individual-Worker permission；
- `Editor` 可以更新/部署既有 Worker，但不能创建或删除 Worker；
- Worker 必须先存在，之后才能授予 per-Worker role。

因此 issuer **必须**：

1. 从 PPF Provisioner 接收已经存在的 Worker ID/name；
2. discovery / validate 当前 Provider 的 permission-group 与 resource-selector 表示；
3. 只为指定 Worker mint account-owned `Editor` token；
4. 安装前验证返回的非秘密 token policy / identity；
5. token 明文只作为进程内 secret material 返回给 Broker；
6. 支持通过非秘密 token ID revoke。

### 不猜 Policy JSON

Cloudflare 公共文档确认了能力，但当前没有给出足够稳定、完整的“Specified Workers + Editor”新权限 Policy JSON 示例。

因此 PPF reference implementation **不会**硬编码推测出来的 resource selector。

第一个 live pilot 必须通过已经授权的 Provider interaction 捕获当前准确 API shape，确认它确实只命中指定 Worker，然后才实现/冻结 Cloudflare issuer adapter。

这是一项安全约束，不代表其余 Provisioning 模型没有实现。

## 5. GitHub Actions Secret Writer Adapter

GitHub REST API 要求先使用 repository public key 加密 Secret，再创建/更新 repository Secret。

具体 writer 必须：

1. 获取 repository Actions Secret public key；
2. 使用 libsodium sealed-box 语义加密；
3. 通过 repository Actions Secrets endpoint PUT encrypted value + key ID；
4. 验证时只暴露 Secret-name metadata；
5. 支持删除本轮 transaction 创建的 Secret。

Writer 不得读取或返回旧 Secret 明文。

普通 Project Agent 通常只需 Secret metadata read；真正 write authority 属于 trusted Broker identity。

## 6. Process Isolation

Production Broker **应**作为短生命周期隔离 process/service invocation 运行。

不得：

- 打印 Request credential；
- 打印可能包含 token 的 Provider response body；
- 持久保存 plaintext token；
- 把 plaintext 放入 exception message；
- 通过 model/tool output 暴露 token；
- 从 chat 接受 token 值。

Provider error 必须转成经过清洗的 error code。

## 7. Result Contract

允许返回的安全字段包括：

- installation status；
- repository；
- Worker 非秘密 ID；
- minted token 非秘密 ID；
- installed Secret name；
- Secret-metadata verification；
- rollback state 与经过清洗的 rollback error。

`plaintextReturned` 永远为 `false`。

## 8. 验收要求

Live new-project pilot 中 Secret Broker 部分只有在以下全部成立时才通过：

- mint token 以前 Worker 已存在；
- 实际 token 被验证为 individual-Worker `Editor`；
- 两个 GitHub Secret 安装成功，plaintext 未出现在 Agent output / log / Git；
- 该 credential 可以完成 deployment；
- credential 不能修改无关 Worker；
- 强制制造第二个 Secret 写入失败时，新 token 被 revoke，且只删除本 transaction 第一个已写 Secret；
- 对已经存在的 Secret 再运行时会 block，而不是覆盖。

在 Provider-specific issuer 通过 live acceptance 前，状态必须写成：

`secret_broker_orchestration: implemented`  
`cloudflare_granular_token_issuer: live-acceptance-pending`
