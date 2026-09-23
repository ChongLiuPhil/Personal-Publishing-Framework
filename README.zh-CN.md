**第一次了解整个体系：** 从 [AHICP 主页](https://chongliuphil.github.io/AI-Assisted-Human-Inquiry-and-Creation-Protocol/) 开始；那里提供完整使用指南，并说明怎样把技术配置交给 AI。

# Personal Publishing Framework

[English](README.md) | [中文](README.zh-CN.md)

**公共项目入口：** [AHICP 主页](https://chongliuphil.github.io/AI-Assisted-Human-Inquiry-and-Creation-Protocol/) · [PPF 主页](https://chongliuphil.github.io/Personal-Publishing-Framework/) · [Vault Interface 主页](https://chongliuphil.github.io/Vault-interface/) · [Starter 主页](https://chongliuphil.github.io/Inquiry-Publishing-Project-Starter/)

**体系与 Agent 入口：** [`docs/ECOSYSTEM.zh-CN.md`](docs/ECOSYSTEM.zh-CN.md) · [`ecosystem.yaml`](ecosystem.yaml) · [`llms.txt`](docs/llms.txt) · [Starter 统一指南](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/ECOSYSTEM.zh-CN.md) · [Agent 调取契约](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/AGENT_RETRIEVAL_CONTRACT.zh-CN.md)

**Personal Publishing Framework（PPF，个人出版框架）**是一套以源内容为中心、强调可迁移性的框架，用于发展、分享和出版知识与创作成果。

> **格式和平台可以更换；源内容应当长久存在。**

PPF 面向任何希望把想法、学习成果、写作、研究、教学材料、故事、诗歌或其他创作发展为可长期保存、持续演进并能够以多种形式分享的作品的人。

它不要求使用者是专业学者，也不要求作品最终进入正式出版，更不要求使用 AI。一个 PPF 项目可以是儿童诗集、个人学习项目、技术教程、公共知识网站、长期写作中的书，也可以是正式学术著作。

## 核心模型

PPF 把作品的持久源内容，与具体出版格式和发布平台分开：

```text
创作者拥有的源内容
        |
        +---- 持续发布 ----------> HTML / Web
        |
        +---- 按需版本 ----------> EPUB
                                  PDF
                                  DOCX
                                  LaTeX
                                  Print
```

即使未来更换构建工具、托管商或发行平台，作品仍应可以从权威源内容（canonical source）重新构建。

对于新配置的原创或未发布作品，参考安全默认是：权威源内容保持 **private（私有）**，Continuous Web 在明确公开发布前保持 **restricted + authenticated（受限并需要认证）**。Web 公开绝不意味着源仓库也必须公开。

## 两种发布模式

### Continuous Publication — 持续发布

某些输出，尤其是 Web Edition，可以在已接受的源内容更新后自动重建：

```text
source update
-> validate
-> build HTML
-> validate output
-> deployment readiness gate
-> deploy
-> verify
```

### Edition Publication — 版本出版

其他格式仅在明确请求或冻结正式版本时生成：

```text
source
-> build requested format
-> review
-> release
-> optional external publication
```

典型格式包括 EPUB、PDF、DOCX、LaTeX、印刷就绪文件及平台专用版本。

## 生命周期

PPF 将出版生命周期区分为五个相关但不同的环节：

1. **SOURCE** — 持久、由创作者控制的源内容。
2. **BUILD** — 从源内容生成一种或多种出版格式。
3. **PUBLISH** — 让读者可以访问某个输出。
4. **RELEASE** — 在需要时冻结一个具名或版本化版本。
5. **ARCHIVE** — 保存足以在未来重建作品的源内容和版本状态。

## 范围边界

PPF 规范人的作品如何被持续维护、发展、分享和出版。它**不定义人与 AI 应当如何协作**。

使用 AI 的项目可以采用 **AI-Assisted Human Inquiry and Creation Protocol（AHICP）** 作为兼容的治理层；PPF 本身不依赖 AI。

## 参考实现

第一套参考实现采用：

- Git 作为 canonical versioned source；
- Quarto / Pandoc 进行多格式转换；
- HTML 作为默认持续发布格式；
- GitHub Actions 作为独立 验证关卡；
- repository-owned `make web-publish-check` 作为统一 Web publication gate；
- Cloudflare Workers Builds + GitHub App 作为新项目默认参考交付集成；Cloudflare Pages 继续支持已有项目，不自动迁移；
- `project.infrastructure.json` 作为 GitHub/Cloudflare 期望状态清单，默认 private，并通过只读协调规划器比较实际状态；
- Cloudflare Workers Static Assets 作为 Web delivery layer；
- EPUB、PDF、DOCX、LaTeX 作为按需生成的 发布产物。

这些技术只是参考栈，而不是 PPF 的硬性要求。

## 设计原则

- **源内容先于格式。**
- **先保证创作者能够持续掌握源内容，再考虑平台便利。**
- **持续 Web 发布与正式版本出版相互区分。**
- **构建、正式版本和外部发布是不同动作。**
- **发布意图应当是声明式且可迁移的。**
- **仓库公开并不自动等于所有输出都获得发布授权。**
- **框架应同时适用于短小创作与长期知识项目。**

## v0.1 计划

PPF v0.1 将定义：

- 最小项目模型；
- 作为声明式出版契约的 `publishing.yaml`；
- 持续发布与按需版本两种发布模式；
- 与输出格式相对独立的源内容原则；
- 版本与归档语义；
- Quarto、GitHub Actions、Cloudflare 的参考工作流；
- 与其他工具和平台兼容的实现指南。

## 参考实现

第一套可执行 参考实现 位于 [`templates/quarto-book/`](templates/quarto-book/README.zh-CN.md)。

它把 PPF 模型实现为：

```text
Git canonical source
-> repository-owned Web gate
-> GitHub Actions independent validation
-> Cloudflare Workers Builds
-> Cloudflare Workers Static Assets

明确请求
-> EPUB / PDF / DOCX / LaTeX
-> GitHub Actions artifact
```

参考实现与规范本身保持分离，因此未来可以用其他技术栈实现相同的 PPF 生命周期。

## 状态

**Working version: v0.1.0-draft**

当前已完成初始规范、Quarto 参考实现、第一个真实 downstream runtime pilot，以及从该 pilot 提炼出的 Workers Builds ↔ GitHub 可复用集成范本。PPF 自身现已用 root-level CI 持续验证 reference template。Pilot 结果见 `docs/FIRST_PILOT_LESSONS.zh-CN.md`，账户授权说明见 `docs/CLOUDFLARE_GITHUB_AUTHORIZATION.zh-CN.md`。


可复用的 GitHub–Cloudflare 期望状态与协调契约见 [`docs/GITHUB_CLOUDFLARE_INTEGRATION.zh-CN.md`](docs/GITHUB_CLOUDFLARE_INTEGRATION.zh-CN.md)。

Cloudflare 参考实现 的 production credential 选择见：

`docs/CLOUDFLARE_SECURITY_PROFILES.zh-CN.md`

关于从真实 Cloudflare pilot 提炼出的 provider integration 通用模式、概念边界及是否应进一步规范化，见非规范研究 note：

`docs/PROVIDER_INTEGRATION_PATTERN_RESEARCH.zh-CN.md`



## 与综合 Starter 的关系

如果希望把 AHICP、PPF 与公开 Vault Interface 组合到新项目，或对既有 GitHub 项目进行可审计升级，可使用：

https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter

Starter 只负责组合、版本锁定、检查与升级计划；本仓库继续是自身规范／模板的权威来源。

## 许可

本仓库采用**非商业双重许可模式**，目的是支持个人学习、教育、研究、公益以及其他非商业复用，同时保留商业授权权利。

- 软件、脚本、Schema、自动化、机器可读配置和可执行模板：**PolyForm Noncommercial License 1.0.0**；
- 说明文档、规范、图示、教育材料与方法论内容：**CC BY-NC-SA 4.0**；
- 商业使用需要另行取得商业许可。

仓库级权威许可边界见 [LICENSE.md](LICENSE.md) 与 [COMMERCIAL-LICENSING.md](COMMERCIAL-LICENSING.md)。
