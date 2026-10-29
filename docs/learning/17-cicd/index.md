# CI/CD Pipelines

Continuous integration builds and tests every change; continuous delivery and deployment move tested changes toward production in a controlled, repeatable way. This section covers the branching workflows that shape how changes arrive, the CI tools and quality gates that check them, and the deployment strategies and infrastructure-as-code that ship them.

---

## Topics

### [Git Workflows](git-workflows.md)
**branches - rebase - Git Flow - GitHub Flow - trunk-based development - code review**
The Git operations behind daily work, and the branching models teams use to decide how changes reach main.

### [Continuous Integration](continuous-integration.md)
**GitHub Actions - Jenkins - GitLab CI - quality gates - SAST - DAST - SCA - artifact repositories**
Automated builds and tests, pipeline definitions across the major CI tools, and security and quality checks inside the pipeline.

### [Continuous Deployment and IaC](continuous-deployment-iac.md)
**blue-green - canary - rolling - shadow - Terraform - CloudFormation - Ansible - rollback**
Safe release strategies, infrastructure defined as code, secrets handling in pipelines, and post-deployment verification.

### More in this section

### [Git: Pull, Merge, Rebase, and Renames](git-pull-merge-rebase.md)
**Core concepts - How it works / Step by step - Worked example: resolving a conflict during a rebase - Common pitfalls - Quick recap**
Git history is how a team understands what changed and why. Interviewers ask about `pull` versus `rebase`, and about merging versus rebasing, because the choice affects the...

