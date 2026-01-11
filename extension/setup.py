"""
Simple VS Code Extension Loader - No build required
Serves the extension directly from Python
"""

import json


def create_extension_manifest():
    """Create VS Code extension manifest"""
    manifest = {
        "name": "trading-command-center",
        "displayName": "🤖 Trading Command Center",
        "description": "AI Trading Dashboard with Integrated Chat",
        "version": "1.0.0",
        "publisher": "local",
        "engines": {"vscode": "^1.70.0"},
        "categories": ["Dashboard"],
        "activationEvents": ["onCommand:trading.open", "onStartupFinished"],
        "main": "./src/extension.js",
        "contributes": {
            "commands": [
                {
                    "command": "trading.open",
                    "title": "Open Trading Command Center",
                    "category": "Trading",
                }
            ],
            "keybindings": [
                {"command": "trading.open", "key": "ctrl+shift+t", "mac": "cmd+shift+t"}
            ],
        },
    }
    return manifest


print(json.dumps(create_extension_manifest(), indent=2))
