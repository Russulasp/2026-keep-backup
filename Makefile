.PHONY: smoke smoke-login smoke-probe smoke-fixture backup docker-up docker-down docker-smoke

smoke:
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright

smoke-login:
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright-login

smoke-probe:
	@mkdir -p logs
	@out_file="logs/smoke_probe_latest.txt"; \
	status=0; \
	{ \
		echo "# keep-backup smoke-probe transcript"; \
		echo "# command=make smoke-probe"; \
		echo "# started_at=$$(date -Iseconds)"; \
		docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright-probe; \
		status=$$?; \
		echo "# exit_code=$$status"; \
	} | tee "$$out_file"; \
	echo "codex_context_file=$$out_file"; \
	exit $$status

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
