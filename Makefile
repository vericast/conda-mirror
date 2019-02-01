.PHONY: help

ENV_NAME:=conda-mirror-dev

help:
# http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

activate:
	@echo "conda activate $(ENV_NAME)"

env: ## Make a conda development environment
	conda create -n $(ENV_NAME) --file requirements.txt --file requirements-test.txt

test: ## Make a test run
	python run_tests.py -vxrs test/
