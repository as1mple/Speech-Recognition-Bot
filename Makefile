VENV = venv
PYTHON = python3.11
PIP = $(VENV)/bin/pip
MYPY = $(VENV)/bin/mypy
ISORT = $(VENV)/bin/isort
BLACK = $(VENV)/bin/black
FLAKE8 = $(VENV)/bin/flake8

create-venv:
	@if [ -d $(VENV) ]; then \
		echo "Virtual environment '$(VENV)' already exists."; \
	else \
		echo "Creating virtual environment with $(PYTHON)"; \
		$(PYTHON) -m venv $(VENV); \
	fi

install: create-venv
	@echo "Installing dependencies with $(PIP)"
	$(PIP) install -r requirements.txt

check-types:
	@echo "Checking types with mypy"
	$(MYPY) .


check-format:
	@echo "Running isort..."
	$(ISORT) --settings-file config/.isort.cfg .
	@echo "Running black..."
	$(BLACK) --config config/.black .
	@echo "Running flake8..."
	$(FLAKE8) --config config/.flake8 .