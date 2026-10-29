# Git Workflows

Git stores history as a graph of commits, and a branching workflow decides how that history grows. Interviewers ask about workflows to test whether you can explain the trade-offs between long-lived release branches, short-lived feature branches, and trunk-based development, and whether you can use merge and rebase deliberately.

## Core concepts

### Branches, commits, and merges
A **commit** is a snapshot of the project plus a pointer to its parent commit. A **branch** is a movable pointer to a commit. Creating a branch costs almost nothing, which makes short-lived branches practical.

```bash
git switch -c feature/order-totals      # create and switch to a branch
git add -p                              # stage hunks interactively
git commit -m "Add order total calculation"
git push -u origin feature/order-totals
```

A **merge** joins two histories with a new merge commit that has two parents. Merging keeps the full history of both branches.

### Rebasing
A **rebase** replays your commits on top of a new base. It produces a linear history without merge commits, but it creates new commit IDs. Never rebase commits that others have already built on, and never rebase a shared branch that others are pulling.

```bash
git fetch origin
git rebase origin/main          # replay local commits on the latest main
```

Rule of thumb: rebase your own feature branch to keep it current, then merge it into the shared branch.

### Git Flow
**Git Flow** defines long-lived branches and several short-lived ones:

- `main` holds released code.
- `develop` collects work for the next release.
- `feature/*` branches start from `develop` and merge back into it.
- `release/*` branches stabilise a release, and merge into both `main` and `develop`.
- `hotfix/*` branches start from `main` to fix production, then merge into `main` and `develop`.

Git Flow suits software with scheduled, versioned releases, such as installable products or libraries with several supported versions. For a service deployed continuously, it adds ceremony without much benefit.

### GitHub Flow
**GitHub Flow** keeps only `main`, plus short-lived feature branches. You branch, commit, open a pull request, get review and CI results, then merge to `main`. Every merge to `main` is expected to be deployable.

### Trunk-based development
**Trunk-based development** pushes the idea further. Developers integrate into the trunk (main) very frequently, usually in less than a day, through very short-lived branches or directly. Incomplete features are hidden behind **feature flags** so the trunk always builds and stays releasable.

The main benefit is fast feedback and little merge pain. It depends on strong automated tests and a team habit of small, frequent changes.

### Choosing a model

| Model | Branch lifetime | Release style | Good fit |
|---|---|---|---|
| Git Flow | Long-lived `develop` and release branches | Scheduled, versioned | Packaged software with several supported versions |
| GitHub Flow | Short-lived feature branches | Continuous from `main` | Web services with frequent deploys |
| Trunk-based | Hours, or direct commits | Continuous, often behind flags | Teams with strong automated tests |

### Commit messages
A consistent commit message makes history searchable and can drive tooling. The **Conventional Commits** style uses a type and optional scope, such as `feat(orders): add discount rule`, followed by a short summary, an optional body explaining why, and footers such as issue references. Keep the subject line short and in the imperative mood.

### Code review practice
Pull requests are the usual place for review. Good practice includes small, focused changes, a description that explains the reason for the change, automated checks that must pass before merge, at least one reviewer who did not write the code, and comments that ask questions or suggest concrete fixes. Protected branches enforce these rules.

### Merge strategies on pull requests
Hosting platforms offer several ways to merge a pull request:

- **Merge commit**: keeps every commit from the branch and adds a merge commit. The history shows exactly when the branch joined.
- **Squash**: combines the branch into one commit on the target. The history reads as one entry per change, and intermediate "fix typo" commits disappear.
- **Rebase and merge**: replays the branch commits linearly onto the target, with no merge commit.

Squash merges suit feature branches with messy history. Merge commits suit branches where the individual commits carry useful history. Choose one per repository and keep it consistent.

### Resolving conflicts
A conflict happens when two branches change the same lines. Git marks the conflicting region in the file, and you choose the correct content, remove the markers, then stage and continue:

```bash
git fetch origin
git rebase origin/main        # or: git merge origin/main
# edit the conflicted files, then:
git add path/to/conflicted-file.java
git rebase --continue         # or: git commit, after a merge
```

If the rebase becomes messy, `git rebase --abort` returns the branch to its state before the rebase started. Run the test suite after resolving conflicts, because a clean merge can still break behaviour.

### Protecting shared branches
Platforms let you protect `main` so that changes arrive only through pull requests, with required reviews and passing CI checks. A `CODEOWNERS` file assigns reviewers by path, so changes to a sensitive module reach the right people. Protection rules back up the team's habits; they do not replace them.

### Everyday commands worth knowing

```bash
git log --oneline --graph --decorate   # see branch and merge structure
git stash push -m "wip"                # set work aside temporarily
git cherry-pick <commit-sha>           # copy one commit onto the current branch
git restore --staged <file>            # unstage without losing edits
```

### Commit hygiene and rewriting history
Before opening a pull request, tidy your own unpublished commits. `git commit --amend` changes the most recent commit, and `git rebase -i` (run in a normal terminal, since it opens an editor) lets you squash, reword, or reorder your own commits. Once a branch is pushed and others use it, avoid rewriting it. If you must update a pushed branch you own, `git push --force-with-lease` refuses the push when someone else has pushed in the meantime, which prevents silently overwriting their work.

Keep commits atomic: each should compile and pass tests on its own where practical. That makes `git bisect` useful when a regression appears later.

### Working with remotes
`git fetch` downloads new commits and updates the remote-tracking branches (such as `origin/main`) without touching your working files. `git pull` is a fetch followed by a merge, or a rebase if configured. Fetching first and then deciding how to integrate is the safer habit, because you see what changed before it touches your branch.

```bash
git fetch --prune              # download changes and remove deleted remote branches locally
git branch -vv                 # show which local branches track which remote branches
git push -u origin HEAD        # publish the current branch and set its upstream
```

### Branch naming and lifetime
Short, consistent branch names help everyone see what a branch is for. A common pattern is a type prefix and a ticket or topic, such as `feature/order-totals` or `fix/checkout-timeout`. Delete branches after merging, so the list of open branches shows only work in progress. A branch that has lived for weeks is a signal to split the change or to merge a smaller first step.

### Review checklist
- Does the description explain why the change exists and how it was tested?
- Is the change small enough to review in one sitting?
- Do tests cover the new behaviour and the important failure cases?
- Are there secrets, debug logs, or commented-out code?
- Does the change break a public contract or a database migration order?

## How it works / Step by step
1. A developer branches from the latest `main`.
2. They commit small, focused changes with clear messages.
3. They push and open a pull request; CI runs on it.
4. A reviewer checks the change; the author addresses comments, possibly with a rebase.
5. The change merges into `main`, which triggers the deployment pipeline.

## Common pitfalls
- Rebasing a branch that others already pulled, which forces painful reconciliation.
- Leaving feature branches open for weeks, which makes merges risky.
- Using `git push --force` on a shared branch. Use `--force-with-lease` on your own branch if you must.
- Committing secrets, then "removing" them in a later commit. The value stays in history and must be rotated.
- Using Git Flow for a service that deploys continuously, which adds release-branch overhead.
- Approving pull requests without reading them, which defeats the purpose of review.

!!! tip "Interview tip"
    **Q: When would you use merge instead of rebase?**
    Merge when the history of a shared branch must be preserved, such as integrating a feature into `main`. Rebase your own unpublished or personal branch to keep it current and tidy. The rule is to avoid rewriting history that other people have based work on.

## Quick recap
- Branches are cheap pointers; merges keep history, while rebases rewrite it linearly.
- Git Flow suits scheduled releases; GitHub Flow suits continuous deployment from `main`.
- Trunk-based development relies on small changes, feature flags, and strong tests.
- Conventional commit messages and focused pull requests make history and review easier.
- Never rewrite shared history, and keep secrets out of commits entirely.

**See also:** [Continuous Integration](continuous-integration.md), [Continuous Deployment and IaC](continuous-deployment-iac.md), [Build Tools](../05-build-tools/index.md)
