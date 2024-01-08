# Developent Guide
tidevice3 primarily encapsulates pymobiledevice3, aiming to offer a better command-line user experience.

# Code Structure
Within the cli directory, apart from cli_common.py, the name of each other file represents a subcommand. When adding a new subcommand, you need to register it in cli_common.py.

# The project uses poetry for dependency management and publishing

```bash
# Install poetry
pip install poetry

# Install dependencies to the local directory .venv
poetry install

# Run unit tests
poetry run pytest -v

# Test a single subcommand
poetry run t3 list
```

Refer to .github/workflows for release processes.

