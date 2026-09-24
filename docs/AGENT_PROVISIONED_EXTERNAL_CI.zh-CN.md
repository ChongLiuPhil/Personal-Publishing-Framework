# Agent 自动配置 External CI Profile

**状态：** 已实现的参考 Profile；全新项目线上验收仍待完成  
**Profile id：** `agent-provisioned-external-ci`

当某个项目明确优先要求“尽量不重复人工操作 + 日常部署权限严格限制到单个 Worker”，并愿意维护额外基础设施时，本 Profile 是高级可选路径；普通个人账号新项目默认采用更简单的每项目 Workers Builds 配置。

它补充而不是删除原生 Workers Builds Profile。

## 1. 目标体验

平台完成一次性 bootstrap 后，人类只需把项目目标交给 Agent，常规基础设施工作应由 Agent 完成：

```text
项目请求
-> private GitHub 仓库
-> Stack / Template 采用
-> account-wide Access 前置检查
-> Cloudflare Worker 元数据
-> 项目专属部署凭据
-> GitHub Actions 部署
-> restricted 运行时验证
-> 非秘密状态持久写回
```

只有公开发布、新读者范围、新正式域名/DNS 权限、付费升级或扩大 Provider 权限时才重新回到人类。

## 2. 两次平台级授权

稳定状态只保留两条长期信任关系。

### GitHub Provisioning Principal

使用边界清楚的 GitHub account / organization scope。Provisioner GitHub App 只申请创建和维护项目所需权限；具体实现通常包括 Repository Administration write、Contents write、Workflows write、Actions write、Secrets write、Pull requests write 与 Metadata read。

Repository 创建方式取决于 owner type：
- **个人 user account** 的 authenticated-user repository creation endpoint 接受 GitHub App **user access token**（或其他受支持的 user-authorized fine-grained token），不接受 installation token；
- **organization** 的 repository creation endpoint 接受 GitHub App installation access token，也接受 user access token。

因此 manifest 显式记录 `github.ownerType`，平台 Provisioning Principal 必须与 owner type 匹配。

App/user authorization 属于平台级授权。在已经批准的 scope 内新增仓库，不应要求人类逐项目重新授权。

### Cloudflare Provisioning Principal

建立一个严格控制的平台凭据或 OAuth/MCP 授权，用于读取账户状态、验证 account-wide Access baseline、创建 Worker、读取 deployment / observability state，并只在另有授权时修改 Access。

**Token minting 是另一条高权限边界。** Cloudflare 当前 account-owned token API 对创建/更新 account-owned token 要求 Super Administrator authority。不得把这项 authority 交给普通 project Agent 或 CI credential；它只能隔离在 trusted Secret Broker / provisioning service 内。

新建 Worker 需要 Workers product-level Admin；日常项目部署不需要这一广泛权限。

## 3. Private-by-default Cloudflare 基线

Provisioner 创建任何项目 Worker 之前，必须确认 Cloudflare Access 已通过 `all_workers` destination 或等价机制保护整个账户的 Workers。

该基线覆盖现有和未来 Worker。无法验证时必须 fail closed。

公共项目应表现为对这条私有基线的明确、审核过的例外。生产站公开不能自动使 Preview 公开。

## 4. Worker 创建身份与部署身份分离

平台 Provisioner 可以使用 product-level Admin 创建 Worker。Worker 存在后，日常部署凭据应变为：

**Account-owned API token + Individual Worker scope + Editor role**

这个项目 token 可以更新和部署该 Worker，但不应拥有无关 Worker 的修改权限。

模板因此声明：

```yaml
deployment:
  provider: github-actions-cloudflare-workers
  securityProfile: agent-provisioned-external-ci
  credentialStrategy: project-scoped-account-token
  secretBroker: true
```

## 5. Secret Broker 边界

项目 token 的明文不得返回给语言模型，不得打印到日志，不得进入 Git，也不得写入公共项目状态。

Provisioner 只输出非秘密请求，例如：

```json
{
  "schema": "ppf/secret-broker-request/v1",
  "credential": {
    "scope": "individual-worker",
    "role": "Editor"
  },
  "target": {
    "provider": "github-actions",
    "secretNames": [
      "CLOUDFLARE_API_TOKEN",
      "CLOUDFLARE_ACCOUNT_ID"
    ]
  }
}
```

拥有隔离 token-minting authority 的 trusted tool/service 内部执行：

```text
Cloudflare 创建 token
-> 明文只存在于受信 broker 内
-> 加密写入 GitHub Actions Secret
-> 丢弃明文
```

模型只看到安装状态和非秘密 ID。

Reference Broker 编排现在已经在 `providers/infrastructure/secret_broker.py` 中可执行：它拒绝覆盖已有目标 Secret，验证 issuer adapter 返回的 minted scope；后续写入失败时，只回滚本 transaction 写入的 Secret，并 revoke 本轮新 mint 的 token；对可变 token buffer 做 best-effort wipe；只返回 `ppf/secret-broker-result/v1`。详见 [`TRUSTED_SECRET_BROKER.zh-CN.md`](TRUSTED_SECRET_BROKER.zh-CN.md)。

Cloudflare granular-token **issuer adapter** 仍是独立 live-acceptance 项。PPF 不会硬编码猜测出来的 “Specified Workers + Editor” policy-resource JSON；第一个已授权 pilot 必须 discovery 并验证当前 Provider API shape 后，才能冻结该 adapter。

## 6. 仓库部署 Workflow

参考模板包含 `.github/workflows/deploy-cloudflare.yml`。

它：

1. 仅在 `main` 或手动触发时运行；
2. 读取持久化 PPF publication contract；
3. Web 部署仍未授权或 disabled 时不部署；
4. 通过仓库自身 Web gate 构建；
5. 只用该仓库的 Cloudflare account/token secrets 执行 `wrangler deploy`。

新项目默认不开自动 Preview。只有受保护 Preview 已真实验证后才可启用。

## 7. 可执行 Provisioner

`providers/infrastructure/provisioning.py` 与现有 reconciliation 层共用同一个 `project.infrastructure.json` 真值源。

它执行或规划：

1. 验证 external-CI Profile；
2. 任何写操作前验证 account-wide Access；
3. GitHub 仓库不存在时以 private 创建；
4. Worker 不存在时创建 Worker 元数据；
5. 只读取 GitHub secret metadata，不读取 secret 值；
6. 两个部署 Secret 未安装时返回 `SECRET_BROKER_REQUIRED`；
7. 准备完成后返回 `READY_FOR_CI`。

Provisioner 不负责擅自公开发布，也不能绕过 publication gate。

## 8. 验证

restricted 项目不能因为 CI 成功就宣称完成。必须确认：

- GitHub 仓库仍为 private；
- account-wide Worker protection 仍存在；
- 线上 Worker revision 正确；
- 匿名访问生产站会被 challenge 或拒绝；
- 如果启用 Preview，匿名 Preview 也被 challenge 或拒绝；
- 静态资源不能绕过访问层；
- Git、日志、issue、PR 和 chat 中不存在部署 token；
- 回滚点已经记录。

公开发布继续使用独立 PPF publication gate，不能从“部署成功”推导出来。

## 9. Native Workers Builds 仍然支持

`workers-builds-native` 继续作为方便、Provider-native 的 Profile，并且本仓库已经拥有真实 pilot 证据。

当最少 Provider 配置比单 Worker 权限隔离更重要时仍可采用。Workers Builds 当前 build credential 仍采用 user-token 模型。

对明确选择高级 Agent Provisioning 的项目，external-CI 仍有优势，因为 Provisioner 可以先创建 Worker，再给该 Worker 安装精确范围的部署 token；但它不再是普通个人账号新项目的默认接入路线。

## 10. 当前证据边界

仓库实现与 CI 能证明契约内部一致。Project Provisioner 与原子 Secret Broker 编排已经实现并可测试，但 Cloudflare granular-token issuer adapter 仍需真实 Provider acceptance；这些证据仍不能证明“新建项目端到端线上路径”已经真实通过。

把本 Profile 从“已实现高级可选 Profile”升级为“production-accepted”之前，必须用一个全新项目完成：

```text
新 private repo
-> Worker 创建
-> secret broker
-> GitHub Actions deploy
-> restricted 匿名拒绝
-> revision 验证
-> durable state write-back
```

并记录准确 Provider 证据和回滚点。在该 pilot 完成前，不得把 Profile B 描述为已经 production-accepted。
