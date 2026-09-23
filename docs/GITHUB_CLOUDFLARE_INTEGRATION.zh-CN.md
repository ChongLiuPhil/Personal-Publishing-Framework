# GitHub–Cloudflare 基础设施集成

PPF 项目在 `project.infrastructure.json` 中声明托管意图。该清单是期望状态；GitHub 与 Cloudflare API 响应以及匿名 HTTP 探测结果才是实际状态。Provider adapter 先读取现状，规划器再生成最小、幂等的协调计划；只有授权与发布关卡通过后，orchestrator 才能应用变更。

由网页 AI Agent 根据 GitHub 仓库配置 Cloudflare 时，遵循[网页 Agent 接入契约](WEB_AGENT_GITHUB_CLOUDFLARE_ONBOARDING.zh-CN.md)，其中规定了资源发现、最小项目输入、安全应用边界、在线验证与回滚。

## 可见性与安全默认值

仓库可见性与网站可见性是两个独立字段。网站公开不会连带公开 GitHub 仓库，源码开放也不会连带公开托管网站。新项目默认使用 private 仓库、private Worker、private 预览、无公共 bypass、禁止付费服务，并依赖账户级 Access 基线。预览保护与正式站可见性互相独立。

`release.state: public` 只记录期望的公开状态，本身不构成批准。公开切换必须带有上游批准标识和相应发布关卡。仓库公开还必须通过内容、许可、隐私以及当前文件和 Git 历史的秘密检查。网站公开必须通过独立网站发布关卡，并验证一个控制 Worker 仍然保持 private。账户级 Access 属于平台初始化边界，项目协调流程不得启用或关闭它。

## 文件与命令

- `schema/project.infrastructure.schema.json` 定义机器可读的期望状态契约。
- `templates/quarto-book/project.infrastructure.json` 提供默认 private 的示例。
- `schema/integration-state.schema.json` 定义保存在本地私有状态中的 provider ID。
- `providers/infrastructure/manifest.py` 校验项目清单。
- `providers/infrastructure/plan.py` 对照 provider 读取的状态生成只读计划。
- `providers/infrastructure/state.py` 将非秘密 ID 和审计事件保存在 `~/.ppf/infrastructure`（或 `PPF_INFRA_STATE_DIR`），并设置仅所有者可读写的权限。
- `providers/infrastructure/github.py`、`cloudflare.py` 和 `coordinator.py` 提供可注入的 GitHub、Workers、Workers Builds、Access API 适配器，以及 `doctor / plan / apply / verify / rollback` 命令。

```sh
python providers/infrastructure/manifest.py project.infrastructure.json
python -m providers.infrastructure.plan project.infrastructure.json --actual actual-state.json
python -m providers.infrastructure.coordinator doctor project.infrastructure.json
python -m providers.infrastructure.coordinator plan project.infrastructure.json --website-gate approval.json --build-config builds.json --triggers triggers.json
python -m providers.infrastructure.coordinator apply project.infrastructure.json --website-gate approval.json --build-config builds.json --triggers triggers.json
python -m providers.infrastructure.coordinator verify project.infrastructure.json
python -m providers.infrastructure.coordinator rollback project.infrastructure.json
```

GitHub 凭据使用 GITHUB_TOKEN，Cloudflare 凭据使用 CLOUDFLARE_API_TOKEN 和 CLOUDFLARE_ACCOUNT_ID；只在 Agent 受保护的进程环境中直接录入，不通过命令行参数传递。设置 PPF_PRODUCTION_HOSTNAME、PPF_PREVIEW_URL 和 PPF_CONTROL_WORKER_URL 后可执行匿名 HTTP 验证，这些值只包含 hostname。API 客户端只返回脱敏错误码，不输出 provider 原始错误。

规划器不修改 provider 状态。缺少实际状态时返回 `READ_REQUIRED`；未发现账户级 Access 时阻止 apply；意外的公开状态标记为 `SECURITY_DRIFT`。账户级 Access 设置方法会明确停止并返回 `ACCOUNT_SECURITY_UI_APPROVAL_REQUIRED`，由账户所有者在 Cloudflare 控制台提交该安全设置，之后适配器重新读取并验证。状态和审计记录会拒绝秘密字段及凭据格式值。由于 Cloudflare 不会返回构建 Secret 的值，构建配置回滚快照会省略 Secret 环境变量；回滚不会重写或记录这些值。

## Provider 行为

Cloudflare Access 可通过账户级 all_workers destination 保护全部 Worker。启用该基线后，公开某个正式站点 hostname 需要为该 hostname 单独建立精确的 public destination 和 bypass policy。worker destination 同时覆盖正式站和预览；更具体的 public destination 优先，因此只匹配正式 hostname 的 bypass 会让预览 hostname 继续受账户级基线保护。账户级基线必须继续启用。bypass 会关闭匹配流量的 Access 执行与 Access 请求日志，因此公开应用需要 Worker observability。公开切换后必须同时验证目标站可匿名访问，并验证另一个 private 控制 Worker 仍拒绝匿名请求。

Workers Builds 使用 Worker 不可变的 `external_script_id` tag 标识 Worker，不能将它与 Worker 名称混为一谈。Worker 名称、tag、GitHub 仓库 ID、连接 UUID、trigger UUID 和 build-token UUID 必须分开记录。build-token UUID 是标识符，不是秘密值。Cloudflare 当前文档的 Workers Builds 配置流程要求 user-scoped API token，并授予 Workers Builds Configuration Edit 和 Workers Scripts Read；不得把这类凭据称为最小权限。修改 GitHub 仓库可见性要求仓库 Administration write 权限。所有凭据不得进入源码和日志。

GitHub App 安装/授权、账户级 Access 初始化、域名/DNS、计费与最终公开切换仍是明确的人工关卡。`apply` 不得从 build、deploy、sync 或 update 请求中推断这些操作已获批准。不得自动迁移或删除 Pages 资源。

## 当前实现边界

Provider adapter 现可读取 GitHub 仓库、Workers、Workers Builds 配置和触发器以及 Access 应用。GitHub 可见性、Workers Builds 配置/触发器和精确正式 hostname 的 Access 例外会先读取再幂等协调。账户级 Access 仍由账户所有者在 Cloudflare 控制台设置；Worker 代码部署沿用项目获批的构建流程。真实 apply/verify 需要 provider 凭据、已在控制台启用的账户级 Access 和相应的明确发布关卡；模拟测试不等同于真实验证。

当前 provider 参考（2026-09-23 核验）：

- Cloudflare Workers Access：<https://developers.cloudflare.com/workers/configuration/cloudflare-access/>
- Cloudflare Workers Builds API：<https://developers.cloudflare.com/workers/ci-cd/builds/api-reference/>
- Cloudflare Workers 最佳实践：<https://developers.cloudflare.com/workers/best-practices/workers-best-practices/>
- GitHub 仓库 API：<https://docs.github.com/en/rest/repos/repos>
