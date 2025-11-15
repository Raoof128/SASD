# Contributing to SOAR Platform

Thank you for considering contributing to the SOAR Platform! This document provides guidelines for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/SASD.git`
3. Add upstream remote: `git remote add upstream https://github.com/ORIGINAL_OWNER/SASD.git`
4. Create a new branch: `git checkout -b feature/your-feature-name`

## Development Setup

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Local Setup

```bash
# Install dependencies
make install

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
make init

# Run tests
make test

# Start development server
make dev
```

### Using Docker

```bash
# Start all services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Screenshots** (if applicable)
- **Error logs**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** and **motivation**
- **Proposed solution**
- **Alternative solutions** considered
- **Additional context**

### Contributing Code

1. **Choose an issue** or create one
2. **Comment** on the issue to let others know you're working on it
3. **Fork and branch** from `main`
4. **Make your changes** following our coding standards
5. **Write tests** for your changes
6. **Ensure all tests pass** (`make test`)
7. **Update documentation** as needed
8. **Submit a pull request**

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with the following tools:

- **Black** for code formatting (120 character line length)
- **Flake8** for linting
- **MyPy** for type checking
- **isort** for import sorting

```bash
# Format code
make format

# Run linters
make lint

# Type check
mypy backend/
```

### Code Quality Requirements

- **Type hints** for all function signatures
- **Docstrings** for all public functions, classes, and modules
- **Unit tests** for all new functionality
- **Integration tests** for API endpoints
- **Error handling** with informative messages
- **Logging** for debugging (use appropriate log levels)

### Example Code Style

```python
"""
Module docstring describing the purpose.
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ExampleClass:
    """
    Class docstring describing the class.

    Attributes:
        name: Description of attribute
    """

    def __init__(self, name: str) -> None:
        """Initialize the class.

        Args:
            name: The name parameter
        """
        self.name = name

    def process_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process the data and return results.

        Args:
            data: Input data dictionary

        Returns:
            Processed data or None if processing fails

        Raises:
            ValueError: If data is invalid
        """
        try:
            # Implementation
            return processed_data
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return None
```

## Testing Guidelines

### Test Structure

```
tests/
├── test_integrations.py    # API integration tests
├── test_playbooks.py        # Playbook tests
├── test_models.py           # Database model tests
├── test_auth.py             # Authentication tests
└── test_api_endpoints.py    # API endpoint tests
```

### Writing Tests

```python
import pytest
from unittest.mock import AsyncMock, patch


class TestPhishingPlaybook:
    """Test phishing response playbook."""

    @pytest.fixture
    def mock_incident(self):
        """Create mock incident for testing."""
        # Setup fixture
        return incident

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_incident):
        """Test successful playbook execution."""
        # Arrange
        playbook = PhishingResponsePlaybook()

        # Act
        result = await playbook.execute(mock_incident)

        # Assert
        assert result['success'] == True
        assert result['verdict'] == 'malicious'
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_playbooks.py -v

# Run specific test
pytest tests/test_playbooks.py::TestPhishingPlaybook::test_execute_success -v
```

### Test Coverage Requirements

- **Minimum 70% coverage** for all new code
- **80%+ coverage** for critical security functions
- All **playbooks** must have tests
- All **API endpoints** must have integration tests
- All **integrations** must be mocked and tested

## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks
- **perf**: Performance improvements
- **ci**: CI/CD changes

### Examples

```
feat(playbooks): add ransomware containment playbook

Implements automated ransomware detection and containment with:
- File system isolation
- Process termination
- Network segmentation
- Automated backup restoration

Closes #123
```

```
fix(auth): resolve JWT token expiration issue

Fixed bug where tokens were expiring prematurely due to
timezone mismatch between server and client.

Fixes #456
```

### Scope Guidelines

- `playbooks` - Security playbooks
- `integrations` - External API integrations
- `api` - API endpoints
- `auth` - Authentication/authorization
- `db` - Database models/migrations
- `docker` - Docker configuration
- `docs` - Documentation
- `tests` - Test suite

## Pull Request Process

### Before Submitting

1. ✅ Update documentation
2. ✅ Add/update tests
3. ✅ Run `make format`
4. ✅ Run `make lint`
5. ✅ Run `make test`
6. ✅ Update CHANGELOG.md
7. ✅ Rebase on latest `main`

### PR Template

When creating a PR, include:

- **Description** of changes
- **Motivation** and context
- **Type of change** (bug fix, feature, etc.)
- **Testing** performed
- **Screenshots** (if UI changes)
- **Checklist** completion

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **Code review** by at least one maintainer
3. **Testing** verification
4. **Documentation** review
5. **Approval** and merge

### Merge Requirements

- ✅ All CI/CD checks passing
- ✅ At least one approving review
- ✅ No merge conflicts
- ✅ Branch up to date with main
- ✅ All conversations resolved

## Development Workflow

### Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/add-new-playbook

# 2. Make changes and commit
git add .
git commit -m "feat(playbooks): add lateral movement playbook"

# 3. Keep branch updated
git fetch upstream
git rebase upstream/main

# 4. Push to your fork
git push origin feature/add-new-playbook

# 5. Create pull request on GitHub
```

### Bug Fixes

```bash
# 1. Create bugfix branch
git checkout -b fix/authentication-error

# 2. Fix the bug and commit
git commit -m "fix(auth): resolve token validation error"

# 3. Add tests for the fix
git commit -m "test(auth): add test for token validation"

# 4. Push and create PR
git push origin fix/authentication-error
```

## Adding New Features

### New Playbook

1. Create playbook file in `backend/playbooks/`
2. Inherit from `BasePlaybook`
3. Implement `execute()` method
4. Add to playbook registry in `orchestrator.py`
5. Write tests in `tests/test_playbooks.py`
6. Add documentation in `docs/PLAYBOOK_CATALOG.md`

### New Integration

1. Create integration file in `backend/integrations/`
2. Implement async API methods
3. Add configuration to `config.py`
4. Update `.env.example`
5. Write tests with mocking
6. Document in `docs/API_INTEGRATIONS.md`

### New API Endpoint

1. Create route in appropriate `backend/routes/` file
2. Implement endpoint with proper error handling
3. Add authentication/authorization
4. Write integration tests
5. Update API documentation

## Documentation

### When to Update Documentation

- Adding new features
- Changing existing behavior
- Adding/removing dependencies
- Updating configuration
- Fixing bugs (if behavior changes)

### Documentation Locations

- `README.md` - Project overview
- `QUICKSTART.md` - Getting started guide
- `docs/ARCHITECTURE.md` - System architecture
- `docs/API_INTEGRATIONS.md` - Integration guides
- `docs/DEPLOYMENT.md` - Deployment instructions
- `CHANGELOG.md` - Version history

## Community

### Getting Help

- **GitHub Issues** - Bug reports and feature requests
- **Discussions** - Questions and general discussion
- **Documentation** - Comprehensive guides

### Recognition

Contributors will be recognized in:
- `CHANGELOG.md` for their contributions
- GitHub contributor graph
- Release notes

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## Questions?

If you have questions about contributing, please:
1. Check existing documentation
2. Search existing issues
3. Create a new issue with the `question` label

Thank you for contributing to making security automation better!
