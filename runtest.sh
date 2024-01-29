#!/bin/bash -ex
#

poetry run isort . -m HANGING_INDENT -l 120 --check-only
poetry run pytest -v
