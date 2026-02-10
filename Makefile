.PHONY: smoke smoke-fixture backup docker-up docker-down docker-smoke

smoke:
	uv run --with playwright python -m keep_backup.app --mode smoke-playwright

smoke-fixture:
	uv run --with playwright python -m keep_backup.app --mode smoke-playwright-fixture

backup:
	uv run python -m keep_backup.app --mode backup

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-smoke:
	docker compose run --rm app python -m keep_backup.app --mode smoke-playwright
