# Agent 协作契约

在配置或发布项目之前，先阅读：

1. [`docs/ECOSYSTEM.zh-CN.md`](docs/ECOSYSTEM.zh-CN.md)
2. [`ecosystem.yaml`](ecosystem.yaml)
3. [统一跨仓库 Agent 调取契约](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/AGENT_RETRIEVAL_CONTRACT.zh-CN.md)
4. 涉及 Continuous Web 或 Cloudflare 时，先阅读 [`docs/CONTINUOUS_WEB_CLOUDFLARE.zh-CN.md`](docs/CONTINUOUS_WEB_CLOUDFLARE.zh-CN.md) 与 Starter 最小人类/Work 交接，再读取适用的 PPF provider-specific runbook
5. 面对**新项目**时，读取 [`docs/AGENT_PROVISIONED_EXTERNAL_CI.zh-CN.md`](docs/AGENT_PROVISIONED_EXTERNAL_CI.zh-CN.md)、[`docs/TRUSTED_SECRET_BROKER.zh-CN.md`](docs/TRUSTED_SECRET_BROKER.zh-CN.md) 与 Starter 的 Project Provisioning Contract；平台 bootstrap 已完成后，优先采用 `agent-provisioned-external-ci`
6. 当 PPF 作为完整 Inquiry Publishing Stack 的一层时，读取项目的 AHICP 入口和所选 Starter profile

由网页 AI Agent 为 GitHub 仓库配置 Cloudflare 时，还必须遵循 [`docs/WEB_AGENT_GITHUB_CLOUDFLARE_ONBOARDING.zh-CN.md`](docs/WEB_AGENT_GITHUB_CLOUDFLARE_ONBOARDING.zh-CN.md)（English: [`docs/WEB_AGENT_GITHUB_CLOUDFLARE_ONBOARDING.md`](docs/WEB_AGENT_GITHUB_CLOUDFLARE_ONBOARDING.md)）。

对于包含原创或未发布内容的新项目，安全默认值是：canonical 源仓库 private，同时 Continuous Web 保持 restricted + authenticated。当通过完整 Inquiry Publishing Stack 采用时，默认组合是完整 PPF + 完整 AHICP + Vault Interface；精简 profile 必须由人类明确选择。两项平台 provisioning principal 已授权、account-wide Access 已验证后，不得仅因为在已批准范围内新增另一个项目 repository 或 Worker 就反复要求账户级 consent。

从任意 PPF 公共入口进入时，在跨组件配置前恢复四组件生态。公共链接只授权读取公共信息，绝不授权私人状态访问。

执行 Cloudflare 操作前，必须说明准确目标、受影响层、数据流、凭据范围、人类批准边界、验证项目和回滚路径。需要人类操作 UI 时，必须给出编号的操作者级步骤，包括当前 Dashboard 路径、应填写的非秘密值、完成证据，以及随后要验证的状态。绝不要求人类把密码、token、私钥、恢复码或其他秘密粘贴到聊天中。External-CI Profile 的 Cloudflare deployment token 必须经 trusted Secret Broker 直接写入 GitHub Actions secrets；模型只能接收非秘密安装状态。Reference Broker 状态机必须拒绝覆盖已有目标 Secret，并在本轮 transaction rollback 时 revoke 新 mint 的 token。

把人工关卡当作可续办的检查点，不要因此暂停整项任务。继续执行其他已获授权且互不依赖的工作；某一步确实受关卡阻塞时，给出对应服务的直达链接、准确导航步骤、需要选择/填写的非秘密内容、秘密输入边界、完成证据，以及我随后会读取验证的具体状态。只等待这一个关卡；用户完成后重新读取提供商状态并自动续办，不要要求重复已完成步骤。

始终区分 proposal、authorization、execution、verification 与 durable write-back。
