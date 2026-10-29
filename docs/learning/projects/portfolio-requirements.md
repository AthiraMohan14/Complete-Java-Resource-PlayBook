# Portfolio Requirements

A portfolio shows an employer how you work, not just what you built. Every project you publish should meet the standards below. Reviewers spend a few minutes on each repository, so the README, the commit history, and a working demo matter as much as the code.

## Checklist

Use this list before you share a project link.

### Code quality
- Clean, readable code with consistent naming and small methods
- Clear separation between layers: web, service, and data access
- No dead code, commented-out blocks, or leftover debug output
- Automated formatting and static analysis configured and passing
- Business rules covered by unit tests; integration tests for persistence and HTTP

### Documentation
- A README that explains what the project does, how to run it locally, and how to run its tests
- API documentation generated from an OpenAPI (Swagger) specification, with example requests and responses
- Architecture diagrams showing the main components and data flow (a Mermaid or image diagram is fine)
- A short design note for each significant decision (for example, the tenancy model or the fan-out approach)

### Git history
- Commit messages that say what changed and why, in the imperative mood
- Small, focused commits that show the design evolving
- No secrets, large generated files, or binaries committed
- A clean main branch with a readable merge or pull-request history

### Live demo
- Deployed to a public host with a domain name
- HTTPS enabled with a valid certificate
- A demo account or sample data so a reviewer can try it without setup
- The deployment can be reproduced from the repository (infrastructure as code or deployment scripts)

### Performance
- Query plans checked for the slowest endpoints, with indexes where needed
- Caching used where data is read often and changes rarely, with the invalidation approach stated
- A load-test script in the repository and a results summary with the scenario, data size, and percentile latencies
- Before-and-after numbers for at least one optimisation

### Security
- No hard-coded secrets; configuration read from environment variables or a secrets manager
- Input validated at the boundary; output encoded for its context
- Authentication and authorisation tested, including negative cases
- Dependencies scanned for known vulnerabilities, with a process for updates
- Error responses that do not reveal internals

### Scalability
- A written note on how the design would handle more load, and what would break first
- Test data that is large enough to show the difference between a good and a poor design
- Stateless services where possible, so instances can be added

## How to evidence each item

A reviewer trusts evidence over claims. For each item, point to something they can check:

| Claim | Evidence to link |
|---|---|
| Tests cover business rules | A CI badge and the test directory |
| API is documented | The published OpenAPI page |
| Performance improved | A results file with before and after figures |
| Security is handled | Tests for access denial and a dependency scan report |
| Demo works | The live URL and a sample login |
| Design is scalable | A design note with the trade-offs and limits |

## Presenting the project

Write a short case study for each project: the problem, your constraints, the key decisions with their trade-offs, what you measured, and what you would do next. Keep it to a page. Interviewers ask follow-up questions about exactly these points, so prepare answers to "why this and not that?" for each decision.

## Common pitfalls

- A README that does not say how to run the project
- A demo that works only on your machine, or has expired
- Tests that exist but do not run in CI
- Performance claims with no numbers
- Commits that say "fix" or "update" with no context
- Secrets committed then removed in a later commit; they remain in the history and must be rotated

!!! tip "Interview tip"
    **Q: What is the most important thing you built, and what would you change?**
    A: Name one project, state the problem and your key trade-off, then give one specific measured result and one honest limitation. Ending with what you would change shows that you can judge your own design, which interviewers value as much as the build itself.

## Quick recap

- Meet the checklist for code, docs, history, demo, performance, security, and scalability
- Give reviewers evidence they can check, not just claims
- Keep a README that explains setup and tests, and a live demo that works
- Remove secrets from history immediately, and rotate them
- Prepare a short case study with trade-offs and measured results

**See also:** [Projects overview](index.md), [Hands-On Project Ladder](hands-on-project-ladder.md), [E-Commerce Platform](ecommerce-platform.md)
