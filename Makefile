.PHONY: help smoke smoke-login smoke-probe smoke-dom smoke-dom-investigate smoke-fixture backup parse-dom docker-up docker-down docker-smoke up down run login probe dom fixture investigate

help:
	@echo "Primary targets (all delegate to docker compose):"
	@echo "  make up            # docker compose up -d --build"
	@echo "  make down          # docker compose down"
	@echo "  make smoke         # smoke-playwright"
	@echo "  make login         # smoke-playwright-login"
	@echo "  make probe         # smoke-playwright-probe"
	@echo "  make dom           # smoke-playwright-dom"
	@echo "  make fixture       # smoke-playwright-fixture"
	@echo "  make run           # backup"
	@echo "  make parse-dom     # parse from latest DOM snapshot"

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


smoke-dom:
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright-dom

smoke-dom-investigate:
	@mkdir -p logs
	@out_file="logs/smoke_dom_investigate_latest.txt"; \
	echo "# keep-backup smoke-dom investigation transcript" > "$$out_file"; \
	echo "# command=make smoke-dom-investigate" >> "$$out_file"; \
	echo "# started_at=$$(date -Iseconds)" >> "$$out_file"; \
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright-dom >> "$$out_file" 2>&1; \
	status=$$?; \
	echo "# exit_code=$$status" >> "$$out_file"; \
	latest_log="$$(ls -1t logs/run_*.log 2>/dev/null | head -n1)"; \
	if [ -n "$$latest_log" ]; then \
		echo "# latest_log=$$latest_log" >> "$$out_file"; \
		echo "# latest_log_tail" >> "$$out_file"; \
		tail -n 40 "$$latest_log" | sed 's/^/# log: /' >> "$$out_file"; \
	fi; \
	latest_dom="$$(ls -1t logs/artifacts/dom_snapshot_*.html 2>/dev/null | head -n1)"; \
	if [ -n "$$latest_dom" ]; then \
		echo "# latest_dom_snapshot=$$latest_dom" >> "$$out_file"; \
	fi; \
	cat "$$out_file"; \
	echo "codex_context_file=$$out_file"; \
	exit $$status

smoke-fixture:
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright-fixture

backup:
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode backup

parse-dom:
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode parse-dom

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-smoke:
	docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright

up: docker-up

down: docker-down

run: backup

login: smoke-login

probe: smoke-probe

dom: smoke-dom

fixture: smoke-fixture

investigate: smoke-dom-investigate
