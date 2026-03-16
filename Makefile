test:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -vvv -p pytest_mock tests/

testp:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -vvv -s -p pytest_mock tests/

cov:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -vvv -p pytest_mock -p pytest_cov --cov=stringtime --cov-report=term-missing tests/

registry:
	python3 scripts/build_phrase_registry.py

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
