test:
	python3 -m pytest -vvv tests/

lint:
	black stringtime
	isort stringtime
	black tests
	isort tests

build:
	sed -i '' "s/DEBUG = True/DEBUG = False/g" stringtime/__init__.py
	rm -rf dist/
	python3 setup.py sdist bdist_wheel
	rm -r build/

deploy:
	rm -rf dist/
	python3 setup.py sdist bdist_wheel
	twine upload dist/*
	rm -r build/