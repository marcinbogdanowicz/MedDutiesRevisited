#!/usr/bin/env bash

PYTHONPATH=$PYTHONPATH:. flask --app web.app run --host=0.0.0.0