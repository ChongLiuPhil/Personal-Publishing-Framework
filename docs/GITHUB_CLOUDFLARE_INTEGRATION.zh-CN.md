# GitHub–Cloudflare 基础设施集成

PPF 项目在 `project.infrastructure.json` 中声明托管意图。该清单是期望状态；GitHub 与 Cloudflare API 响应以及匿名 HTTP 探测结果才是实际状态。Provider adapter 先读取现状，规划器再生成最小、幂等的协调计划；只有授权与发布关卡通过后，orchestrator 才能应用变更。

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

```sh
python providers/infrastructure/manifest.py project.infrastructure.json
python -m providers.infrastructure.plan project.infrastructure.json --actual actual-state.json
```

规划器不修改 provider 状态。缺少实际状态时返回 `READ_REQUIRED`；账户级 Access 不足时返回 `BOOTSTRAP_REQUIRED`；意外的公开状态标记为 `SECURITY_DRIFT`。状态和审计记录会拒绝秘密字段及凭据格式值。API token、密码、Cookie、私钥或 provider 原始错误响应均不得进入状态文件或日志。

## Provider 行为

Cloudflare Access 可通过账户级 `all_workers` destination 保护全部 Worker。启用该基线后，公开某个正式 Worker 需要为该 Worker 单独建立 `worker` destination 和 bypass policy；账户级基线必须继续启用。预览可以独立保护。bypass 会关闭匹配流量的 Access 执行与 Access 请求日志，因此公开应用需要 Worker observability。公开切换后必须同时验证目标站可匿名访问，并验证另一个 private 控制 Worker 仍拒绝匿名请求。

Workers Builds 使用 Worker 不可变的 `external_script_id` tag 标识 Worker，不能将它与 Worker 名称混为一谈。Worker 名称、tag、GitHub 仓库 ID、连接 UUID、trigger UUID 和 build-token UUID 必须分开记录。build-token UUID 是标识符，不是秘密值。Cloudflare 当前文档的 Workers Builds 配置流程要求 user-scoped API token，并授予 Workers Builds Configuration Edit 和 Workers Scripts Read；不得把这类凭据称为最小权限。修改 GitHub 仓库可见性要求仓库 Administration write 权限。所有凭据不得进入源码和日志。

GitHub App 安装/授权、账户级 Access 初始化、域名/DNS、计费与最终公开切换仍是明确的人工关卡。`apply` 不得从 build、deploy、sync 或 update 请求中推断这些操作已获批准。不得自动迁移或删除 Pages 资源。

## 当前实现边界

目前已实现并测试清单校验、可见性不变量、只读规划器、私有 ID/审计状态存储，以及既有 Cloudflare Worker 生命周期 adapter。这个参考包尚未实现读取 provider 资源清单或修改 GitHub/Cloudflare 状态的 API 操作；在补齐之前，操作人员必须提供独立核验过的实际状态快照，不能把计划当作资源存在或变更已完成的证据。

当前 provider 参考（2026-09-23 核验）：

- Cloudflare Workers Access：<https://developers.cloudflare.com/workers/configuration/cloudflare-access/>
- Cloudflare Workers Builds API：<https://developers.cloudflare.com/workers/ci-cd/builds/api-reference/>
- Cloudflare Workers 最佳实践：<https://developers.cloudflare.com/workers/best-practices/workers-best-practices/>
- GitHub 仓库 API：<https://docs.github.com/en/rest/repos/repos>
