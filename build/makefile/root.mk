#
# General Make config
#

.DEFAULT = help
ROOTDIR := $(CURDIR)

#
# Project config
#

ALLOW_DEPLOY ?= false
TERRAFORM_WORKSPACE_NAME ?= dev
TERRAFORM_BUCKET ?= dummy_terraform_bucket

CACHE_DIR ?= .cache
ARTIFACTS_DIR ?= .artifacts

#
# Binaries
#

PYTHON ?= python3.7
PIP ?= pip3.7
ZIP ?= zip
WGET ?= wget
JQ ?= jq
PYTEST ?= pytest

#
# Global Variables
#

OS = $(shell uname -s | tr '[:upper:]' '[:lower:]')

#
# Functions
#

with_aws_role = STS_OUTPUT=$$(aws sts assume-role --role-arn $(1) --role-session-name makefile) \
	AWS_ACCESS_KEY_ID=$$(echo "$$STS_OUTPUT" | jq .Credentials.AccessKeyId) \
	AWS_SECRET_ACCESS_KEY=$$(echo "$$STS_OUTPUT" | jq .Credentials.SecretAccessKey) \
	AWS_SESSION_TOKEN=$$(echo "$$STS_OUTPUT" | jq .Credentials.SessionToken) $(2)

#
# Targets
#

define HELP_TEXT
help:                   Display this help message
setup:                  Installs required dependencies.
build:                  Builds artifacts.
test:                   Runs unit tests.
test_integration:       Runs integration tests.
configure_deployment:   Configure system environment
deploy:                 Deploys application.
destroy:                Destroys application.
clean:                  Cleans temporary files.
distclean:              Cleans all generated files.
endef
export HELP_TEXT

# Display help text.
.PHONY: help
help:
	@echo "$$HELP_TEXT"

# Install dependencies required for further steps or development.
# For example: create virtual environment.
.PHONY: setup
setup:
	@:

# Build project (compile etc.)
.PHONY: build
build:
	@:

# Package project into an artifacts (for example: JAR, deployment package).
.PHONY: package
package:
	@:

# Lint source code.
.PHONY: lint
lint:
	@:

# Run unit tests.
.PHONY: test
test:
	@:

# Run integration tests (against deployed service).
.PHONY: test_integration
test_integration:
	@:

# Deploy project.
.PHONY: deploy
deploy:
	@:

# Configure project after it has been deployed.
.PHONY: configure_deployment
configure_deployment:
	@:

# Destroy deployment.
.PHONY: destroy
destroy:
	@:

# Remove temporary local files.
.PHONY: clean
clean:
	rm -rf "$(ARTIFACTS_DIR)"

# Remove temporary local files and local dependency cache.
.PHONY: distclean
distclean: clean
	rm -rf "$(CACHE_DIR)"

$(CACHE_DIR):
	mkdir -p "$(CACHE_DIR)"

$(ARTIFACTS_DIR):
	mkdir -p "$(ARTIFACTS_DIR)"
