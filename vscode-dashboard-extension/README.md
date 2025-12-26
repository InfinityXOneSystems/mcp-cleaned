# Infinity Dashboard VS Code Extension

This extension opens the Infinity Monitor (Gateway/Dashboard) inside a VS Code webview for quick access.

## Settings
- `infinityDashboard.url`: URL to load (use your Cloud Run URL or local `http://localhost:8000/`).
- `infinityDashboard.autoOpen`: auto-open on startup.

## Build & Run
```bash
cd vscode-dashboard-extension
npm install
npm run build
```

Then press F5 in VS Code to launch the Extension Development Host.
# Infinity Dashboard VS Code Extension

Full-screen dashboard shell for VS Code.

## Features
- Opens Infinity-Monitor or Command Center as a full-screen webview
- Auto-opens on VS Code startup (configurable)
- Zen Mode integration for distraction-free dashboard
- Configurable dashboard URL

## Installation

```bash
cd vscode-dashboard-extension
npm install
npm run compile
npm run package
code --install-extension infinity-dashboard-0.0.1.vsix
```

## Configuration

Settings (File > Preferences > Settings):
- `infinityDashboard.url`: Dashboard URL (default: http://localhost:8000/)
- `infinityDashboard.autoOpen`: Auto-open on startup (default: true)

## Usage

Commands (Ctrl+Shift+P):
- `Infinity Dashboard: Open` - Open dashboard
- `Infinity Dashboard: Toggle` - Toggle Zen Mode

## Development

```bash
npm install
npm run compile
# Press F5 in VS Code to launch Extension Development Host
```

## Build VSIX

```bash
npm run package
```

Produces `infinity-dashboard-0.0.1.vsix` for distribution.
