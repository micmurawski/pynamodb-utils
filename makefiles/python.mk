#
# Public Variables
#


PYTHON ?= python3
PIP ?= pip
PYTEST ?= pytest
PYTHON_VENV ?= venv
COV ?= src/pynamodb_utils
TESTS_REQUIREMENTS ?= src/tests/requirements.txt
TESTS_DIR=src/tests

#
# Functions
#
in_venv = . $(PYTHON_VENV)/bin/activate && $(1)
#
# Integration with root Makefile
#

setup: python_venv
ifneq ($(wildcard ./setup.py),)
test: python_test
test_integration: python_test_integration
endif
distclean: python_distclean

#
# Main Python commands
#

.PHONY: python_test
python_test: $(PYTHON_VENV) install_dependencies $(TESTS_REQUIREMENTS)
	$(call in_venv,$(PYTHON) -m $(PIP) install --no-cache --requirement $(TESTS_REQUIREMENTS))
	$(call in_venv,$(PYTHON) -m $(PYTEST) $(TESTS_DIR) --cov-config pytest.ini --cov=$(COV) \
		--cov-report xml \
		--cov-report term-missing \
	)

.PHONY: python_venv
python_venv: $(PYTHON_VENV)
	@:

.PHONY: python_distclean
python_distclean:
	rm -rf "$(PYTHON_VENV)"
	rm -rf ".pytest_cache"

#
# Virtual Env
#

install_dependencies: export PIP_PROCESS_DEPENDENCY_LINKS=1
install_dependencies: $(PYTHON_VENV)
	$(call in_venv,$(PYTHON) -m $(PIP) install --upgrade 'pip')
ifneq ($(wildcard ./setup.py),)
	$(call in_venv,$(PYTHON) -m $(PIP) install --editable .)
endif

$(PYTHON_VENV):
	$(PYTHON) -m venv "$@"
	touch $(PYTHON_VENV)
