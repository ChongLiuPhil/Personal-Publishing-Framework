# Agent 协作契约

在配置或发布项目之前，先阅读：

1. [`docs/ECOSYSTEM.zh-CN.md`](docs/ECOSYSTEM.zh-CN.md)
2. [`ecosystem.yaml`](ecosystem.yaml)
3. [统一跨仓库 Agent 调取契约](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/AGENT_RETRIEVAL_CONTRACT.zh-CN.md)
4. 涉及 Continuous Web 或 Cloudflare 时，先阅读 [`docs/CONTINUOUS_WEB_CLOUDFLARE.zh-CN.md`](docs/CONTINUOUS_WEB_CLOUDFLARE.zh-CN.md)，再读取适用的 PPF provider-specific runbook
5. 当 PPF 作为完整 Inquiry Publishing Stack 的一层时，读取项目的 AHICP 入口和所选 Starter profile

对于包含原创或未发布内容的新项目，安全默认值是：canonical 源仓库 private，同时 Continuous Web 保持 restricted + authenticated。当通过完整 Inquiry Publishing Stack 采用时，默认组合是完整 PPF + 完整 AHICP + Vault Interface；精简 profile 必须由人类明确选择。

从任意 PPF 公共入口进入时，在跨组件配置前恢复四组件生态。公共链接只授权读取公共信息，绝不授权私人状态访问。

执行 Cloudflare 操作前，必须说明准确目标、受影响层、数据流、凭据范围、人类批准边界、验证项目和回滚路径。需要人类操作 UI 时，必须给出编号的操作者级步骤，包括当前 Dashboard 路径、应填写的非秘密值、完成证据，以及随后要验证的状态。绝不要求人类把密码、token、私钥、恢复码或其他秘密粘贴到聊天中。

始终区分 proposal、authorization、execution、verification 与 durable write-back。
