# PM MCP Server Makefile
PY ?= python3
VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
SERVER := src/server.py

# Database path - defaults to main project database
DB_PATH ?= ../data/jira_lite.db

.PHONY: help bootstrap validate run run-http claude-add install clean test

help: ## Show this help message
	@echo "PM MCP Server - Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

$(VENV):
	$(PY) -m venv $(VENV)

bootstrap: $(VENV) ## Setup Python virtual environment and install dependencies
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ MCP server dependencies installed"

validate: bootstrap ## Validate configuration and database connectivity
	PM_DATABASE_PATH=$(DB_PATH) $(PYTHON) $(SERVER) --validate-config

run: bootstrap ## Run MCP server in stdio mode (for Claude Desktop)
	@echo "🚀 Starting PM MCP Server in stdio mode..."
	PM_DATABASE_PATH=$(DB_PATH) $(PYTHON) $(SERVER) --transport stdio

run-http: bootstrap ## Run MCP server in HTTP mode for testing
	@echo "🚀 Starting PM MCP Server in HTTP mode..."
	PM_DATABASE_PATH=$(DB_PATH) $(PYTHON) $(SERVER) --transport http --host 127.0.0.1 --port 8848

test: bootstrap ## Run basic functionality tests
	@echo "🧪 Testing MCP server..."
	PM_DATABASE_PATH=$(DB_PATH) $(PYTHON) -c "\
import sys; sys.path.insert(0, 'src'); \
from config import Config; \
from database import PMDatabase; \
try: \
    PMDatabase.initialize(); \
    projects = PMDatabase.get_all_projects(); \
    print(f'✅ Database accessible - {len(projects)} projects found'); \
except Exception as e: \
    print(f'❌ Database test failed: {e}'); \
    sys.exit(1)"

claude-add: bootstrap ## Show Claude Desktop configuration
	@echo "🔧 Claude Desktop MCP Server Configuration:"
	@echo ""
	@echo "Add this to your claude_desktop_config.json:"
	@echo "{"
	@echo "  \"mcpServers\": {"
	@echo "    \"pm\": {"
	@echo "      \"command\": \"$(shell pwd)/$(VENV)/bin/python\","
	@echo "      \"args\": [\"$(shell pwd)/$(SERVER)\", \"--transport\", \"stdio\"],"
	@echo "      \"env\": {"
	@echo "        \"PM_DATABASE_PATH\": \"$(shell cd .. && pwd)/data/jira_lite.db\""
	@echo "      }"
	@echo "    }"
	@echo "  }"
	@echo "}"
	@echo ""
	@echo "Then restart Claude Desktop to load the server."

install: bootstrap validate ## Complete installation with validation
	@echo ""
	@echo "✅ PM MCP Server installed successfully!"
	@echo ""
	@echo "Quick start:"
	@echo "  make run          # Test in stdio mode"
	@echo "  make run-http     # Test in HTTP mode (http://127.0.0.1:8848)"
	@echo "  make claude-add   # Get Claude Desktop config"
	@echo ""
	@echo "Environment:"
	@echo "  Database: $(DB_PATH)"
	@echo "  Projects: Check with 'make test' command"

clean: ## Clean up generated files and virtual environment
	rm -rf $(VENV)
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleaned up MCP server files"