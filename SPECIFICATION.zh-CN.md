# Personal Publishing Framework — 规范

**版本：** v0.1.0-draft

## 1. 目的

PPF 为人的作品定义一套可迁移的出版生命周期。它把持久源内容、生成格式、版本决定和发布基础设施彼此区分。

PPF 不限制作品主题。兼容项目可以是知识作品、教学材料、研究、文章、诗歌、小说、文档或其他创作。

## 2. 规范性术语

- **MUST（必须）** — PPF 合规所要求。
- **SHOULD（应当）** — 强烈推荐，除非项目记录了偏离理由。
- **MAY（可以）** — 可选。

## 3. 核心对象

### 3.1 Source

PPF 项目必须标识 canonical source。

源内容应尽可能：
- 便于人直接阅读；
- 受版本控制；
- 不依赖单一出版格式；
- 与声明的依赖一起足以重新构建支持的输出。

生成后的 HTML、PDF、EPUB、DOCX、LaTeX 或印刷文件不得静默取代 canonical source。

### 3.2 Publication contract

项目应维护声明式 publication contract，约定默认文件名为 `publishing.yaml`。

该契约记录“希望如何发布”。Cloudflare Wrangler 等 provider-specific 配置属于实现状态，应与之分离。

### 3.3 Publication modes

PPF 定义两种主要模式：

- **continuous** — 已接受的源内容变化后自动重建；
- **on-demand** — 只有明确请求或 release workflow 才构建。

以后可以增加其他模式，但必须明确其语义。

### 3.4 Artifact

生成的输出属于 publication artifact，例如 HTML、EPUB、PDF、DOCX、LaTeX、印刷文件或其他表示。

除非项目显式声明，否则 artifact 均视为派生结果。

### 3.5 Deployment readiness

`continuous` 描述的是某个输出应随已接受的源内容变化而持续重建的发布意图；它**不等于**在 provider 尚未配置完成时无条件执行外部部署。

如果某个 deployment provider 需要目标资源、凭据、域名或其他前置条件，项目 MUST 在启用自动 deployment 前确认这些条件。项目 SHOULD 让 deployment activation 成为显式、可审计的状态，而不是由“仓库存在某个 workflow”隐式推断。

当 validation 与 deployment 由不同 CI / provider 执行时，项目 SHOULD 保留一个 repository-owned、provider-independent 的 canonical build/validation gate，使不同执行环境调用同一逻辑，而不是复制两套容易漂移的验证规则。

项目 MAY 维护独立的 provider-integration machine contract，用于描述期望的 repository connection、branch、build/deploy commands 与 readiness。该 contract 不得与 provider 账户中的真实状态混为一谈；如果 provider 不会原生读取该 contract，项目必须明确这一点。

## 4. 生命周期

PPF 区分：

```text
SOURCE -> BUILD -> PUBLISH -> RELEASE -> ARCHIVE
```

这些动作相互关联，但不是同义词。

- **SOURCE** — 维护持久作品源。
- **BUILD** — 把源转换成输出格式。
- **PUBLISH** — 让某个输出可被访问。
- **RELEASE** — 冻结一个有意图的版本或 edition。
- **ARCHIVE** — 保存足够的源和版本状态以便未来重建。

一次 build 不得自动被解释成 release；一次 release 也不得自动被解释为允许外部发布，除非项目明确声明这种行为。

## 5. Continuous Web publication

当项目希望存在持续可阅读的公共版本时，PPF 推荐把 HTML/Web 作为默认 continuous publication mode。

参考流水线：

```text
accepted source change
-> repository-owned validation/build gate
-> independent CI validation
-> provider readiness
-> provider build/deploy
-> production verification
```

验证失败必须阻止发布。

在 deployment provider 尚未 ready 时，continuous Web **build / validation** MAY 保持启用，而 provider deployment 保持 staged / disabled。

## 6. 按需格式

EPUB、PDF、DOCX、LaTeX 和 print-ready files 等格式，默认应采用 on-demand，除非项目有明确理由持续构建。

在可行时，一次显式 on-demand 请求 SHOULD 只选择并构建一个目标格式，以减少无关工具链、字体、TeX 或平台依赖对其他格式的耦合。

## 7. 可迁移性

canonical content 应尽量减少会不必要地阻止其他支持格式转换的 format-specific markup。

可以存在平台专用增强，但核心意义应在没有这些增强时仍可恢复。

## 8. 授权

仓库可见性与发布授权是两个不同概念。

源仓库公开不得自动解释为所有输出和发行渠道都已经获得发布授权。

## 9. AI 中立

PPF 不要求使用 AI。

使用 AI 的项目可以采用独立治理协议，例如 AI-Assisted Human Inquiry and Creation Protocol（AHICP）。

PPF 本身不重新定义作者身份、主体性或责任。

## 10. 参考技术栈

首个 reference stack 可以使用 Git、Quarto/Pandoc、GitHub Actions、Cloudflare Workers Builds、Wrangler 与 Cloudflare Workers Static Assets；这些实现不是规范性要求。

在 GitHub/GitLab 等 provider-native Git integration 可用时，reference implementation MAY 让 GitHub Actions 负责独立 validation，而让 hosting provider 的原生 build system 负责 delivery；二者 SHOULD 调用同一个 repository-owned publication gate。

如果 provider-native Git integration 不可用，项目 MAY 使用 GitHub Actions 等 external CI 配合 scoped deployment credential。

在 provider 支持权限范围划分时，reference implementation SHOULD 把一次性 infrastructure provisioning 与长期 recurring deployment credential 分离，并为持续部署使用满足任务所需的最小权限。

如果 provider-native integration 当前无法满足项目要求的 credential scope，项目 SHOULD 明确记录这种 trade-off，而不是把较宽权限静默描述为 least privilege。项目 MAY 提供一个 hardened external-CI profile，使用更细粒度的 deployment credential，直到 provider-native integration 能满足同等安全要求。

支持 MCP/OAuth 的 AI Agent MAY 帮助完成 provider-side configuration；这属于可选自动化，不是 PPF 合规要求。账户所有者必须保留对身份授权、权限范围、production security profile 与生产 cutover 的控制。

## 11. 版本

规范自身在积极开发阶段使用语义版本。具体作品的 edition 可以采用其他明确记录的版本规则。

## 12. 当前合规状态

本草案已经包含初始 schema、reference workflows 与首个真实 downstream runtime pilot 的反馈。更完整的 conformance tests、release conventions 与 provider migration guides 仍将在后续 v0.1 修订中发展。
