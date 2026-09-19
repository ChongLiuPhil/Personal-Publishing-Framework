# Cloudflare Profile B：Hardened External CI

**PPF 状态：** 可选 hardened reference profile  
**默认：** 不启用自动部署

Profile B 用于明确要求 routine deployment credential 只能修改一个既有 Worker 的项目。

## 架构

```text
GitHub Actions
-> account-owned Cloudflare API token
-> one specified Worker
-> Editor
-> Wrangler
```

Cloudflare 当前 granular Workers permissions 支持把 account-owned token 限制到单个 Worker，并授予 `Editor`。对于既有 Worker 的 routine deploy，这比 Workers Builds 默认 user build token 的 scope 更窄。

## 模板文件

- `cloudflare-external-ci.yaml` — PPF machine contract
- `.github/workflows/cloudflare-external-ci.yml` — validate/manual deployment workflow

默认 PR 行为只执行：

`make cloudflare-build`

不会读取 Cloudflare secret，也不会 deploy。

只有 `workflow_dispatch` 手工选择 `preview` 或 `production` 时，才读取 credentials。

Production mode 还要求 workflow ref 必须是 `main`。

## 人类最少配置

只有项目真正选择 Profile B 时才做以下操作。

### Cloudflare

在 Cloudflare 的 **Manage Account → Account API Tokens** 创建 account-owned token。

目标权限：

- Scope：Specified Worker
- Worker：当前项目 Worker
- Role：Editor

不要为了 routine deployment 增加 KV、R2、D1、all-zone Workers Routes 或 Workers Admin。

### GitHub

在 repository：

**Settings → Secrets and variables → Actions**

添加：

Secret：

`CLOUDFLARE_API_TOKEN`

Variable：

`CLOUDFLARE_ACCOUNT_ID`

token secret 不进入 Git、不进入聊天、不进入 machine contract。

## 安全迁移顺序

1. 保留当前已验证 deployment path；
2. 合并 Profile B candidate；
3. candidate validate-only CI PASS；
4. 创建 scoped token + GitHub secret/variable；
5. 手工运行 preview；
6. preview PASS；
7. 手工运行 production；
8. production PASS；
9. 再关闭旧 deployment trigger；
10. 最后撤销旧 broad credential。

不要先拆旧链路再测试新链路。

## 与 Profile A 的关系

Profile A（Workers Builds Native）仍是低人工成本 reference default。

Profile B 不是“更高级所以所有人都必须用”，而是给明确要求 per-Worker least privilege 的项目使用。

如果未来 Workers Builds 支持 account-owned per-Worker token，应重新评估 Profile C。
