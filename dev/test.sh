#!/usr/bin/bash

set -e

coverage run -m unittest "$@" -v --durations 5
coverage report -m --skip-empty --fail-under 95 --omit="./algorithm/tests/*"