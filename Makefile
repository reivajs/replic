.PHONY: setup dev stop

setup:
	@echo "⚙️ Setting up..."
	cp .env.microservices .env || echo ".env exists"
	mkdir -p logs database temp
	pip install fastapi uvicorn httpx python-dotenv jinja2
	@echo "✅ Setup complete"

dev:
	@echo "🚀 Starting development mode..."
	python scripts/start_dev.py

stop:
	@pkill -f "main.py" || echo "No processes to kill"