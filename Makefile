PYTEST := uv run pytest

COV_FLAGS := --cov=core/cogs --cov=core.utils --cov=core.config --cov-report=term-missing

.PHONY: help test test-fast test-dispatch test-regression test-live test-live-enabled test-utils test-cov test-cov-dispatch test-cov-all

help:
	@echo "Available targets:"
	@echo "  make test              - run default test suite"
	@echo "  make test-fast         - run fast local suites (non-live)"
	@echo "  make test-dispatch     - run command dispatch tests"
	@echo "  make test-regression   - run regression tests"
	@echo "  make test-utils        - run utility/helper unit tests"
	@echo "  make test-live         - select live tests (still skipped unless enabled)"
	@echo "  make test-live-enabled - run live tests with --run-live"
	@echo "  make test-cov          - run full suite with coverage"
	@echo "  make test-cov-dispatch - run dispatch+regression with coverage"
	@echo "  make test-cov-all      - run full suite with coverage and XML report"

test:
	$(PYTEST)

test-fast:
	$(PYTEST) tests/test_command_dispatch.py tests/test_regression.py tests/test_utils_helpers.py tests/test_config.py

test-dispatch:
	$(PYTEST) tests/test_command_dispatch.py

test-regression:
	$(PYTEST) tests/test_regression.py

test-utils:
	$(PYTEST) tests/test_utils_helpers.py

test-live:
	$(PYTEST) -m live

test-live-enabled:
	$(PYTEST) --run-live tests/test_discord_live.py -rs

test-cov:
	$(PYTEST) $(COV_FLAGS)

test-cov-dispatch:
	$(PYTEST) $(COV_FLAGS) tests/test_command_dispatch.py tests/test_regression.py tests/test_utils_helpers.py tests/test_config.py

test-cov-all:
	$(PYTEST) $(COV_FLAGS) --cov-report=xml
