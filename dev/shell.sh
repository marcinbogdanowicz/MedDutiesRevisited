#!/usr/bin/bash

RUN_IMPORTS_SCRIPT=$(cat <<EOF
import os
from pathlib import Path

root_path = Path('/')
app_path = root_path / 'app'

files_to_import_as_modules = []
directories_to_skip = [str(app_path / relative_path) for relative_path in ('algorithm/tests', 'algorithm/e2e_tests')]

imports_str = '''
import functools
import itertools
import os
import sys
import time
from contextlib import contextmanager, suppress
from datetime import datetime, timedelta, timezone
from pathlib import Path
'''

exec(imports_str)

def print_red(text: str):
    print(f'\033[91m{text}\033[00m')

def import_public_properties(module_name: str):
    imported = ''
    module = __import__(module_name, fromlist=['*'])
    for attr in dir(module):
        if not attr.startswith('_'):
            globals()[attr] = getattr(module, attr)
            imported += f'from {module_name} import {attr}\n'
    return imported

def import_module(module_name: str):
    module = __import__(module_name, fromlist=['*'])
    from_name, module_name = module_name.rsplit('.', 1)
    globals()[module_name] = module
    return f'from {from_name} import {module_name}\n'

for root, dirs, files in os.walk(app_path):
    if root in directories_to_skip:
        continue

    for filename in files:
        if filename.endswith('.py') and not filename.startswith('_'):
            module = str(Path(root).relative_to(app_path) / filename)[:-3].replace('/', '.')
            if filename in files_to_import_as_modules:
                imports_str += import_module(module)
            else:
                imports_str += import_public_properties(module)

print_red(f'\nADDITIONAL_IMPORTS:\n{imports_str}')
EOF
)


docker compose run --rm -w /app algorithm bash -c "ipython -c \"$RUN_IMPORTS_SCRIPT\" -i"