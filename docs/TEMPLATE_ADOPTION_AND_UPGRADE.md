# PPF Reference Template Adoption and Upgrade

The executable reference implementation lives in `templates/quarto-book/`. Its machine-readable ownership and upgrade boundaries are defined by `template-manifest.yaml`.

Upgrade tooling must distinguish upstream-managed, merge-managed, and project-owned paths. Project source content, references, assets, project-specific validators, human publication decisions, canonical identity, and provider actual state must never be silently overwritten by a PPF template upgrade.

A downstream upgrader should use the adopted PPF commit as the merge base, compare current project state with the target template revision, open a PR, and pass the project's existing publication and runtime gates.
