isort --settings-file config/.isort.cfg . &&
black --config config/.black . &&
flake8 --config config/.flake8 .