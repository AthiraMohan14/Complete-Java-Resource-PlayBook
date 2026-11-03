# Git Workflows

!!! note "In simple words"
    A branch is a label that points to a commit, so making one is cheap. A workflow is the team's agreement about how those branches are created, reviewed, and merged back into the main line of code.

Git stores history as a graph of commits, and a branching workflow decides how that graph grows. Interviewers ask about workflows to see whether you can explain the trade-offs between long-lived release branches, short-lived feature branches, and trunk-based development. They also check whether you use merge and rebase on purpose.

## Why it matters

When several people change the same code, the team needs rules. Without them, branches live for weeks, merges conflict badly, and nobody can say which version is in production. A good workflow keeps changes small, makes review routine, and keeps the main branch in a state that can be released. The workflow you choose also affects how often you can deploy.

## How it works

### Branches, commits, and merges

A **commit** is a snapshot of the project together with a pointer to its parent commit. A **branch** is a movable pointer to a commit. Creating a branch costs almost nothing, which makes short-lived branches practical.

```bash
git switch -c feature/order-totals      # create and switch to a branch
git add -p                              # stage chosen hunks interactively
git commit -m "Add order total calculation"
git push -u origin feature/order-totals
```

A **merge** joins two histories with a new commit that has two parents. The merge keeps the full history of both branches.

### Rebasing

A **rebase** replays your commits on top of a new base. The result is a straight line of history with no merge commit. Rebasing creates new commit IDs, though. Never rebase commits that other people have built on, and never rebase a shared branch that others pull from.

```bash
git fetch origin
git rebase origin/main          # replay local commits on the latest main
```

A useful rule of thumb: rebase your own feature branch to keep it current, then merge it into the shared branch. The detailed comparison of pull, merge, and rebase is on the Git Pull, Merge, Rebase, and Renames page.

### Git Flow

**Git Flow** defines long-lived branches and several kinds of short-lived ones:

- `main` holds released code.
- `develop` collects work for the next release.
- `feature/*` branches start from `develop` and merge back into it.
- `release/*` branches stabilise a release. They merge into both `main` and `develop`.
- `hotfix/*` branches start from `main` to repair production. They merge into `main` and `develop`.

Git Flow suits software with scheduled, versioned releases, such as installable products or libraries with several supported versions. For a service that deploys continuously, it adds ceremony without much benefit.

### GitHub Flow

**GitHub Flow** keeps only `main`, plus short-lived feature branches. You create a branch, commit, open a pull request, collect review and CI results, and merge into `main`. Every merge into `main` is expected to be deployable.

```mermaid
flowchart LR
    A[Branch from main] --> B[Commit small changes]
    B --> C[Open pull request]
    C --> D[CI checks run]
    D --> E[Review]
    E --> F[Merge into main]
    F --> G[Deploy]
```

### Trunk-based development

**Trunk-based development** goes one step further. Developers integrate into the trunk, which is `main`, very often, usually within a day. They use very short-lived branches or commit directly. Unfinished features are hidden behind **feature flags**, so the trunk always builds and stays releasable.

The main benefit is fast feedback and little merge pain. The approach depends on strong automated tests and on a team habit of making small, frequent changes.

### Choosing a model

| Model | Branch lifetime | Release style | Good fit |
|---|---|---|---|
| Git Flow | Long-lived `develop` and release branches | Scheduled and versioned | Packaged software with several supported versions |
| GitHub Flow | Short-lived feature branches | Continuous from `main` | Web services with frequent deploys |
| Trunk-based | Hours, or direct commits | Continuous, often behind flags | Teams with strong automated tests |

### Commit messages

A consistent message style makes history searchable, and tools can read it too. The **Conventional Commits** style starts with a type and an optional scope, such as `feat(orders): add discount rule`. It continues with a short summary, an optional body that explains why the change was made, and footers such as issue references. Keep the subject line short and in the imperative mood.

### Code review practice

Pull requests are where review usually happens. Good practice includes:

- Small, focused changes.
- A description that explains the reason for the change.
- Automated checks that must pass before a merge.
- At least one reviewer who did not write the code.
- Comments that ask questions or suggest a concrete fix.

Protected branches enforce these rules, so the team does not have to rely on memory.

### Merge strategies on pull requests

Hosting platforms offer several ways to merge a pull request:

- **Merge commit** keeps every commit from the branch and adds a merge commit. The history shows exactly when the branch joined.
- **Squash** combines the branch into one commit on the target. The history then has one entry per change, and small "fix typo" commits disappear.
- **Rebase and merge** replays the branch commits in a line onto the target, with no merge commit.

Squash merges suit feature branches with messy history. Merge commits suit branches whose individual commits carry useful history. Pick one strategy for each repository and keep to it.

### Resolving conflicts

A conflict happens when two branches change the same lines. Git marks the region in the file. You choose the correct content, remove the markers, stage the file, and continue:

```bash
git fetch origin
git rebase origin/main        # or: git merge origin/main
# edit the conflicted files, then:
git add path/to/conflicted-file.java
git rebase --continue         # or: git commit, after a merge
```

If a rebase becomes messy, `git rebase --abort` returns the branch to the state it had before the rebase began. Run the test suite after resolving conflicts, because a clean merge can still break behaviour.

### Protecting shared branches

Platforms let you protect `main`, so that changes arrive only through pull requests, with required reviews and passing CI checks. A `CODEOWNERS` file assigns reviewers by path, so changes to a sensitive module reach the right people. Protection rules support good habits, but they do not replace them.

### Everyday commands worth knowing

```bash
git log --oneline --graph --decorate   # see branch and merge structure
git stash push -m "wip"                # set work aside temporarily
git cherry-pick <commit-sha>           # copy one commit onto the current branch
git restore --staged <file>            # unstage without losing edits
```

### Commit hygiene and rewriting history

Before you open a pull request, tidy your own unpublished commits. `git commit --amend` changes the most recent commit. `git rebase -i` lets you squash, reword, or reorder your own commits, but it opens an editor, so run it in a normal terminal. After a branch is pushed and others use it, avoid rewriting it. If you must update a pushed branch that you own, `git push --force-with-lease` refuses the push when someone else has pushed in the meantime. That prevents you from silently overwriting their work.

Keep commits atomic, meaning each one compiles and passes tests on its own where practical. Then `git bisect` can find a regression quickly.

### Working with remotes

`git fetch` downloads new commits and updates the remote-tracking branches, such as `origin/main`, without touching your working files. `git pull` is a fetch followed by a merge, or by a rebase if you configure it that way. Fetching first and then deciding how to integrate is the safer habit, because you see what changed before it touches your branch.

```bash
git fetch --prune              # download changes and remove deleted remote branches locally
git branch -vv                 # show which local branches track which remote branches
git push -u origin HEAD        # publish the current branch and set its upstream
```

### Branch naming and lifetime

Short, consistent branch names tell everyone what a branch is for. A common pattern is a type prefix followed by a ticket or topic, such as `feature/order-totals` or `fix/checkout-timeout`. Delete branches after they merge, so the list of open branches shows only work in progress. A branch that has lived for weeks is a signal to split the change, or to merge a smaller first step.

### Review checklist

- Does the description explain why the change exists, and how it was tested?
- Is the change small enough to review in one sitting?
- Do the tests cover the new behaviour and the important failure cases?
- Are there secrets, debug logs, or commented-out code?
- Does the change break a public contract, or the order of a database migration?

## Where it is used

- Web services that deploy several times a day, which usually run GitHub Flow or trunk-based development.
- Libraries and packaged products with several supported versions, which often use Git Flow or release branches.
- Teams in regulated environments that need an approval record, which they get from protected branches and pull request reviews.

## Benefits

- Short branches keep merges small and conflicts rare.
- Pull requests create a review record and a place for automated checks.
- A single, always-releasable main branch makes deployment decisions simpler.
- Clear naming and conventional commit messages make history easy to search.

## Cons and limits

- Git Flow adds several long-lived branches to maintain, and it can delay releases.
- Trunk-based development needs feature flags and strong tests. Without them, unfinished work can reach users.
- Long-lived branches create painful merges, however the team names them.
- Protection rules can slow a small team down if they are set too strictly.

### Common pitfalls

- Rebasing a branch that others already pulled, which forces painful reconciliation.
- Leaving feature branches open for weeks, which makes merges risky.
- Using `git push --force` on a shared branch. Use `--force-with-lease` on your own branch if you must rewrite it.
- Committing a secret and then removing it in a later commit. The value stays in history, so it must be rotated.
- Using Git Flow for a service that deploys continuously, which adds release-branch overhead.
- Approving pull requests without reading them, which defeats the purpose of review.

## Best practices

- Branch from the latest `main`, and keep each branch focused on one change.
- Open pull requests early as drafts, so that feedback arrives while the work is still cheap to change.
- Protect `main`, require reviews, and require passing CI checks.
- Use feature flags for work that is merged but not yet released.
- Delete merged branches, and rebase private branches to keep them current.
- Keep secrets out of commits, and use a secret scanner in the pipeline to catch mistakes.

!!! tip "Interview tip"
    **Q: When would you use merge instead of rebase?**
    Merge when the history of a shared branch must be preserved, such as when you integrate a feature into `main`. Rebase your own unpublished or personal branch to keep it current and tidy. The rule is to avoid rewriting history that other people have based work on.

## Quick recap

- Branches are cheap pointers. Merges keep history, and rebases rewrite it into a straight line.
- Git Flow suits scheduled releases. GitHub Flow suits continuous deployment from `main`.
- Trunk-based development relies on small changes, feature flags, and strong tests.
- Conventional commit messages and focused pull requests make history and review easier.
- Never rewrite shared history, and keep secrets out of commits entirely.

## Official documentation

- [Pro Git book](https://git-scm.com/book/en/v2)
- [Git documentation](https://git-scm.com/doc)
- [git rebase reference](https://git-scm.com/docs/git-rebase)

**See also:** [Continuous Integration](continuous-integration.md), [Continuous Deployment and IaC](continuous-deployment-iac.md), [Build Tools](../05-build-tools/index.md)
