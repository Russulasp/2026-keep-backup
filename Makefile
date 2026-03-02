.PHONY: smoke smoke-login smoke-probe smoke-fixture backup docker-up docker-down docker-smoke

smoke:
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright

smoke-login:
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright-login

smoke-probe:
	@mkdir -p logs
	@out_file="logs/smoke_probe_latest.txt"; \
	if ! touch "$$out_file" 2>/dev/null; then \
		fallback_file="$$(mktemp /tmp/keep-backup-smoke-probe-XXXXXX.txt)"; \
		echo "# warning: cannot write $$out_file (permission denied). fallback=$$fallback_file"; \
		out_file="$$fallback_file"; \
	fi; \
	status=0; \
	{ \
		echo "# keep-backup smoke-probe transcript"; \
		echo "# command=make smoke-probe"; \
		echo "# started_at=$$(date -Iseconds)"; \
		docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright-probe; \
		status=$$?; \
		echo "# exit_code=$$status"; \
	} | tee "$$out_file"; \
	latest_log="$$(ls -1t logs/run_*.log 2>/dev/null | head -n1)"; \
	if [ -n "$$latest_log" ]; then \
		echo "# latest_log=$$latest_log" | tee -a "$$out_file" >/dev/null; \
		echo "# latest_log_tail" | tee -a "$$out_file" >/dev/null; \
		tail -n 20 "$$latest_log" | sed 's/^/# log: /' | tee -a "$$out_file" >/dev/null; \
	fi; \
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
