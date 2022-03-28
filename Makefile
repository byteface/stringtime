# to run tests you can use test

test:
	python3 -m unittest tests.test_stringtime

# test:
# python3 -m unittest tests.test_stringtime.TestCase.test_phrases_past


clean:
	rm -r dir/

build:
	rm -r dist/
	python3 setup.py sdist bdist_wheel
	rm -r build/

deploy:
	rm -r dist/
	python3 setup.py sdist bdist_wheel
	twine upload dist/*
	rm -r build/