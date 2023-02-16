#! /usr/bin/env bash

pybabel extract . -o locale/messages.pot
pybabel update -i locale/messages.pot -d locale
pybabel compile -d locale
