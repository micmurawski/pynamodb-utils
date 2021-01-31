PROJECT_NAME = pynamodb-utils
LAMBDA_PYTHON_PACKAGE_NAME = $(PROJECT_NAME)
COV = pynamodb_utils

include build/makefile/root.mk
include build/makefile/python.mk
include build/makefile/lint.mk
