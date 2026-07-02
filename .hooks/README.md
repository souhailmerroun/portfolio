# Hooks — code quality + safety

This folder's hooks ship with the repo and apply to every clone via
`core.hooksPath = .hooks`.

## Required per-clone setup

Run **once after clone** on every machine:

```sh
cd <this-repo>
./.hooks/setup.sh
```

This sets `core.hooksPath = .hooks` so the hooks in this folder run on commit/push.

## Hooks shipped

### `pre-commit`
Code quality — blocks:
1. `.env` files
2. `.DS_Store` — blocks staging and auto-removes any already tracked
3. Merge conflict markers
4. Invalid JSON
5. Large files (>10 MB)
6. Common secret patterns (AWS keys, GitHub tokens, Slack tokens)
7. Inline JS/CSS in HTML (must use external `.js` / `.css` files)
8. Files exceeding line-count limits per extension
9. Missing version bump in `package.json` when app code changes

### `pre-push`
Safety — blocks force-push to any branch to prevent history erasure.
