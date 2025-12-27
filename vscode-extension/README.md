MCP Headless Agents Panel
=========================

This is a minimal VS Code extension that opens a webview to list and invoke the headless agents exposed by the Omni Gateway.

Installation (local development)

1. In VS Code, open this folder (`vscode-extension`) as the workspace for the extension.
2. Install dependencies (none required for this minimal extension).
3. Press F5 to run the extension in the Extension Development Host.
4. Open the command palette and run `MCP: Open Headless Agents Panel`.

Configuration

- `mcp.gatewayUrl` — base URL of your running Omni Gateway (default: `http://localhost:8000`).

Usage

- Click `Refresh Team` to fetch available agents from `/api/agents/headless_team`.
- Enter a URL and click `Run` to execute the selected agent via the gateway.

Security

- The extension talks to the Omni Gateway over HTTP. For production use, run the gateway behind TLS and use authentication headers.
