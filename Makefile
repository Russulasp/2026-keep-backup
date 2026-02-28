.PHONY: smoke smoke-login smoke-probe smoke-fixture backup docker-up docker-down docker-smoke

smoke:
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright

smoke-login:
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright-login

smoke-probe:
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright-probe

smoke-fixture:
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright-fixture

backup:
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode backup

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-smoke:
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright
