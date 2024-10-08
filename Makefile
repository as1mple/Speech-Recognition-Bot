VENV = venv
PYTHON = python3.11
PIP = $(VENV)/bin/pip
MYPY = $(VENV)/bin/mypy

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
