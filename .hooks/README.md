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
Code quality + safety — blocks:
0. **Direct commits on `main`/`master`** — main is merge-only; branch first
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
Safety — blocks:
- **Direct pushes to `main`/`master`** — main is updated only via GitHub merge
- Force-push to any branch (prevents history erasure)

## Workflow

`main` is protected: you cannot commit or push to it directly. All work flows
through short-lived feature branches merged on GitHub.

```sh
git checkout -b a/<task>     # branch off main (prefix per machine: a/… , b/…)
# ...work, commit...
git ship                     # push branch → open PR → squash-merge → back on updated main
```

`git ship` is a global alias (see `git config --global --get alias.ship`); run
the same `git config` command on each machine to install it.
