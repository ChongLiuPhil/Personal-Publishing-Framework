# Cloudflare ↔ GitHub 一次性授权指南（PPF Reference）

本指南面向没有技术背景的操作者。

目标不是让操作者学习 API、Wrangler 或 CI，而是只完成账户所有者必须亲自确认的授权动作。完成后，AI Agent 或项目维护者应根据仓库中的 `cloudflare-builds.yaml` 继续配置。

## 1. 推荐路线

```text
AI Agent
   |
   +--> Cloudflare OAuth / MCP      (如果客户端支持)

Cloudflare
   |
   +--> Workers Builds
            |
            +--> Cloudflare GitHub App
                    |
                    +--> selected repository only
```

Cloudflare API MCP：

`https://mcp.cloudflare.com/mcp`

Workers Builds MCP：

`https://builds.mcp.cloudflare.com/mcp`

`cloudflare-builds.yaml` 是 **PPF machine contract**。Cloudflare 不会自动读取它；AI 或人类需要把其中参数应用到 Cloudflare Workers Builds。

## 2. 授权 AI ↔ Cloudflare（可选但推荐）

如果 AI 客户端支持 MCP：

1. 打开 Plugins / Connectors / MCP / Integrations。
2. 添加 Cloudflare 官方 MCP。
3. 登录 Cloudflare。
4. 如果可以选择权限，只保留完成 Workers / Workers Builds 管理所需的权限。
5. 完成 OAuth 授权。

完成标准：

> AI Agent 能实际读取 Cloudflare account、Workers 或 Workers Builds 状态。

如果客户端不支持 Cloudflare MCP，不影响 PPF 使用；直接用 Dashboard fallback。

## 3. 授权 Cloudflare ↔ GitHub

1. 打开 Cloudflare Dashboard。
2. 进入 **Workers & Pages**。
3. 选择 **Create application → Import a repository**，或在已有 Worker 的 Builds 设置中连接 Git repository。
4. 选择 GitHub。
5. GitHub 显示 Cloudflare Workers & Pages App 授权页。
6. 如果可以选择 **All repositories** 或 **Only select repositories**，选择 **Only select repositories**。
7. 只选择当前项目需要的 repository。
8. 返回 Cloudflare。

完成标准：

> Cloudflare 能看到项目 repository，但没有获得不相关 repository 的访问权限。

### 完成这次一次性授权以后

人类应停止手工执行常规 build 配置。Cloudflare 当前 Workers Builds API 已支持在 GitHub App 授权存在后，程序化管理 repository connection、trigger、environment variable、build 执行与 build monitoring。

API Agent 使用 **user-scoped** token：

~~~text
Workers Builds Configuration: Edit
Workers Scripts: Read
~~~

前者管理 Builds/configuration，后者用于解析 Worker immutable tag。Token 只进入执行工具的 secure secret store，不进入 Git 或聊天。

Access application / policy 自动化使用另一枚最小权限 token：

~~~text
Access: Apps and Policies Write
~~~

只有 Agent 必须创建/修改 OTP 或 identity provider 时，再增加：

~~~text
Access: Organizations, Identity Providers, and Groups Write
~~~

Canonical 最小人类操作契约位于 Starter：
https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/CLOUDFLARE_MINIMAL_HUMAN_HANDOFF.zh-CN.md

## 4. “Set up your application” 页面

以下 UI 映射是 **2026-09-19 的 dated observation**，不是永久 Cloudflare 规范。完整映射与 UI drift 规则见：

`docs/CLOUDFLARE_OBSERVED_UI_MAPPING.zh-CN.md`

当前 Cloudflare 创建流程可能显示以下字段。

### Project name

填项目的 Worker / project name。

示例：

`epistemology-textbook`

### Build command

从 `cloudflare-builds.yaml` 复制。

PPF Quarto reference：

`bash scripts/cloudflare_build.sh`

不要留空，因为 PPF reference build 需要固定 Quarto + canonical Web gate。

### Deploy command

从 machine contract 复制。

PPF reference：

`npm run cloudflare:deploy`

它最终调用：

`wrangler deploy`

### Builds for non-production branches

PPF reference 建议：

**开启 / 勾选**

这样非 production branch 可以运行 preview build。

### Protect with Cloudflare Access

不要根据 repository public/private 来决定这一项。

先读取当前 publication contract：

~~~text
publication.web.authorization_state
publication.web.visibility
publication.web.access
~~~

Reference mapping：

- `visibility: public` + `access.mode: none`：通常保持公开；
- `visibility: restricted`：按项目 access policy 启用 Cloudflare Access；
- `visibility: private`：先确认项目定义的 private audience / route policy，再配置 Access 或保持公开 route disabled/staged。

Cloudflare current Workers documentation 还支持在创建后对单个 Worker、production+preview、或指定 hostname/path 配置 Access。因此创建页面中的 checkbox 不是 access policy 的唯一真值源。

具体 provider mapping 见：

`docs/CLOUDFLARE_ACCESS_PROFILE.zh-CN.md`

不要把 password、OTP、token 或其他 secret 写进 `publishing.yaml` 或聊天。

### Advanced settings → Non-production branch deploy command

PPF reference：

`npm run cloudflare:preview`

它最终调用：

`wrangler versions upload`

### Advanced settings → Path

如果项目从 repository 根目录构建：

`/`

如果是 monorepo，则应改成真正的项目目录。

### API token

Workers Builds 可以使用 Cloudflare 自动创建/选择的 **user build token**。

重要：

- 不复制 token secret；
- 不把 token 写入 Git；
- 不把 token 发到聊天；
- 不把 token 写入 `cloudflare-builds.yaml`。

当前 Cloudflare 产品对 Workers Builds 仍是 user-token 模型；详细安全 trade-off 见：

`docs/CLOUDFLARE_SECURITY_PROFILES.zh-CN.md`

### Variables

如果 machine contract 没有要求变量：

**留空。**

不要为了“看起来完整”随意创建变量或 secret。

## 5. Production branch 没有显示怎么办

创建页面不一定总会单独显示 production branch 字段。

如果没有显示：

1. 不要因此停止创建；
2. repository default branch 如果是 `main`，完成后检查 build / deployment 记录；
3. 确认 Cloudflare 的 build record 显示预期 branch；
4. 如果需要进一步确认，在 Worker 的 Builds 设置中查看 trigger / branch 配置。

不要为了找一个没显示的字段去改其他无关设置。

## 6. 第一次 Deploy 后验证什么

第一次成功后，不要立刻做 Custom Domain cutover。

先确认：

- Worker 存在；
- GitHub repository connection 生效；
- main build PASS；
- non-production preview PASS；
- workers.dev / preview URL 可以访问；
- repository-defined build command 实际执行；
- GitHub 原 production 仍然正常（如果正在迁移）。

只有这些都通过后，才进入 Custom Domain / canonical URL / legacy-site policy。

## 7. Token 安全与 production profile

Workers Builds 的自动 build token 适合最低人工成本的原生 Git integration，但当前默认权限比纯 static Worker 日常 deploy 所需更宽。

PPF 定义三种 Cloudflare security profile：

- **Profile A — Workers Builds Native**：原生、低人工成本、当前 reference default；
- **Profile B — Hardened External CI**：GitHub Actions + account-owned per-Worker Editor token；
- **Profile C — Future Native Granular**：未来 Workers Builds 支持 account-owned per-Worker token 后的理想组合。

详细说明：

`docs/CLOUDFLARE_SECURITY_PROFILES.zh-CN.md`

## 8. 在 preview 验证前不要做

- 不绑定正式 Custom Domain；
- 不改 DNS；
- 不关闭旧 production；
- 不修改 canonical URL；
- 不把 preview 当成正式 production cutover。

如果实际 Cloudflare UI 与本文档不同，不要猜。重新读取当前 provider UI、current official docs 与 repository machine contract，验证真实 build/runtime state，并把新观察反向更新到 dated Observed UI Mapping / runbook。
