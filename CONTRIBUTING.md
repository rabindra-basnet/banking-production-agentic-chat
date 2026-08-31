# Contributing to Banking Production Agentic Chat

## Development Setup

1. Fork and clone the repository
2. Install dependencies: `make install`
3. Create a feature branch: `git checkout -b feature/step-XX-description`
4. Make your changes
5. Run quality checks: `make quality`
6. Run tests: `make test`
7. Commit with conventional commits: `git commit -m "feat(agents): add coordinator agent routing"`
8. Push and open a Pull Request

## Branch Naming Convention
- `feature/step-XX-<description>` — Step-based features
- `feature/<domain>/<description>` — Domain features
- `fix/<description>` — Bug fixes
- `security/<description>` — Security patches
- `docs/<description>` — Documentation changes

## Commit Message Convention
We use [Conventional Commits](https://www.conventionalcommits.org/):
```
<type>(<scope>): <description>

Types: feat, fix, docs, style, refactor, test, chore, ci, security
Scopes: agents, api, mcp, security, session, llm, observability, config
```

## Code Quality Requirements
- All code must pass `ruff` linting
- All code must pass `mypy` strict type checking
- All public functions must have docstrings
- Test coverage must not decrease
- Security scans must pass (bandit, detect-secrets)

## Pull Request Checklist
- [ ] Code follows project style guidelines
- [ ] Tests added/updated for changes
- [ ] Documentation updated if needed
- [ ] No secrets or PII in code
- [ ] CI pipeline passes
- [ ] CODEOWNERS reviewer approved
