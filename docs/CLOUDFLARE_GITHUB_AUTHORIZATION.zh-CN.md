# GitHub + Cloudflare 平台授权指南（PPF Reference）

**Reviewed:** 2026-09-24

目标是让未来新项目尽量不重复要求人类授权，同时把 Provider authority 控制在明确范围内。

PPF 现在区分两条受支持路线：

1. **Agent-Provisioned External CI** — 未来由 AI Agent 新建项目时的首选路线。
2. **Workers Builds Native** — 已有真实 pilot 证据的 provider-native 备选路线。

`cloudflare-builds.yaml` 继续是 PPF machine contract；Cloudflare 不会自动读取它。

## 1. 未来 Agent 自动新建项目的首选路线

```text
Human
  |
  +-- GitHub provisioning principal 一次授权
  |
  +-- Cloudflare provisioning principal 一次授权
          |
          v
      Project Provisioner
       /            \
 GitHub              Cloudflare
 private repo        all_workers baseline 检查
 workflow            Worker 创建
 repo secrets <---- trusted secret broker
       \             /
        GitHub Actions
             |
        wrangler deploy
```

本 Profile 不需要为每个新项目再次安装 Cloudflare GitHub App。

详见 [AGENT_PROVISIONED_EXTERNAL_CI.zh-CN.md](AGENT_PROVISIONED_EXTERNAL_CI.zh-CN.md)。

## 2. 一次性 GitHub 平台授权

使用边界清楚的 GitHub user account 或 organization scope。

Provisioning GitHub App 只申请实现真正需要的权限。典型 repository permission 包括：

```text
Administration: write
Contents: write
Workflows: write
Actions: write
Secrets: write
Pull requests: write
Metadata: read
```

实际权限必须根据实现的具体 API 操作复核，不能为了方便扩大。

Credential type 必须与 repository owner 匹配：

- personal user owner -> 使用 GitHub App user access token（或其他受支持的 user-authorized fine-grained token）调用 `POST /user/repos`；
- organization owner -> 可使用 GitHub App installation access token 或 user access token 调用 `POST /orgs/{org}/repos`。

Project infrastructure manifest 显式记录 `github.ownerType`；不要为了判断 user/org 而让 installation token 去调用不适用的 identity endpoint。

完成标准：

> Provisioner 能在已批准范围内创建和配置 private project repository，而不要求人类逐仓库重新授权。

不要为了方便授权无关 account。

## 3. 一次性 Cloudflare 平台授权

通过 API token、OAuth 或执行客户端支持的 Cloudflare 官方 MCP，建立一个 Cloudflare provisioning principal。

该平台身份可能需要检查 account / Worker inventory、读取 Access application、创建 Worker metadata、读取 deployment / observability state、在另有授权时修改 Access，以及只在明确得到 domain/DNS authority 时绑定域名。

新建 Worker 需要 Workers product-level Admin。日常 project deployment 不能继续使用这一广泛身份。

创建 **account-owned API token** 的 authority 更高：Cloudflare 当前 account-token API 对 token 创建/更新要求 Super Administrator authority。这项 authority 必须隔离在 trusted Secret Broker / provisioning service 内，不能授予 project CI 或语言模型面对的 Agent。

完成标准：

> Provisioner 能验证 account-wide Access baseline 并创建 Worker，而项目后续部署可以换成只限制到该 Worker 的凭据。

## 4. 新项目之前先建立 account-wide private baseline

在自动创建任何 project Worker 以前，配置并验证 destination 覆盖 `all_workers` 的 Cloudflare Access application，或等价的 account-wide baseline。

这是平台 bootstrap，不是某个项目的 public publication 决定。

Provisioner 如果不能确认未来 Worker 默认受保护，必须 fail closed。

不得为了让 Provisioning 更方便而自动创建 public bypass。

## 5. 项目专属 deployment credential

平台 Provisioner 创建 Worker 后，再创建 account-owned API token，并限制为：

```text
resource: individual Worker
role: Editor
```

这枚 token 是项目日常部署身份。

它不应拥有：

- 创建无关 Worker 的权限；
- 修改无关 Worker 的权限；
- 修改 account-wide Access 的权限；
- 除非部署契约真实需要，否则不拥有 zone/route 修改权限。

## 6. Secret Broker 是必需边界

项目 token 与 account ID 需要写入 GitHub Actions secrets，但 token 明文不得经过语言模型。

可执行 Provisioner 只返回非秘密 `secretBrokerRequest`。

Trusted broker 必须：

1. 创建 Cloudflare token；
2. token 明文只存在于 broker process 内；
3. 获取 GitHub repository public key，或使用 Provider 提供的安全 Secret 写入机制；
4. 写入 `CLOUDFLARE_API_TOKEN` 与 `CLOUDFLARE_ACCOUNT_ID`；
5. 丢弃明文；
6. 只把非秘密安装状态与 ID 返回给 Agent。

绝不要求使用者把该 token 粘贴进聊天。

## 7. 平台 bootstrap 后的 restricted deployment

两次平台授权已经存在后，未来新项目通常不应再要求额外账户级 consent。

Agent 可以：

- 创建 private GitHub repository；
- 初始化 PPF / Starter 项目；
- 创建 Worker；
- 调用 Secret Broker；
- 运行 GitHub Actions deployment；
- 验证匿名访问被 Cloudflare Access 拒绝；
- 把非秘密 Provider 状态写回项目。

Public release 仍然是独立的人类出版决定。

## 8. Workers Builds Native 备选路线

明确选择 provider-native Git integration 的项目仍可采用：

```text
AI Agent / operator
   |
   +--> Cloudflare
           |
           +--> Workers Builds
                    |
                    +--> Cloudflare GitHub App
                            |
                            +--> selected repository
```

这一路线需要 Cloudflare GitHub App authorization。

授权存在后，Provider API 可以在支持范围内继续管理 Workers Builds configuration、repository connection、trigger、build 与 monitoring。

Workers Builds 当前 build credential 仍采用 user-token 模型，不得描述成 one-Worker least privilege。

## 9. Cloudflare MCP

如果客户端支持 Cloudflare 官方 MCP，可用它建立或操作 Cloudflare provisioning principal。

相关官方入口包括：

```text
https://mcp.cloudflare.com/mcp
https://builds.mcp.cloudflare.com/mcp
```

MCP 不改变授权边界：登录/MFA 与 consent 仍由人完成；secret 仍不能进入聊天/model context。

## 10. Bootstrap 之后仍由人保留的 Gate

不能因为创建了一个新 repository 或 Worker，就机械地再次把工作交还给人类。

只有动作改变这些保留边界时才回到人类：

- public publication；
- 新增/扩大 reader audience；
- 新 canonical domain 或 DNS authority；
- 新 GitHub organization / App installation scope；
- 扩大 Cloudflare permission scope；
- paid-plan / billing change；
- 没有可信 Secret Broker 时的 secret direct input。

完整最小人类契约见 Starter 的 Project Provisioning Contract 与 Cloudflare handoff。
