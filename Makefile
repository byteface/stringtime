test:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -vvv -p pytest_mock -m "not slow and not variant and not regression" tests/

test-canonical:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -vvv -p pytest_mock tests/test_core_api.py tests/test_parser_canonical.py tests/test_cli.py tests/test_recurring.py

test-all:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -vvv -p pytest_mock tests/

test-fast:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -vvv -p pytest_mock -m "not slow and not variant and not regression" tests/

test-slow:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -vvv -p pytest_mock -m "slow and not variant" tests/

test-regressions:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -vvv -p pytest_mock -m regression tests/

test-variants:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -vvv -p pytest_mock -m variant tests/

test-variants-fast:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -vvv -p pytest_mock tests/test_parser_variants.py

test-parallel:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -vvv -p pytest_mock -p xdist.plugin -n auto -m "not slow and not variant and not regression" tests/

testp:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -vvv -s -p pytest_mock tests/

cov:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -vvv -p pytest_mock -p pytest_cov --cov=stringtime --cov-report=term-missing tests/

variants:
	python3 scripts/find_variant_failures.py

extract-variants:
	python3 scripts/find_extraction_variant_failures.py

demo:
	python3 demo/app.py

lint:
	black stringtime tests
	isort stringtime tests

build:
	rm -rf build/
	rm -rf dist/
	sed -i '' "s/DEBUG = True/DEBUG = False/g" stringtime/__init__.py
	python3 setup.py sdist bdist_wheel
	rm -r build/

deploy:
	rm -rf build/
	rm -rf dist/
	python3 setup.py sdist bdist_wheel
	twine upload dist/*
	rm -r build/
