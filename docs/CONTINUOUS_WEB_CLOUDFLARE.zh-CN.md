# Continuous Web 与 Cloudflare — PPF 入口

本文件是 PPF 仓库内的 Cloudflare 工作入口。跨项目操作契约由 Starter 统一维护：

https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/CONTINUOUS_WEB_CLOUDFLARE.zh-CN.md

执行 Cloudflare 操作前，先读取共享契约，再读取 PPF 的 provider-specific runbook：

1. docs/CLOUDFLARE_GITHUB_AUTHORIZATION.md — 账户所有者与 GitHub App 的详细授权流程；
2. docs/CLOUDFLARE_SECURITY_PROFILES.md — 部署凭据 profile 与最小权限权衡；
3. docs/CLOUDFLARE_ACCESS_PROFILE.md — reader access 映射；
4. docs/CLOUDFLARE_OBSERVED_UI_MAPPING.md — 带日期的 Cloudflare UI 观察。

## Agent 要求

如果必须由人类操作，必须给出编号的操作者级步骤，包括准确 account/project/domain、当前 UI 路径、需要选择的非秘密值、秘密边界、完成证据、后续验证与回滚。

不得要求人类把密码、token、私钥、恢复码或其他秘密粘贴到聊天。若当前 Cloudflare UI 与已有 runbook 不同，应核对当前 UI 或官方文档，不得猜测。

对于任何新配置的原创/未发布 PPF 项目，安全默认姿态都是 private source + restricted Continuous Web + authenticated access-policy reference。从 restricted 转为 public 必须得到人类明确授权，并不要求源仓库同时公开。
