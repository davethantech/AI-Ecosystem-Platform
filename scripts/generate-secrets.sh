#!/usr/bin/env sh
set -eu
printf 'SECRET_KEY: '
python3 -c 'import secrets; print(secrets.token_urlsafe(64))'
printf 'POSTGRES_PASSWORD (URL-safe): '
python3 -c 'import secrets; print(secrets.token_urlsafe(32).replace("-", "A").replace("_", "B"))'
