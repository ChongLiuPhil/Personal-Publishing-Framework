# Publication Visibility, Access Policy, and Canonical Identity Migration — 2026-09-19

**状态：** HUMAN-APPROVED / NORMATIVE MIGRATION AUDIT  
**范围：** PPF provider-neutral publication semantics

## 人类授权

项目责任人明确批准把以下真实需求迁移为 PPF 持久规范：

- source repository 是否公开，不应决定 Web publication 是否公开；
- publication 是否获准发布，与 publication 面向谁可见必须分开；
- restricted/private Web publication 需要一等 access-policy 语义；
- provider-native endpoint 与长期 canonical publication identity 必须分开；
- provider-specific access 产品、password/OTP/SSO、GitHub Free 等产品限制不得写入 normative core。

## 本次 Promotion

本次正式 Promotion：

1. **Source / Repository Visibility**
2. **Publication Authorization**
3. **Publication Visibility**
4. **Access Policy**
5. **Canonical Publication Identity**

PPF 明确禁止以下自动推断：

~~~text
public source => public publication
private source => private publication
publication authorized => unrestricted public access
deployed runtime => canonical URL
provider endpoint => canonical identity
~~~

## Provider-neutral vocabulary

Publication visibility：

- `public`
- `restricted`
- `private`

Access mode：

- `none`
- `authenticated`
- `selected-audience`
- `other`

Canonical identity type：

- `provider-native`
- `custom-domain`
- `other`

这些是最小语义层，不规定具体 provider 产品。

## 未 Promotion

以下继续留在 reference implementation 或 dated provider documentation：

- Cloudflare Access；
- Cloudflare One / Zero Trust；
- email OTP / one-time PIN；
- 具体 password protection 产品；
- GitHub Free / paid plan 的 Pages 产品限制；
- `workers.dev` 是否适合某类 production；
- 具体 DNS / Custom Domain UI；
- 某个项目应选哪个 canonical domain。

## Secret boundary

Access policy metadata 只描述 mode / implementation / policy reference。

Password、token、private key、recovery code、session secret 等不得写入 publication contract。

## Schema migration

`schema/publishing.schema.json` 新增的字段全部 optional，因此：

- 保持 `schema: ppf/v0.1`；
- 现有 downstream contract 继续可验证；
- 项目只有在明确采用新的 upstream revision 时，才把这些字段视为其 adopted PPF state；
- upstream merge 不自动更新任何 downstream adopted commit。
