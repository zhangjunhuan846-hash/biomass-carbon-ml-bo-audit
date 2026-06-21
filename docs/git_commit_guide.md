# Git commit guide

Recommended commit message for this release:

```text
feat: harden offline BO replay skill v1.1.0
```

Longer commit body:

```text
- add objective direction control for maximize/minimize targets
- add exploit-only, diversity, and oracle upper-bound baselines
- strengthen descriptor leakage filtering and validity audit
- improve report decision logic and scientific boundary wording
- add .gitignore, package discovery, and local pytest support
- remove generated outputs and cache artifacts from release archive
```

Recommended command sequence:

```bash
git add .
git commit -m "feat: harden offline BO replay skill v1.1.0" \
  -m "Add objective direction control, secondary baselines, stricter leakage audit, improved reporting, packaging fixes, and repository hygiene."
```

If this is the first upload of the project:

```bash
git init
git add .
git commit -m "feat: add carbon literature BO replay skill"
```

If you only want a small documentation commit after code has already been committed:

```bash
git add README.md README_en.md skill.md AGENTS.md docs/
git commit -m "docs: clarify offline replay boundaries and usage"
```
