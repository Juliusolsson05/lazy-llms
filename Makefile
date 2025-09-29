PORT ?= 1929
PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin
MCP_VENV := mcp/venv
MCP_VENV_BIN := $(MCP_VENV)/bin

.PHONY: help bootstrap bootstrap-mcp init register jl-run-auto jl-init-db migrate-to-db mcp-install mcp-run mcp-validate mcp-claude-config docker-build docker-run docker-stop clean test

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

bootstrap: ## Set up Python virtual environment and install dependencies
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt
	@echo "✅ Virtual environment created and dependencies installed"

jl-run-auto: bootstrap ## Start Jira-lite server with auto port detection
	@echo "🚀 Starting Jira-lite server..."
	$(VENV_BIN)/python -m src.jira_lite.app --port $(PORT) --auto

jl-init-db: bootstrap ## Initialize JSON files with mock data
	@echo "🗄️  Initializing JSON files with mock data..."
	$(VENV_BIN)/python -m src.jira_lite.mock_data

# MCP Server targets
bootstrap-mcp: ## Setup MCP server environment
	@echo "🔧 Setting up MCP server..."
	cd mcp && $(PYTHON) -m venv venv
	cd mcp && venv/bin/pip install --upgrade pip
	cd mcp && venv/bin/pip install -r requirements.txt
	@echo "✅ MCP server dependencies installed"

mcp-validate: bootstrap-mcp ## Validate MCP server configuration
	@echo "🔍 Validating MCP server..."
	cd mcp && PM_DATABASE_PATH=../data/jira_lite.db venv/bin/python src/server.py --validate-config

mcp-run: bootstrap-mcp ## Run MCP server in stdio mode
	@echo "🚀 Starting MCP server..."
	cd mcp && PM_DATABASE_PATH=../data/jira_lite.db venv/bin/python src/server.py --transport stdio

mcp-run-http: bootstrap-mcp ## Run MCP server in HTTP mode for testing
	@echo "🚀 Starting MCP server in HTTP mode..."
	cd mcp && PM_DATABASE_PATH=../data/jira_lite.db venv/bin/python src/server.py --transport http --port 8848

mcp-claude-config: ## Show Claude Desktop configuration for MCP server
	@echo "🔧 Claude Desktop MCP Server Configuration:"
	@echo ""
	@echo "Add this to your claude_desktop_config.json:"
	@echo '{'
	@echo '  "mcpServers": {'
	@echo '    "pm": {'
	@echo '      "command": "'$(shell pwd)'/mcp/venv/bin/python",'
	@echo '      "args": ["'$(shell pwd)'/mcp/src/server.py", "--transport", "stdio"],'
	@echo '      "env": {'
	@echo '        "PM_DATABASE_PATH": "'$(shell pwd)'/data/jira_lite.db"'
	@echo '      }'
	@echo '    }'
	@echo '  }'
	@echo '}'
	@echo ""
	@echo "Then restart Claude Desktop to load the PM server."

mcp-install: bootstrap-mcp mcp-validate ## Complete MCP server installation
	@echo ""
	@echo "✅ PM MCP Server installed successfully!"
	@echo ""
	@echo "Quick start:"
	@echo "  make mcp-run          # Test MCP server in stdio mode"
	@echo "  make mcp-run-http     # Test in HTTP mode (http://127.0.0.1:8848)"
	@echo "  make mcp-claude-config # Get Claude Desktop configuration"

init: bootstrap ## Create project initialization tool
	@echo "🔧 Project initialization not yet implemented"
	@echo "   Use the web UI to create projects for now"
	@echo "   Visit: http://127.0.0.1:$(PORT)"

register: bootstrap ## Register project with Jira-lite server
	@echo "📝 Project registration not yet implemented"
	@echo "   Use the web UI to register projects for now"
	@echo "   Visit: http://127.0.0.1:$(PORT)"

test: bootstrap ## Run basic functionality tests
	@echo "🧪 Testing API endpoints..."
	@$(VENV_BIN)/python -c "import requests; print('Health check:', requests.get('http://127.0.0.1:$(PORT)/api/health').json())" 2>/dev/null || echo "❌ Server not running on port $(PORT)"

clean: ## Clean up generated files and virtual environment
	rm -rf $(VENV)
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf src/jira_lite/__pycache__
	rm -rf src/jira_lite/api/__pycache__
	find . -name "*.pyc" -delete
	@echo "✅ Cleaned up generated files"

# Quick start targets
demo: jl-init-db jl-run-auto ## Initialize with mock data and start server

migrate-to-db: bootstrap ## Migrate JSON data to SQLite database
	@echo "🔄 Migrating JSON data to SQLite + Peewee..."
	$(VENV_BIN)/python -m src.jira_lite.migrate

# Docker targets
docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t jira-lite:latest .

docker-run: docker-build ## Run application in Docker
	@echo "🚀 Starting Jira-lite in Docker..."
	docker-compose up -d

docker-stop: ## Stop Docker containers
	@echo "⏹️  Stopping Docker containers..."
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f jira-lite

docker-shell: ## Get shell in running container
	docker-compose exec jira-lite /bin/bash

# Combined targets
install: bootstrap jl-init-db ## Full installation: setup venv, install deps, init DB
	@echo ""
	@echo "✅ Installation complete!"
	@echo "   Run: make jl-run-auto"
	@echo "   Then visit: http://127.0.0.1:$(PORT)"

install-db: bootstrap migrate-to-db ## Install with SQLite database migration
	@echo ""
	@echo "✅ Database installation complete!"
	@echo "   Run: make jl-run-auto"
	@echo "   Then visit: http://127.0.0.1:$(PORT)"

# Complete installation with both web UI and MCP server
install-complete: bootstrap migrate-to-db bootstrap-mcp mcp-validate ## Complete installation: Web UI + MCP server
	@echo ""
	@echo "🎉 Complete LLM-Native PM System installed!"
	@echo ""
	@echo "Web UI:"
	@echo "   make jl-run-auto     # Start at http://127.0.0.1:$(PORT)"
	@echo ""
	@echo "MCP Server:"
	@echo "   make mcp-run         # Test MCP server"
	@echo "   make mcp-claude-config # Get Claude Desktop config"
	@echo ""
	@echo "Database: $(shell pwd)/data/jira_lite.db"
	@echo "Projects: $(shell $(VENV_BIN)/python -c 'import sys; sys.path.insert(0, \"src\"); from jira_lite.repositories import ProjectRepository; print(len(ProjectRepository.get_all()))' 2>/dev/null || echo 'Check manually') found"

docker-demo: docker-run ## Complete Docker demo setup
	@echo ""
	@echo "✅ Docker demo running!"
	@echo "   Visit: http://127.0.0.1:1929"
	@echo "   API: http://127.0.0.1:1929/api"
	@echo "   Stop with: make docker-stop"

# ===============================================
# Cross-Machine Sync Commands
# ===============================================
# These commands help sync your database between multiple machines
# See docs/CROSS_MACHINE_SYNC.md for detailed instructions

sync-setup: ## Setup sync remote for cross-machine database sync
	@$(MAKE) -f Makefile.sync setup-sync

sync-push: ## Push everything (including DB) to private sync remote
	@$(MAKE) -f Makefile.sync push-sync

sync-pull: ## Pull everything (including DB) from private sync remote
	@$(MAKE) -f Makefile.sync pull-sync

sync-status: ## Show sync status and current mode
	@$(MAKE) -f Makefile.sync status-sync

sync-help: ## Show detailed sync help
	@echo "📚 Cross-Machine Sync Help"
	@echo "=========================="
	@echo ""
	@echo "This feature lets you sync your entire PM state (including database)"
	@echo "between multiple machines using a private Git remote."
	@echo ""
	@echo "Quick Start:"
	@echo "  1. Create a PRIVATE GitHub repo for sync (e.g., myproject-sync)"
	@echo "  2. Run: make sync-setup"
	@echo "  3. Enter your private repo URL when prompted"
	@echo "  4. Use: make sync-push (to save) and make sync-pull (to load)"
	@echo ""
	@echo "Commands:"
	@echo "  make sync-setup  - Initial setup (run once)"
	@echo "  make sync-push   - Push your work to sync remote"
	@echo "  make sync-pull   - Pull work from sync remote"
	@echo "  make sync-status - Check sync status"
	@echo ""
	@echo "⚠️  WARNING: Never push database to main/origin remote!"
	@echo ""
	@echo "See docs/CROSS_MACHINE_SYNC.md for full documentation"

# Quick demo that starts everything
# Ultimate quickstart command
quickstart: install-complete ## 🚀 Complete setup + Claude Code integration ready
	@echo ""
	@echo "🎯 Running quickstart script..."
	$(PYTHON) scripts/quickstart.py
	@echo ""
	@echo "🌟 Starting Web UI..."
	$(VENV_BIN)/python -m src.jira_lite.app --port $(PORT) --auto

demo-full: install-complete ## Demo: Complete system with web UI and MCP server
	@echo ""
	@echo "🎯 Starting complete demo..."
	@echo "   1. Web UI will start at http://127.0.0.1:$(PORT)"
	@echo "   2. Use 'make mcp-claude-config' for Claude Desktop setup"
	@echo "   3. Test MCP tools with 'make mcp-run-http'"
	@echo ""
	$(VENV_BIN)/python -m src.jira_lite.app --port $(PORT) --auto