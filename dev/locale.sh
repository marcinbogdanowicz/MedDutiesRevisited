#!/usr/bin/bash

function usage {
    echo "Usage: $0 {extract|update|compile}"
    echo "extract: Extracts all messages from the source files marked with _() function and updates the .pot file."
    echo "update: Updates all .po files with the new messages from the .pot file. Translations should then be added."
    echo "compile: Compiles all .po files to .mo files."
}

case $1 in
    "extract")
        pybabel extract -o messages.pot .
        ;;
    "update")
        pybabel update -i messages.pot -d algorithm/translation/locales
        ;;
    "compile")
        pybabel compile -d algorithm/translation/locales
        ;;
    *)
        usage
        ;;
esac