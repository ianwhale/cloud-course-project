# Execute the "targets" in this file with `make <target>` e.g. `make help`.
#
# You can also run multiple in sequence, e.g. `make clean lint test serve-coverage-report`
#
# See run.sh for more in-depth comments on what each target does.

build:
	bash run.sh build

clean:
	bash run.sh clean

deploy-lambda: clean
	bash run.sh deploy-lambda

generate-client-library:
	bash run.sh generate-client-library

help:
	bash run.sh help

install:
	bash run.sh install

install-generated-sdk:
	bash run.sh install-generated-sdk

lint:
	bash run.sh lint

lint-ci:
	bash run.sh lint:ci

publish-prod:
	bash run.sh publish:prod

publish-test:
	bash run.sh publish:test

release-prod:
	bash run.sh release:prod

release-test:
	bash run.sh release:test

run:
	bash run.sh run

run-mock:
	bash run.sh run-mock

serve-coverage-report:
	bash run.sh serve-coverage-report

test-ci:
	bash run.sh test:ci

test-quick:
	bash run.sh test:quick

test:
	bash run.sh run-tests

test-wheel-locally:
	bash run.sh test:wheel-locally
