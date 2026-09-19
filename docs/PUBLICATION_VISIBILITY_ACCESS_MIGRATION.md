# Publication Visibility, Access Policy, and Canonical Identity Migration — 2026-09-19

**Status:** HUMAN-APPROVED / NORMATIVE MIGRATION AUDIT  
**Scope:** PPF provider-neutral publication semantics

## Human authorization

The project owner explicitly approved promoting the following real requirements into durable PPF norms:

- source-repository visibility must not determine Web-publication visibility;
- authorization to publish must remain distinct from who may view a publication;
- restricted/private Web publication needs first-class access-policy semantics;
- provider-native endpoints must remain distinct from long-lived canonical publication identity;
- provider-specific access products, password/OTP/SSO mechanisms, and GitHub plan limitations must remain outside the normative core.

## Promoted in this migration

This migration formally promotes:

1. **Source / Repository Visibility**
2. **Publication Authorization**
3. **Publication Visibility**
4. **Access Policy**
5. **Canonical Publication Identity**

PPF explicitly rejects these automatic inferences:

~~~text
public source => public publication
private source => private publication
publication authorized => unrestricted public access
deployed runtime => canonical URL
provider endpoint => canonical identity
~~~

## Provider-neutral vocabulary

Publication visibility:

- `public`
- `restricted`
- `private`

Access mode:

- `none`
- `authenticated`
- `selected-audience`
- `other`

Canonical identity type:

- `provider-native`
- `custom-domain`
- `other`

These are minimum semantic categories and do not prescribe a provider product.

## Not promoted

The following remain reference-implementation detail or dated provider documentation:

- Cloudflare Access;
- Cloudflare One / Zero Trust;
- email OTP / one-time PIN;
- concrete password-protection products;
- GitHub Free / paid Pages product limitations;
- whether `workers.dev` is appropriate for a particular production context;
- concrete DNS / Custom Domain UI;
- which canonical domain a particular project should choose.

## Secret boundary

Access-policy metadata describes only mode / implementation / policy reference.

Passwords, tokens, private keys, recovery codes, session secrets, and similar values must not be stored in the publication contract.

## Schema migration

All new fields in `schema/publishing.schema.json` are optional, therefore:

- `schema: ppf/v0.1` remains unchanged;
- existing downstream contracts continue to validate;
- a project treats these fields as adopted PPF state only after explicitly adopting the new upstream revision;
- an upstream merge does not automatically update any downstream adopted commit.
