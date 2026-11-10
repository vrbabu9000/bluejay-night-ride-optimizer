# CLAUDE.md

Instructions for Claude Code in the Blue Jay Night Ride optimizer repository.

## Git and GitHub ground rules

**Git and GitHub are manual. Claude never commits.**

- Claude never runs git or GitHub commands that change anything. That means no add, commit,
  push, pull, fetch, merge, rebase, reset, revert, cherry-pick, tag, stash, checkout,
  switch, branch, restore, rm, mv, clean, remote, config, init, clone or `git -C`,
  and no `gh` at all. These are blocked by deny rules in `.claude/settings.json`.
- Claude may run read-only git (`git status`, `git diff`, `git log`) to write accurate
  commit messages.
- At the end of any change, Claude gives the user:
  1. a ready-to-paste commit message, and
  2. the exact commands in ```bash code blocks, **one command per block**. The user runs them.

  Prefer `git add <specific files>` over `git add .` unless every change belongs in the commit.
- **GitHub account: vrbabu9000 only. Never vrajesh9000.**
  - Remote: `git@github.com-personal:vrbabu9000/<repo>.git` (the SSH alias for the personal key).
  - Repo-local identity: `vrbabu9000 <vrb.canada@gmail.com>`.
  - Before any push command, Claude tells the user to run `git config user.name` to confirm.
- **Commit messages follow Conventional Commits:**
  - Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `style`, `perf`, `test`.
  - Subject: short, imperative, lower case, no period, about 72 characters or fewer.
  - Body: bullets saying what changed and why.
  - If the work carries a tracked version or milestone (for example methodology v1.7, M3,
    D-50), put it in the subject in brackets.
  - No AI co-author trailer unless the user asks.
- **Branches: the user decides.** Claude may suggest a name (`feat/<thing>`, `fix/<thing>`);
  the user creates the branch.
