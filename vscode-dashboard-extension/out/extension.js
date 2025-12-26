"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
let dashboardPanel;
function activate(context) {
    console.log('Infinity Dashboard extension activated');
    // Auto-open on startup if configured
    const config = vscode.workspace.getConfiguration('infinityDashboard');
    if (config.get('autoOpen')) {
        setTimeout(() => openDashboard(context), 2000);
    }
    // Register commands
    context.subscriptions.push(vscode.commands.registerCommand('infinity-dashboard.open', () => {
        openDashboard(context);
    }));
    context.subscriptions.push(vscode.commands.registerCommand('infinity-dashboard.toggle', () => {
        vscode.commands.executeCommand('workbench.action.toggleZenMode');
    }));
}
function openDashboard(context) {
    const config = vscode.workspace.getConfiguration('infinityDashboard');
    const dashboardUrl = config.get('url') || 'http://localhost:8000/';
    if (dashboardPanel) {
        dashboardPanel.reveal(vscode.ViewColumn.One);
    }
    else {
        dashboardPanel = vscode.window.createWebviewPanel('infinityDashboard', 'Infinity Monitor', vscode.ViewColumn.One, {
            enableScripts: true,
            retainContextWhenHidden: true
        });
        dashboardPanel.webview.html = getWebviewContent(dashboardUrl);
        dashboardPanel.onDidDispose(() => {
            dashboardPanel = undefined;
        }, null, context.subscriptions);
        // Optional: Toggle Zen Mode for full-screen experience
        vscode.commands.executeCommand('workbench.action.toggleZenMode');
        vscode.commands.executeCommand('workbench.action.closeSidebar');
    }
}
function getWebviewContent(url) {
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
function deactivate() { }
//# sourceMappingURL=extension.js.map