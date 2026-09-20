# Agent 协作契约

在配置或发布项目之前，先阅读：

1. [`docs/ECOSYSTEM.zh-CN.md`](docs/ECOSYSTEM.zh-CN.md)
2. [`ecosystem.yaml`](ecosystem.yaml)
3. 如果涉及 Continuous Web 或 Cloudflare，阅读 [`docs/CONTINUOUS_WEB_CLOUDFLARE.zh-CN.md`](docs/CONTINUOUS_WEB_CLOUDFLARE.zh-CN.md)
4. 项目的 AHICP 入口和选定的 Starter profile

新项目默认基线是完整 PPF 加完整 AHICP。不要把私人项目状态复制进本仓库。未发布原创作品默认保持私人。

在执行 Cloudflare 操作前，必须说明目标、数据流、凭据范围、人类批准边界、验证项目和回滚路径。绝不要求人类把密码、token、私钥或恢复码粘贴到聊天中。

Agent 可以沿着公共体系链接理解整体架构，但读取私人状态和执行发布必须获得人类明确授权。保持 proposal、authorization、execution、verification 和 durable write-back 的区分。
