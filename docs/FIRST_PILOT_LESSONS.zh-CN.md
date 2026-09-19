# PPF 第一个真实 Downstream Pilot：经验与回灌

**日期：** 2026-09-19  
**Pilot：** `ChongLiuPhil/epistemology-textbook`  
**PPF base：** v0.1.0-draft @ `9326920e1920d18f0a71eac26d4068da9d6bdffe`

## 1. Pilot 目的

验证同一 canonical Quarto source 是否可以真实支持：

```text
QMD / BibTeX
    |
    +--> continuous Web
    |
    +--> explicit on-demand EPUB
    +--> explicit on-demand PDF
    +--> explicit on-demand DOCX
    +--> explicit on-demand LaTeX
```

同时保持 BUILD / PUBLISH / RELEASE 分离。

## 2. 真实运行结果

Pilot 在 GitHub Actions 中实际验证：

- Governance：PASS
- Web profile render：PASS
- rendered HTML integrity：PASS
- EPUB：PASS
- DOCX：PASS
- LaTeX：PASS
- PDF：PASS
- GitHub Pages production deployment：PASS

PDF 需要项目专用的 CJK fonts + TinyTeX，且明显比 EPUB / DOCX / LaTeX 更重。这支持把重型出版格式留在 on-demand，而不拖入日常 Web pipeline。

运行时间只代表该次 runner 环境，不是 PPF 性能规范。

## 3. 第一条经验：continuous build 与 provider deployment 应分开

最初 reference template 直接在 `main` push 后尝试 Cloudflare deployment。

真实迁移表明，一个项目可能已经具备：

- canonical source；
- Web profile；
- source/output validation；

但尚未具备：

- provider account context；
- Worker target；
- deployment credentials；
- canonical URL；
- staging verification。

因此 PPF 现在明确：

`continuous publication intent != unconditional provider deployment`

reference template 改为默认持续 build/validate，但 provider deployment 需要显式 activation。

## 4. 第二条经验：一次 on-demand 请求只构建一个格式

不同格式会引入不同工具链。

特别是 PDF 可能引入：

- TeX；
- fonts；
- language-specific packages；
- print geometry。

因此 reference workflow 应让用户一次明确选择一个目标格式，并验证对应 artifact 确实生成。

这降低一个格式的依赖对其他格式的耦合。

## 5. 第三条经验：provider provisioning 与 recurring deploy 应分离

Cloudflare 当前权限模型表明：

- 创建 Worker 可能需要 product-level Admin；
- 部署到已存在的指定 Worker只需要该 Worker 的 Editor；
- 修改 Custom Domain / Route 还需要对应 zone 的 Workers Routes Write。

因此更合理的长期模型是：

```text
one-time provisioning authority
        |
        +--> create/confirm resource
        +--> attach route/domain when needed

long-lived CI credential
        |
        +--> deploy only to the intended existing resource
```

PPF 本身不规范 Cloudflare 权限，但 reference implementation 应示范最小权限与权限生命周期分离。

## 6. 第四条经验：发布迁移不能覆盖既有项目治理

Pilot 第一次 CI 失败并不是 Quarto 或 PPF 问题，而是迁移过程误删了原项目治理 validator 依赖的一个 Working Memory invariant。

这说明：

- PPF 只治理 publication lifecycle；
- 项目原有的协作、审计、许可或研究治理必须继续有效；
- publication migration 不应静默重写其他治理层。

这也是 PPF 与 AHICP / personal governance 分层的重要理由。

## 7. 第五条经验：readiness 状态也需要进入 CI

如果 deployment readiness 是机器可读状态，那么改变：

- provider state；
- canonical URL；
- deployment gate；
- readiness config；

应重新触发相关 validation。

仅验证书稿文件而忽略 publication contract / provider readiness，会留下配置漂移。

## 8. 回灌到 v0.1 reference implementation

根据此次 pilot：

1. continuous Web build 与 Cloudflare deployment activation 分离；
2. continuous Web validation 与 provider deployment activation 分离；
3. repository-owned `make web-publish-check` 成为 GitHub Actions 与 Cloudflare 共用的 canonical gate；
4. Cloudflare Workers Builds + GitHub App 成为默认参考 delivery integration；
5. `cloudflare-builds.yaml` 记录期望的 Git connection / build / deploy / preview / readiness，但不冒充 provider account 的真实状态；
6. Node / Wrangler / Quarto 在 reference implementation 中固定版本，并通过非部署 contract CI 验证；
7. on-demand workflow 验证请求格式的 artifact；
8. schema 增加 deployment integration / readiness 与 release semantics；
9. 文档加入 OAuth/MCP、GitHub App、provisioning / recurring deployment 的安全边界；
10. PPF 根级 CI 持续验证 reference template，而不只依赖一次 pilot。

## 9. 尚未由 Pilot 验证的内容

此次 pilot **没有**验证：

- Cloudflare account-side deployment；
- Workers Custom Domain cutover；
- DNS migration；
- Amazon KDP / Kindle delivery；
- external publisher DOCX workflow；
- formal release archive convention。

这些仍属于后续 v0.1 pilot 范围。


## 10. 后续 Cloudflare ↔ GitHub 范本验证

同一 downstream pilot 随后继续验证 repository-side Cloudflare integration contract。

在 `epistemology-textbook` 中实际验证：

- GitHub Actions 调用统一 `make web-publish-check`：PASS；
- Node 24 pin：PASS；
- Wrangler 4.135.0 安装与版本检查：PASS；
- Quarto 1.10.18 从空白 runner 下载并进行 SHA-256 校验：PASS；
- `make cloudflare-build`：PASS；
- rendered Web artifact validation：PASS；
- merge 后 GitHub Pages production deployment：PASS；
- active GitHub workflows 中没有 Cloudflare token / Wrangler deploy / Cloudflare deploy action：PASS。

因此当前 reference implementation 的默认模型升级为：

```text
GitHub Actions = independent validation
repository-owned gate = shared build/validation logic
Workers Builds = preferred Cloudflare Git delivery
Cloudflare MCP = optional agent-side account automation
GitHub Actions + scoped token = fallback
```

这一阶段仍然**没有**声称 Cloudflare account-side deployment 已完成。Worker/account/GitHub App connection、第一次 Cloudflare preview、Custom Domain 与 production cutover 仍需要后续真实账户验证。
