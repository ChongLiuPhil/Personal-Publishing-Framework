# Provider Integration Pattern — Research Note

**Status:** `AI-PROPOSED / NON-NORMATIVE / RESEARCH NOTE`  
**Research date:** 2026-09-19  
**Scope:** PPF reference implementation / cross-layer architecture research

> This file records an infrastructure pattern that has not been promoted into normative PPF. It is not a human-approved PPF Core decision, does not change the current Cloudflare production security profile, and does not create a new standalone project.

## 1. Research question

The real `epistemology-textbook` pilot has produced a repeatable external-provider integration path:

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

The question is whether this should be promoted beyond a Cloudflare setup pattern, and whether its proper home is PPF, AHICP, Academic Vault, or a new standalone project.

## 2. Relationship to established engineering patterns

This is not a new infrastructure paradigm from first principles.

It is structurally related to:

- **GitOps**: declarative desired state, versioned state, automated retrieval, and reconciliation;
- **Kubernetes controllers**: comparing desired state with actual state and using a control loop to reduce the difference;
- **Infrastructure as Code / Terraform**: configuration -> plan -> apply through provider APIs;
- **OAuth delegated authorization**: the resource owner performs the human authorization step and machines operate with scoped credentials rather than shared passwords.

The PPF pilot's distinctive combination is not the invention of reconciliation itself, but bringing the following boundaries together for personal publishing infrastructure:

1. a repository-owned publication quality gate;
2. separation of provider integration intent from provider actual state;
3. a human authorization boundary;
4. a machine contract directly consumable by AI or automation;
5. verification of real account-side state and repository write-back;
6. minimal handoff for a zero-technical-background account owner;
7. separation of publication authorization, deployment readiness, and production cutover.

The current best description is therefore:

> **a publishing-specific composition of GitOps/controller/delegated-authorization ideas, not yet evidence for a separate infrastructure discipline.**

## 3. Current conclusion

### 3.1 Do not create a new standalone project

Only one provider, Cloudflare, has completed a full account-side pilot.

There is not yet enough evidence that:

- provider differences will preserve the same contract;
- non-publishing domains require the same objects;
- a new project would not duplicate GitOps, IaC, or deployment-automation concepts.

A new large open-source project is therefore premature.

### 3.2 PPF is the primary home, initially at reference/specification-research level

The most appropriate near-term structure is:

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

For now this should remain at the **reference implementation / design-note layer**.

Only after a second real provider pilot should PPF consider promoting it into a formal **Provider Integration Specification**.

### 3.3 AHICP should carry only the general execution rule

The following principle is not publishing-specific:

> Once a task has appropriate human authorization, AI / automation should exhaust currently available and authorized machine-operable paths before handing purely operational steps back to the human; it must not bypass identity, permission, or high-impact approval boundaries.

Provisional name:

**Machine-Operable-First Escalation**

This is an escalation policy, not a provider lifecycle.

If later adopted by AHICP, its general split should remain:

**Machine / AI:**
- discover;
- inspect;
- compare;
- configure;
- validate;
- reconcile;
- document;
- recover within granted authority.

**Human:**
- identity authorization;
- permission grant / scope approval;
- high-impact irreversible approval;
- public / canonical cutover approval;
- other decisions that require a human responsibility bearer.

AHICP should not duplicate PPF provider-readiness, publication-gate, Custom Domain, or release semantics.

### 3.4 Academic Vault should not become an infrastructure-operations layer

The Vault is responsible for:

- portfolio registry;
- publication authorization;
- deployment registry;
- cross-project routing / governance.

It may record:

```text
current provider
target provider
staging/readiness
production URL
verified project-local state
```

It should not become:

- the canonical source of provider machine contracts;
- the account configuration engine;
- a second truth source for token / permission policy;
- a replacement for project deployment runbooks.

Option D is therefore appropriate only for **portfolio-level observability / registry**, not operations implementation.

## 4. Terminology assessment

### 4.1 Provider Integration Contract

**Keep as a formal candidate term.**

Meaning: a machine-readable repository contract describing provider integration intent.

It is neither provider-native configuration nor provider actual state.

### 4.2 Repository-Owned Publication Gate

**Keep as a formal term.**

Meaning: a provider-independent build / validation gate defined by the repository.

GitHub Actions, Cloudflare, and future providers call the same gate.

### 4.3 Integration Intent vs Provider Actual State

**Name explicitly.**

This is more precise than using “desired state” alone because the current `cloudflare-builds.yaml` is not a complete IaC controller with continuous reconciliation semantics.

Recommended distinction:

- **Integration Intent** — how the repository expects to integrate with the provider;
- **Provider Actual State** — the provider account's real configuration and runtime result.

### 4.4 Readiness State

**Keep as a formal term.**

It represents whether prerequisites for further deployment / cutover are satisfied. It is not active deployment and not publication permission.

### 4.5 Account-Side Reconciliation

**Keep as a process term.**

```text
read repository intent
-> inspect provider actual state
-> compare
-> configure if authorized
-> validate
-> record verified state
```

### 4.6 Human Authorization Boundary

**Keep as a cross-layer term.**

PPF uses it for publishing-provider integration. AHICP, if it later adopts the concept, should specify only the general AI/human authority split.

### 4.7 Agent-Operable Infrastructure

**Do not make it a formal PPF core term yet.**

Reasons:

- PPF must remain AI-neutral;
- “infrastructure” is too broad;
- only publishing-provider integration has been validated.

A better PPF term is:

**Machine-Operable Provider Integration**

An AI agent is one possible machine operator, not a PPF conformance requirement.

### 4.8 Zero-Technical-Background Handoff

**Keep as a documentation/profile term rather than a core architecture object.**

It describes a usability goal for human handoff:

- no need to understand APIs / CI / CLI;
- only account-owner authorization or approval should be required;
- other steps should be performed by tools or agents where possible.

### 4.9 Least-Human-Intervention Operations

**Do not adopt as a formal term.**

“Least human intervention” can misstate the goal as removing humans.

A better candidate is:

**Authority-Bounded Automation**

The goal is:

> reserve human attention for actions that genuinely require human authority.

## 5. Candidate PPF Provider Integration Reconciliation Loop

Non-normative candidate:

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

The Human Authorization Boundary cuts across the loop but blocks automation only at points that require human authority.

## 6. Why this should not yet be called full GitOps / IaC

The current PPF contract:

- is not necessarily pulled automatically by the provider;
- does not necessarily have a resident controller;
- does not guarantee continuous drift repair;
- does not model the provider's complete resource graph;
- permits some provider actual state to be learned by inspection and then written back.

It should therefore not be described as a complete GitOps implementation or Infrastructure as Code system.

A more accurate description is:

**repository-grounded provider integration + explicit reconciliation**

A future reference provider may use Terraform, Pulumi, or a GitOps controller, but PPF should not require those implementations.

## 7. Promotion criteria

### 7.1 Promotion into a PPF Provider Integration Specification

Require at least:

1. a second real publishing provider end-to-end pilot;
2. the same abstraction objects remain useful across both providers;
3. the Provider Integration Contract separates provider-neutral and provider-specific fields;
4. preview / production / rollback / cutover semantics have a stable minimum common denominator;
5. readiness and actual-state reconciliation each have at least one real drift / mismatch repair case;
6. the documentation can be understood without Cloudflare-specific UI names.

### 7.2 Promotion into a general AHICP principle

Require at least:

1. real evidence outside publishing;
2. no duplication of AHICP's existing human purpose / approval / responsibility boundaries;
3. the concept can be stated as one general escalation rule without provider-specific lifecycle semantics.

### 7.3 Consideration of a standalone open-source project

Only discuss after all of the following:

1. at least two non-publishing domains use the same pattern;
2. machine-contract / reconciliation semantics exist independently of PPF;
3. there is a clear user group that needs the pattern without PPF;
4. the boundary from GitOps / IaC / generic agent tooling can be stated clearly;
5. separation reduces rather than increases governance duplication.

## 8. Generalization boundary: current conclusion

### Stronger evidence already exists for

- publishing-provider integration;
- project websites;
- static / knowledge-site hosting;
- academic-publication Web delivery.

### Structurally plausible but not yet validated

- research infrastructure;
- data hosting;
- software deployment;
- academic workflow services;
- AI-operated personal infrastructure.

These areas are structurally similar, but analogy alone is not evidence that PPF should expand into them.

If future scope clearly exceeds publication lifecycle, PPF should retain only the publishing specialization rather than absorb all agentic infrastructure.

## 9. Current option matrix

- **A. Formal PPF module/profile** — `NOT YET`; wait for the second provider pilot.
- **B. PPF reference implementation / provider integration specification** — `PRIMARY PATH`; currently a research/design note.
- **C. AHICP ↔ PPF interface pattern** — `YES, LIMITED`; AHICP provides a general authority/escalation principle while PPF specializes it for publishing.
- **D. Academic Vault infrastructure-operations layer** — `NO`; the Vault remains portfolio registry / reconciliation visibility.
- **E. New standalone open-source project** — `PREMATURE`.
- **F. Design note / pattern language** — `CURRENT STATUS`.

## 10. Things this note does not change

This research note does not change:

- the human choice between Cloudflare production security profiles A / B;
- GitHub Pages as current production;
- Custom Domain / DNS;
- canonical URL;
- release approval;
- PPF's AI-neutral principle;
- the AHICP normative specification;
- the Academic Vault responsibility boundary.

It only provides an auditable starting point for the next architecture-research phase.


## 11. External reference anchors

This note uses the following public engineering specifications and documentation as comparison points, not as normative PPF sources:

- OpenGitOps Principles — <https://opengitops.dev/>
- Kubernetes Controllers — <https://kubernetes.io/docs/concepts/architecture/controller/>
- Terraform provisioning workflow — <https://developer.hashicorp.com/terraform/cli/run>
- OAuth 2.0 Authorization Framework (RFC 6749) — <https://www.rfc-editor.org/rfc/rfc6749>
- Model Context Protocol 2026-07-28 release overview — <https://blog.modelcontextprotocol.io/posts/2026-07-28/>

These references establish existing technical background for desired/actual reconciliation, plan/apply workflows, delegated authorization, and agent-tool authorization. PPF terminology and scope remain defined by PPF itself.
