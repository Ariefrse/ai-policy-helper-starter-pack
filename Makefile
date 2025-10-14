.PHONY: dev test fmt lint docker-build
dev:
	docker compose up --build

test:
	docker compose run --rm backend pytest -q

fmt:
	docker compose run --rm backend black app

lint:
	docker compose run --rm backend ruff check app && docker compose run --rm backend flake8 app

docker-build:
	docker build -t policy-helper-backend ./backend && docker build -t policy-helper-frontend ./frontend
