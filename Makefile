PYTHON=.venv/bin/python
PIP=.venv/bin/pip

.PHONY: install lint format test run

install:
	$(PIP) install -r requirements.txt

lint:
	$(PYTHON) -m ruff check app tests

format:
	$(PYTHON) -m ruff format app tests

test:
	$(PYTHON) -m pytest

run:
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000