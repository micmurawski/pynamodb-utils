SWAGGER_FILE_DIR ?= ""

test: code_lint
lint: code_lint

.PHONY: code_lint
code_lint: $(PYTHON_VENV)
	$(call in_venv,$(PIP) install isort flake8)
	$(call in_venv,isort .)
	$(call in_venv,flake8)

