VP := env("VP", "vp")

set shell := ["bash", "-euo", "pipefail", "-c"]

check: check-test-types lint-workflows frontend-install backend-install frontend-format backend-format frontend-test backend-test

lint-workflows:
    actionlint .github/workflows/*.yaml

frontend-install:
    cd frontend/web && bun install --frozen-lockfile

backend-install:
    cd backend/genai && uv sync --frozen --python 3.14

frontend-format:
    cd frontend/web && {{VP}} fmt --check

backend-format:
    cd backend/genai && uv run --frozen --python 3.14 ruff check --select I
    cd backend/genai && uv run --frozen --python 3.14 ruff format --check

frontend-test:
    cd frontend/web && bun run test

backend-test:
    cd backend/genai && CI=true GOOGLE_CLOUD_PROJECT=test-project uv run --frozen --python 3.14 pytest --log-cli-level=INFO

install-json2ts:
    bun install -g json-schema-to-typescript

check-generated:
    cd backend/genai && PYTHONPATH="$PWD" uv run --frozen --python 3.14 pydantic2ts --module src/event_sourcing/entity/user.py --output ../../frontend/web/lib/firestore/generated/entity_user.ts
    cd backend/genai && PYTHONPATH="$PWD" uv run --frozen --python 3.14 pydantic2ts --module src/event_sourcing/entity/radio_show.py --output ../../frontend/web/lib/firestore/generated/entity_radio_show.ts
    cd backend/genai && PYTHONPATH="$PWD" uv run --frozen --python 3.14 pydantic2ts --module src/event_sourcing/entity/user_keyword.py --output ../../frontend/web/lib/firestore/generated/entity_user_keyword.ts --exclude User --exclude UserId
    git diff --exit-code -- frontend/web/lib/firestore/generated

fix-format:
    cd frontend/web && {{VP}} fmt
    cd backend/genai && uv run --frozen --python 3.14 ruff check --select I --fix tests/conftest.py
    cd backend/genai && uv run --frozen --python 3.14 ruff format tests/conftest.py

check-test-types:
    cd backend/genai && uvx --exclude-newer-package ty=2026-10-12 --python 3.14 --from ty==0.0.86 ty check --python .venv/bin/python tests/conftest.py

install-actionlint:
    go install github.com/rhysd/actionlint/cmd/actionlint@v1.7.12
    if [ -n "${GITHUB_PATH:-}" ]; then printf '%s/bin\n' "$(go env GOPATH)" >> "$GITHUB_PATH"; fi

# Match the formatter used by CI without changing the host installation.
install-vp-macos:
    mkdir -p output/vp
    curl -fsSL https://github.com/voidzero-dev/vite-plus/releases/download/v1.1.0/vp-aarch64-apple-darwin.tar.gz -o output/vp/vp-aarch64-apple-darwin.tar.gz
    curl -fsSL https://github.com/voidzero-dev/vite-plus/releases/download/v1.1.0/vp-checksums.txt -o output/vp/vp-checksums.txt
    cd output/vp && rg ' vp-aarch64-apple-darwin.tar.gz$' vp-checksums.txt | shasum -a 256 -c -
    tar -xzf output/vp/vp-aarch64-apple-darwin.tar.gz -C output/vp
