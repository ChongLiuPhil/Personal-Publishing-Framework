# Provider Integration Pattern — Research Note

**Status:** `AI-PROPOSED / NON-NORMATIVE / RESEARCH NOTE`  
**Research date:** 2026-09-19  
**Scope:** PPF reference implementation / cross-layer architecture research

> 本文件记录一个尚未 Promotion 为 PPF 规范的人机协作基础设施模式。它不是人类已确认的 PPF Core 决定，不改变现有 Cloudflare production security profile，也不创建新的独立项目。

## 1. 研究问题

真实 `epistemology-textbook` pilot 已形成一条可重复的外部 provider 接入链：

```text
Human
  |
  | identity / permission / high-impact approval
  v
Machine operator / AI Agent
  |
  +--> reads repository integration intent
  +--> configures provider
  +--> validates build/deployment
  +--> inspects provider actual state
  +--> reconciles verified state back to repository
  |
Repository
  |
  +--> canonical source
  +--> provider-independent publication gate
  +--> machine-readable integration intent
  +--> readiness / reconciliation state
  +--> nontechnical authorization guide
  |
External Provider
  |
  +--> account-side actual state
```

研究问题是：这一模式是否已经稳定到足以从“Cloudflare setup”提升为可复用规范，以及它应归属于 PPF、AHICP、Academic Vault 还是新的独立项目。

## 2. 与既有工程模式的关系

这个模式不是从零开始的新型基础设施范式。

它与以下成熟模式具有明显结构同构：

- **GitOps**：声明式 desired state、版本化状态、自动获取与持续 reconciliation；
- **Kubernetes controller**：比较 desired state 与 actual state，并通过 control loop 缩小差异；
- **Infrastructure as Code / Terraform**：configuration -> plan -> apply，并通过 provider API 对真实资源执行变更；
- **OAuth delegated authorization**：资源所有者完成人类授权，机器在授予 scope 内使用独立 credential，而不是共享用户密码。

PPF pilot 的新增组合重点不在“发明 reconciliation”，而在把以下边界同时放进个人出版基础设施：

1. repository-owned publication quality gate；
2. provider integration intent 与 provider actual state 分离；
3. human authorization boundary；
4. AI / automation 可直接消费的 machine contract；
5. 对实际 account-side state 的验证与 repository write-back；
6. 面向零技术背景操作者的最小授权 handoff；
7. publication authorization、deployment readiness 与 production cutover 的分离。

因此当前更准确的定位是：

> **对 GitOps / controller / delegated-authorization 思想在个人出版 provider integration 中的组合性特化，而不是一个已经证明独立的新基础设施学科。**

## 3. 当前判断

### 3.1 不创建新的独立项目

当前只有一个 provider（Cloudflare）完成了完整 account-side pilot。

虽然概念可以抽象到其他 provider，当前证据还不足以证明：

- provider 间差异不会改变核心 contract；
- publishing 之外的 domain 仍需要同一组对象；
- 一个独立项目不会与 GitOps / IaC / deployment automation 形成不必要的概念重叠。

因此当前不支持建立新的大型独立开源项目。

### 3.2 PPF 是主要归属，但先保持为 reference/specification research

最合适的近期路径是：

```text
PPF
  |
  +--> Provider Integration Contract
  +--> Repository-Owned Publication Gate
  +--> Integration Intent vs Provider Actual State
  +--> Readiness State
  +--> Account-Side Reconciliation
  +--> Provider Security Profile
  +--> Human Authorization Boundary (publishing specialization)
  +--> Reference Providers
          |
          +--> Cloudflare
          +--> future provider(s)
```

当前应保持为 **reference implementation / design-note 层**。

只有经过第二个真实 provider pilot 后，才考虑 Promotion 为正式 **Provider Integration Specification**。

### 3.3 AHICP 只应承载通用执行原则

以下原则并不只属于 publishing：

> 在任务已经获得适当人类授权的前提下，AI / automation 应先穷尽当前可用、被授权的 machine-operable path，再把纯操作步骤交还给人类；但不得绕过身份、权限或高影响批准边界。

建议暂定名称：

**Machine-Operable-First Escalation**

它表达的是 escalation policy，而不是 provider lifecycle。

如果以后进入 AHICP，应只规定一般职责边界：

**Machine / AI：**
- discover；
- inspect；
- compare；
- configure；
- validate；
- reconcile；
- document；
- recover（在授权范围内）。

**Human：**
- identity authorization；
- permission grant / scope approval；
- high-impact irreversible approval；
- public / canonical cutover approval；
- 其他需要人类责任主体判断的决定。

AHICP 不应复制 PPF 的 provider readiness、publication gate、Custom Domain 或 release semantics。

### 3.4 Academic Vault 不应成为 infrastructure-operations layer

Vault 当前职责是：

- portfolio registry；
- publication authorization；
- deployment registry；
- cross-project routing / governance。

它可以记录：

```text
current provider
target provider
staging/readiness
production URL
verified project-local state
```

但不应成为：

- provider machine contract 的 canonical source；
- account configuration engine；
- token / permission policy 的第二真值源；
- 项目 deployment runbook 的替代品。

因此 option D 只适合作为 **portfolio-level observability / registry**，不适合作为 operations implementation layer。

## 4. 术语判断

### 4.1 Provider Integration Contract

**建议正式保留。**

含义：repository 中描述 provider integration intent 的 machine-readable contract。

它不是 provider-native config，也不是 provider actual state。

### 4.2 Repository-Owned Publication Gate

**建议正式保留。**

含义：由 repository 自己定义、与 provider 解耦的 build / validation gate。

GitHub Actions、Cloudflare 或未来 provider 调用同一个 gate。

### 4.3 Integration Intent vs Provider Actual State

**建议正式命名。**

比单独使用 “desired state” 更谨慎，因为当前 `cloudflare-builds.yaml` 并不具备完整 IaC controller 的自动 reconciliation 语义。

推荐区分：

- **Integration Intent** — repository 期望怎样接入 provider；
- **Provider Actual State** — provider account 当前真实配置与运行结果。

### 4.4 Readiness State

**建议正式保留。**

它表示是否满足进一步 deployment / cutover 的条件，不等于 active deployment，也不等于 publication permission。

### 4.5 Account-Side Reconciliation

**建议作为 process term 保留。**

流程：

```text
read repository intent
-> inspect provider actual state
-> compare
-> configure if authorized
-> validate
-> record verified state
```

### 4.6 Human Authorization Boundary

**建议保留，但属于 cross-layer term。**

PPF 使用它描述 publishing provider integration 中的人类授权边界；AHICP 若采用，只规定更一般的 AI/human authority split。

### 4.7 Agent-Operable Infrastructure

**暂不作为 PPF 正式核心术语。**

原因：

- PPF 必须保持 AI-neutral；
- “infrastructure” 范围过大；
- 当前只验证 publishing provider integration。

在 PPF 内更合适的术语是：

**Machine-Operable Provider Integration**

AI Agent 是一种 machine operator，而不是 PPF 合规的必要条件。

### 4.8 Zero-Technical-Background Handoff

**建议保留为 documentation/profile term，而不是核心架构对象。**

它描述人类 handoff 文档的 usability 目标：

- 不要求理解 API / CI / CLI；
- 只要求完成账户所有者必须亲自做的授权或批准；
- 其余步骤尽量由工具或 Agent 执行。

### 4.9 Least-Human-Intervention Operations

**不建议作为正式术语。**

“最少人类介入”容易把目标误解为排除人类。

更准确的候选表达：

**Authority-Bounded Automation**

目标不是减少人类本身，而是：

> 把人类 attention 保留给真正需要 human authority 的动作。

## 5. PPF 的候选 Provider Integration Reconciliation Loop

非规范候选模型：

```text
Canonical Source
      |
      v
Repository-Owned Publication Gate
      |
      v
Provider Integration Contract
      |
      v
Machine / Human Operator
      |
      +--> Provider Configuration
      +--> Build / Preview / Deploy
      +--> Runtime Verification
      |
      v
Provider Actual State
      |
      v
Account-Side Reconciliation
      |
      v
Repository Readiness / Evidence Update
```

Human Authorization Boundary 横切整个 loop，但只在需要 human authority 的节点阻断自动执行。

## 6. 为什么当前不应直接提升为完整 GitOps / IaC

当前 PPF contract：

- 不一定由 provider 自动 pull；
- 不一定存在常驻 controller；
- 不保证持续自动修复 drift；
- 不持有 provider 的完整资源模型；
- 允许部分 provider actual state 只能通过 inspection 后写回。

因此不应把它直接称为 GitOps implementation 或完整 Infrastructure as Code。

更准确的是：

**repository-grounded provider integration + explicit reconciliation**

未来某个 reference provider 可以使用 Terraform / Pulumi / GitOps controller，但 PPF 不应强制这些实现。

## 7. Promotion criteria

### 7.1 Promotion 到 PPF Provider Integration Specification

至少满足：

1. 第二个真实 publishing provider 完成 end-to-end pilot；
2. 同一组抽象对象在两个 provider 中仍成立；
3. Provider Integration Contract 能区分 provider-neutral fields 与 provider-specific fields；
4. preview / production / rollback / cutover semantics 可以形成稳定最小公约数；
5. readiness 与 actual-state reconciliation 至少各有一次真实 drift / mismatch 修复案例；
6. 文档不依赖 Cloudflare 专有 UI 名称才能理解。

### 7.2 Promotion 到 AHICP 通用原则

至少确认：

1. 该原则在 publishing 之外也有真实任务证据；
2. 不与 AHICP 已有 human purpose / approval / responsibility 边界重复；
3. 能用一条通用 escalation rule 表达，而不引入 provider-specific lifecycle。

### 7.3 考虑独立开源项目

只有在以下条件同时出现后再讨论：

1. 至少两个非 publishing domain 使用同一模式；
2. 存在独立于 PPF 的 machine contract / reconciliation semantics；
3. 有明确用户群不需要 PPF 但需要该模式；
4. 与 GitOps / IaC / generic agent tooling 的边界能够清楚说明；
5. 独立项目能减少而不是增加重复治理。

## 8. 可推广范围：当前结论

### 已有较强证据

- publishing provider integration；
- project websites；
- static / knowledge-site hosting；
- academic publication Web delivery。

### 结构上可能适用，但尚未实证

- research infrastructure；
- data hosting；
- software deployment；
- academic workflow services；
- AI-operated personal infrastructure。

这些领域与本模式有结构相似性，但不能仅凭类比就宣称 PPF 应扩张到这些领域。

如果未来范围明显超出 publication lifecycle，应该让 PPF 只保留 publishing specialization，而不是把所有 agentic infrastructure 都塞入 PPF。

## 9. 当前架构选择矩阵

- **A. PPF 正式模块/profile** — `NOT YET`；等第二 provider pilot。
- **B. PPF reference implementation / provider integration specification** — `PRIMARY PATH`；当前先以 research/design note 存在。
- **C. AHICP ↔ PPF interface pattern** — `YES, LIMITED`；AHICP 提供通用 authority/escalation 原则，PPF 提供 publishing specialization。
- **D. Academic Vault infrastructure-operations layer** — `NO`；Vault 只做 portfolio registry / reconciliation visibility。
- **E. 新独立开源项目** — `PREMATURE`。
- **F. design note / pattern language** — `CURRENT STATUS`。

## 10. 当前不改变的事项

本 research note 不改变：

- Cloudflare production security profile A / B 的人类选择门；
- GitHub Pages current production；
- Custom Domain / DNS；
- canonical URL；
- release approval；
- PPF AI-neutral 原则；
- AHICP normative specification；
- Academic Vault 的职责边界。

它只提供下一阶段架构研究的可审计起点。


## 11. 外部参考锚点

本 note 的概念比较基于以下公开工程规范/文档作为参照，而不是把它们当作 PPF 的规范来源：

- OpenGitOps Principles — <https://opengitops.dev/>
- Kubernetes Controllers — <https://kubernetes.io/docs/concepts/architecture/controller/>
- Terraform provisioning workflow — <https://developer.hashicorp.com/terraform/cli/run>
- OAuth 2.0 Authorization Framework (RFC 6749) — <https://www.rfc-editor.org/rfc/rfc6749>
- Model Context Protocol 2026-07-28 release overview — <https://blog.modelcontextprotocol.io/posts/2026-07-28/>

这些来源用于说明 desired/actual reconciliation、plan/apply、delegated authorization 与 agent-tool authorization 的既有技术背景；PPF 的具体术语与边界仍由 PPF 自己定义。
