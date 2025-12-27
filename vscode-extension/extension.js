const vscode = require('vscode');
const path = require('path');
const fs = require('fs');

function activate(context) {
    context.subscriptions.push(
        vscode.commands.registerCommand('mcp.headless.open', () => {
            const panel = vscode.window.createWebviewPanel(
                'mcpHeadless',
                'MCP Headless Agents',
                vscode.ViewColumn.One,
                {
                    enableScripts: true,
                }
            );

            const htmlPath = path.join(context.extensionPath, 'panel.html');
            let html = '<h1>Panel missing</h1>';
            try {
                html = fs.readFileSync(htmlPath, 'utf8');
            } catch (e) {
                console.error(e);
            }

            panel.webview.html = html;

            // Handle messages from the webview
            panel.webview.onDidReceiveMessage(async message => {
                if (message.command === 'fetchTeam') {
                    const gateway = vscode.workspace.getConfiguration('mcp').get('gatewayUrl') || 'http://localhost:8000';
                    try {
                        const resp = await fetch(`${gateway}/api/agents/headless_team`);
                        const json = await resp.json();
                        panel.webview.postMessage({ command: 'team', payload: json });
                    } catch (e) {
                        panel.webview.postMessage({ command: 'error', payload: String(e) });
                    }
                }
                if (message.command === 'runAgent') {
                    const gateway = vscode.workspace.getConfiguration('mcp').get('gatewayUrl') || 'http://localhost:8000';
                    try {
                        const resp = await fetch(`${gateway}/api/agents/headless_team/execute`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(message.payload)
                        });
                        const json = await resp.json();
                        panel.webview.postMessage({ command: 'runResult', payload: json });
                    } catch (e) {
                        panel.webview.postMessage({ command: 'error', payload: String(e) });
                    }
                }
            });
        })
    );
}

function deactivate() {}

module.exports = { activate, deactivate };
