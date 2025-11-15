# Pull Request

## Description

<!-- Provide a clear and concise description of your changes -->

## Type of Change

<!-- Mark the relevant option with an 'x' -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement
- [ ] Security fix
- [ ] Dependency update
- [ ] Playbook addition/modification
- [ ] Integration addition/modification

## Related Issues

<!-- Link related issues here -->

Fixes #(issue number)
Closes #(issue number)
Related to #(issue number)

## Changes Made

<!-- Provide a detailed list of changes -->

### Backend Changes
-
-

### Frontend Changes
-
-

### Database Changes
-
-

### Documentation Changes
-
-

### Configuration Changes
-
-

## Motivation and Context

<!-- Why is this change required? What problem does it solve? -->

## How Has This Been Tested?

<!-- Describe the tests you ran to verify your changes -->

- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing
- [ ] Docker Compose testing
- [ ] End-to-end testing

**Test Configuration:**
- Python version:
- OS:
- Database version:

**Test Coverage:**
- Lines covered: ___%
- Branches covered: ___%

## Screenshots (if applicable)

<!-- Add screenshots for UI changes -->

## Checklist

### Code Quality
- [ ] My code follows the style guidelines (PEP 8, Black formatting)
- [ ] I have run `make format` to format my code
- [ ] I have run `make lint` and fixed all issues
- [ ] I have added type hints to new functions
- [ ] I have added docstrings to new functions/classes
- [ ] My code passes `mypy` type checking

### Testing
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally
- [ ] Test coverage is at least 70% for new code
- [ ] I have tested in Docker environment

### Documentation
- [ ] I have updated the README.md (if needed)
- [ ] I have updated relevant documentation in `docs/`
- [ ] I have added/updated inline code comments
- [ ] I have updated the CHANGELOG.md
- [ ] I have updated API documentation (if API changes)

### Security
- [ ] I have reviewed my code for security vulnerabilities
- [ ] I have not hardcoded secrets or credentials
- [ ] I have validated all user inputs
- [ ] I have used parameterized queries (no SQL injection)
- [ ] I have escaped outputs properly (no XSS)
- [ ] I have followed OWASP best practices

### Playbooks (if applicable)
- [ ] Playbook follows the `BasePlaybook` interface
- [ ] Playbook has proper error handling
- [ ] Playbook logs all actions
- [ ] Playbook has notification support
- [ ] Playbook has been registered in orchestrator
- [ ] Playbook has comprehensive tests

### Integrations (if applicable)
- [ ] Integration uses async/await properly
- [ ] Integration has retry logic
- [ ] Integration has timeout handling
- [ ] Integration has proper error handling
- [ ] Integration is properly mocked in tests
- [ ] API keys are in configuration

### Database (if applicable)
- [ ] Database migrations are included
- [ ] Migrations are reversible
- [ ] I have tested the migration on a test database
- [ ] Schema changes are documented

### Docker (if applicable)
- [ ] Docker Compose file updated
- [ ] Docker image builds successfully
- [ ] Health checks are working
- [ ] Environment variables documented in `.env.example`

### Breaking Changes
- [ ] This PR does NOT contain breaking changes
- OR
- [ ] Breaking changes are documented
- [ ] Migration guide is provided
- [ ] Version number will be bumped appropriately

## Performance Impact

<!-- Describe any performance implications -->

- [ ] No performance impact
- [ ] Minor performance improvement
- [ ] Significant performance improvement
- [ ] Potential performance degradation (explain below)

## Deployment Notes

<!-- Any special deployment considerations -->

**Pre-deployment:**
-
-

**Post-deployment:**
-
-

**Rollback plan:**
-
-

## Additional Notes

<!-- Any additional information for reviewers -->

## Reviewer Checklist

<!-- For reviewers -->

- [ ] Code is well-structured and readable
- [ ] Tests are comprehensive
- [ ] Documentation is clear and complete
- [ ] Security considerations addressed
- [ ] Performance is acceptable
- [ ] No unintended side effects
- [ ] Commits follow conventional commit format
- [ ] Ready to merge

---

**By submitting this PR, I confirm that my contribution is made under the terms of the MIT license.**
