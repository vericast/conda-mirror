.PHONY: help test

ENV_NAME:=conda-mirror-dev

help:
# http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

activate: ## Make an conda activate command
	@echo "conda activate $(ENV_NAME)"

clean: ## Make a clean source tree
	-find . -name '*.pyc' -exec rm -fv {} \;
	rm -rf conda_mirror/__pycache__ test/__pycache__ __pycache__ dist *.egg-info

env: ## Make a conda development environment
	conda create -n $(ENV_NAME) --file requirements.txt --file requirements-test.txt

release: sdist ## Make a pypi release
	python setup.py sdist
	twine upload dist/*.tar.gz

sdist: clean ## Make a source distribution
	python setup.py sdist

test: ## Make a test run
	python run_tests.py -vxrs test/
