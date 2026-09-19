# Provider Integration Semantic Migration — 2026-09-19

**状态：** HUMAN-APPROVED / NORMATIVE MIGRATION AUDIT  
**范围：** PPF provider-neutral semantics only

## 人类授权

人类项目责任人在 2026-09-19 明确要求把近期真实 provider pilot 中已经稳定、且不依赖 Cloudflare 专有实现的原则迁移为持久 PPF 规范，并要求：

- 不把 provider-specific UI / token / command 细节写入 normative core；
- 不把 AI/MCP 变成 PPF conformance requirement；
- 不把 provider build success 当作 formal production approval；
- 不把 publication permission 与 deployment state 合并；
- 不把 upstream PPF 更新静默视为 downstream 已采用。

## 本次 Promotion

本次 normative migration 只 Promotion 以下 provider-neutral invariants：

1. Repository Integration Intent、Provider Actual State、Human Authorization State 必须区分；
2. provider production branch 不等于 canonical publication production；
3. 通用 readiness vocabulary 是可映射 milestone，不是刚性单一路径 state machine；
4. runtime verification 是 cutover 前 first-class gate；
5. provider action 后应验证 actual state 并 write back durable repository state；
6. canonical production cutover 是显式 gate；
7. 已有 public production URL 在迁移时需要明确 legacy URL policy；
8. downstream adoption 应记录 upstream version/tag/immutable commit，后续 upstream 变化不得自动视为已采用。

## 未 Promotion

以下仍留在 reference implementation / dated observation / research note：

- Cloudflare UI 字段和菜单；
- Workers Builds token 产品限制；
- Profile A/B/C 的 Cloudflare-specific 实现；
- 具体 Wrangler / Quarto / Node 版本；
- 具体 build/deploy commands；
- Cloudflare MCP/OAuth 路径；
- 完整 Provider Integration Reconciliation Loop 作为正式独立 specification。

完整 architecture research 仍见 `docs/PROVIDER_INTEGRATION_PATTERN_RESEARCH.zh-CN.md`，其状态继续为 `AI-PROPOSED / NON-NORMATIVE / RESEARCH NOTE`，直到 promotion criteria 被满足。

## 验证要求

本迁移要求：

- 中文 canonical / 英文 mirror 同步；
- `schema/publishing.schema.json` 正式识别 adoption metadata 与通用 provider state 字段；
- Reference Template CI 实际用 JSON Schema 验证 reference `publishing.yaml`；
- 当前 reference template 在 schema 扩展后保持兼容。
