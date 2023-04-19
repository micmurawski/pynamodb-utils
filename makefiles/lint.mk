SWAGGER_FILE_DIR ?= ""

test: code_lint
lint: code_lint

.PHONY: code_lint
code_lint: $(PYTHON_VENV)
	$(call in_venv, $(PIP) install isort flake8)
	$(call in_venv, $(PYTHON) -m isort --check .)
	$(call in_venv, $(PYTHON) -m flake8 .)

