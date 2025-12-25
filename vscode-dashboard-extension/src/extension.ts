import * as vscode from 'vscode';

let dashboardPanel: vscode.WebviewPanel | undefined;

export function activate(context: vscode.ExtensionContext) {
    console.log('Infinity Dashboard extension activated');

    // Auto-open on startup if configured
    const config = vscode.workspace.getConfiguration('infinityDashboard');
    if (config.get('autoOpen')) {
        setTimeout(() => openDashboard(context), 2000);
    }

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('infinity-dashboard.open', () => {
            openDashboard(context);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('infinity-dashboard.toggle', () => {
            vscode.commands.executeCommand('workbench.action.toggleZenMode');
        })
    );
}

function openDashboard(context: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration('infinityDashboard');
    const dashboardUrl = config.get<string>('url') || 'http://localhost:8000/';

    if (dashboardPanel) {
        dashboardPanel.reveal(vscode.ViewColumn.One);
    } else {
        dashboardPanel = vscode.window.createWebviewPanel(
            'infinityDashboard',
            'Infinity Monitor',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        dashboardPanel.webview.html = getWebviewContent(dashboardUrl);

        dashboardPanel.onDidDispose(
            () => {
                dashboardPanel = undefined;
            },
            null,
            context.subscriptions
        );

        // Optional: Toggle Zen Mode for full-screen experience
        vscode.commands.executeCommand('workbench.action.toggleZenMode');
        vscode.commands.executeCommand('workbench.action.closeSidebar');
    }
}

function getWebviewContent(url: string): string {
    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body, html {
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
            }
            iframe {
                width: 100%;
                height: 100vh;
                border: none;
            }
        </style>
    </head>
    <body>
        <iframe src="${url}" allow="clipboard-read; clipboard-write"></iframe>
    </body>
    </html>`;
}

export function deactivate() {}
