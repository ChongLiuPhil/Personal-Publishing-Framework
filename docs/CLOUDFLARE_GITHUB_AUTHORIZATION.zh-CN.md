# Cloudflare ↔ GitHub 一次性授权指南（PPF 参考）

本指南面向没有技术背景的操作者。

目标不是让操作者学习 API、Wrangler 或 CI，而是只完成**账户所有者必须亲自确认的授权动作**。完成后，支持 Cloudflare MCP 的 AI Agent 应根据项目仓库中的机器契约继续配置。

## 推荐路线

PPF reference implementation 推荐：

```text
AI Agent
   |
   +--> Cloudflare OAuth / MCP
   |
Cloudflare account
   |
   +--> Workers Builds
            |
            +--> GitHub App
                    |
                    +--> selected repository only
```

Cloudflare 官方 API MCP：

`https://mcp.cloudflare.com/mcp`

Workers Builds MCP：

`https://builds.mcp.cloudflare.com/mcp`

项目中的 `cloudflare-builds.yaml` 是 **PPF machine contract**。它不是 Cloudflare 原生自动读取的配置文件；AI Agent 或人类操作者需要把里面的参数配置到 Cloudflare Workers Builds。

## 授权 1：让 AI Agent 连接 Cloudflare

如果你使用的 AI 客户端支持 MCP：

1. 打开该 AI 客户端的 Plugins / Connectors / MCP / Integrations 设置。
2. 添加 Cloudflare 官方 MCP。
3. 浏览器会打开 Cloudflare 登录与授权页面。
4. 登录你自己的 Cloudflare 账户。
5. 如果页面允许选择权限，只保留完成 Workers / Workers Builds 管理所需的权限；不要主动增加与项目无关的 DNS、R2、KV、D1 等权限。
6. 点击允许/授权。
7. 回到 AI 客户端。

完成标准：

> AI Agent 能实际读取你的 Cloudflare account、Workers 或 Workers Builds 状态。

如果你的 AI 客户端不支持 Cloudflare MCP，直接使用后面的 **Dashboard fallback**。

## 授权 2：让 Cloudflare 访问指定 GitHub repository

1. 打开 Cloudflare Dashboard。
2. 进入 Workers & Pages。
3. 创建 Worker 并选择 **Import a repository**，或者在已有 Worker 的 Builds 设置中选择连接 Git repository。
4. 选择 GitHub。
5. GitHub 会显示 Cloudflare Workers & Pages App 的授权页面。
6. 如果可以选择 **All repositories** 或 **Only select repositories**，请选择 **Only select repositories**。
7. 只勾选当前 PPF 项目需要的 repository。
8. 完成安装/授权并返回 Cloudflare。

完成标准：

> Cloudflare 能看到当前项目 repository，但没有获得不相关 repository 的访问权限。

## 两次授权完成以后

如果 AI Agent 已经能够调用 Cloudflare MCP，只需要告诉它：

> “Cloudflare OAuth 和 GitHub App 已授权，请按仓库中的 `cloudflare-builds.yaml` 完成 Workers Builds 配置与第一次 preview 验证。”

AI 应继续完成：

- 确认或创建 Worker；
- 核对 Git repository connection；
- 配置 production branch；
- 配置 build / deploy / preview deploy commands；
- 启用需要的 non-production branch builds；
- 触发第一次 build；
- 检查 build log；
- 验证 preview / workers.dev URL；
- 把真实状态写回项目的 readiness state。

## Dashboard fallback

如果 AI 客户端不能使用 Cloudflare MCP，可以直接在 Cloudflare Dashboard 配置。

从项目的 `cloudflare-builds.yaml` 复制这些字段：

- Worker name；
- GitHub repository；
- production branch；
- root directory；
- build command；
- deploy command；
- preview deploy command。

不要凭记忆重新输入，也不要自己改这些值。

## Token 安全

Workers Builds 会使用 Cloudflare 侧的部署凭据。项目模板的原则是：

- token 不进入 Git；
- token 不写入聊天；
- token 不写进 README；
- token 不写入 `cloudflare-builds.yaml`；
- GitHub App 尽量只授权 selected repositories；
- 如果使用自定义 token，权限应尽量收窄；
- 一次性 provisioning 权限与长期部署权限应分开。

## 在第一次 preview 验证前不要做

- 不绑定正式 Custom Domain；
- 不改 DNS；
- 不关闭旧 production；
- 不修改 canonical URL；
- 不把 preview 当成正式 production cutover。

如果实际界面与文档不同，不要猜。记录当前页面标题和可见选项，再交给 AI 或项目维护者判断。
