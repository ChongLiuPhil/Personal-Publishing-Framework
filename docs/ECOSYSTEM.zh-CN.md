# PPF 在 Inquiry Publishing Stack 中的位置

PPF 负责作品从源内容到构建、发布、正式版本、归档和 Continuous Web 的完整生命周期；它不规定人与 AI 应怎样协作。

如果第一次接触整个体系，请先从 [AHICP 主页](https://inquirystack.philohub.workers.dev/) 开始；那里提供完整使用指南。需要配置、采用或升级项目时，再由 AI 进入 Starter 的机器入口。

要完成一个项目的完整配置，请遵循 [Starter 体系入口](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/ECOSYSTEM.zh-CN.md)，并连接：

- [AHICP 主页](https://inquirystack.philohub.workers.dev/) · [仓库](https://github.com/ChongLiuPhil/AI-Assisted-Human-Inquiry-and-Creation-Protocol)
- [Vault Interface 主页](https://inquirystack.philohub.workers.dev/vault-interface/) · [仓库](https://github.com/ChongLiuPhil/Vault-interface)
- [Starter 主页](https://inquirystack.philohub.workers.dev/starter/) · [仓库](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter)

新项目的默认基线是 **完整 PPF + 完整 AHICP**，Vault Interface 只负责公共元数据。项目应在适当的项目记录中保存实际采用状态、源版本、出版授权和提供商状态。

原创、未发布作品及其他需要保护的源内容默认保持私有。Continuous Web 是一种发布能力，不等于获得发布许可；私人或过渡性产物必须使用读者访问控制。

普通新项目首选 Cloudflare Workers Static Assets + Workers Builds Native：个人账号下 GitHub repository 保持 private，每项目允许一次短人工 repository connection，给 Worker 配置 Access，并验证第二次 push 无需重新授权即可自动部署。GitHub Actions External CI + project-scoped Worker credential 继续作为高级可选 Profile。GitHub 继续作为权威源文件、版本历史和 CI 平台。Cloudflare Pages 继续支持已有项目，不自动迁移。四个框架栏目现以 https://inquirystack.philohub.workers.dev/ 为正式入口；原框架 GitHub Pages 站点已停用。下游项目可根据运行时和发布需求选择 Pages、Workers 或其他受支持的 provider。

四个框架站点的迁移遵循 [Cloudflare 公共站点迁移说明](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/CLOUDFLARE_PUBLIC_DELIVERY_MIGRATION.zh-CN.md)。

详细 Cloudflare 出版契约见 [`CONTINUOUS_WEB_CLOUDFLARE.zh-CN.md`](CONTINUOUS_WEB_CLOUDFLARE.zh-CN.md)，普通每项目接入流程见 [`PER_PROJECT_GITHUB_CLOUDFLARE_SETUP.zh-CN.md`](PER_PROJECT_GITHUB_CLOUDFLARE_SETUP.zh-CN.md)。[`AGENT_PROVISIONED_EXTERNAL_CI.zh-CN.md`](AGENT_PROVISIONED_EXTERNAL_CI.zh-CN.md) 只描述高级可选 Profile；可复用基础设施状态与协调边界继续见 [`GITHUB_CLOUDFLARE_INTEGRATION.zh-CN.md`](GITHUB_CLOUDFLARE_INTEGRATION.zh-CN.md)。[安全配置方案](CLOUDFLARE_SECURITY_PROFILES.zh-CN.md) 说明 deployment credential 权衡；部署身份和读者访问是两个不同决策。

跨组件工作必须阅读 [权威 Agent 调取契约](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/AGENT_RETRIEVAL_CONTRACT.zh-CN.md)。公共链接只用于恢复生态关系，不授权私人状态访问。
