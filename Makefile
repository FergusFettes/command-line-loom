-include .env
export

install: reqs
	pip install --user -U .

publish: reqs
	poetry publish --build -u __token__ -p ${PYPI_TOKEN}

reqs:
	pip install poetry
	poetry export -f requirements.txt --without-hashes > requirements.txt
