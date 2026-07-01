from pathlib import Path

ROOT = Path("repo-setup-agent")

DIRECTORIES = [
    "app/api",
    "app/agent",
    "app/repository",
    "app/parser",
    "app/context",
    "app/llm",
    "app/cache",
    "app/templates",
    "app/static/css",
    "app/static/js",
    "app/static/assets",
    "app/utils",
    "workspaces",
    "logs",
    "tests",
]

FILES = [
    # Root
    ".env",
    "requirements.txt",
    "Dockerfile",
    "docker-compose.yml",
    "README.md",
    ".gitignore",

    # App
    "app/main.py",
    "app/config.py",
    "app/dependencies.py",

    # API
    "app/api/routes.py",
    "app/api/repository.py",
    "app/api/chat.py",
    "app/api/websocket.py",

    # Agent
    "app/agent/orchestrator.py",
    "app/agent/prompt_builder.py",
    "app/agent/tool_executor.py",
    "app/agent/system_prompt.py",

    # Repository
    "app/repository/downloader.py",
    "app/repository/extractor.py",
    "app/repository/detector.py",
    "app/repository/analyzer.py",
    "app/repository/setup_generator.py",
    "app/repository/cleanup.py",

    # Parser
    "app/parser/ast_parser.py",
    "app/parser/import_map.py",
    "app/parser/config_parser.py",

    # Context
    "app/context/manager.py",
    "app/context/skeleton.py",
    "app/context/function_loader.py",
    "app/context/file_loader.py",
    "app/context/working_set.py",

    # LLM
    "app/llm/gemini.py",
    "app/llm/tools.py",
    "app/llm/token_counter.py",

    # Cache
    "app/cache/redis_client.py",
    "app/cache/session_cache.py",
    "app/cache/compression.py",

    # Templates
    "app/templates/base.html",
    "app/templates/index.html",
    "app/templates/setup.html",
    "app/templates/chat.html",

    # Static
    "app/static/css/style.css",

    "app/static/js/app.js",
    "app/static/js/chat.js",
    "app/static/js/repository.js",
    "app/static/js/api.js",

    # Utils
    "app/utils/filesystem.py",
    "app/utils/github.py",
    "app/utils/logger.py",
    "app/utils/helpers.py",
]


def create_structure():
    ROOT.mkdir(exist_ok=True)

    for directory in DIRECTORIES:
        (ROOT / directory).mkdir(parents=True, exist_ok=True)

    for file in FILES:
        path = ROOT / file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    print(f"Project structure created successfully at:\n{ROOT.resolve()}")


if __name__ == "__main__":
    create_structure()