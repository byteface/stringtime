test:
	python3 -m pytest -vvv tests/

testp:
	python3 -m pytest -vvv -s tests/

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