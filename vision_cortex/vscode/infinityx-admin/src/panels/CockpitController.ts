/**
 * MCP-Controlled File
 * Contract: system.cockpit_bridge
 * Agent: vc.documentor
 * Validator: pending
 * 
 * Cockpit Panel Controller
 * Bridges VS Code webview panels to MCP Orchestrator
 */

import * as vscode from "vscode";
import { mcpInvoke, mcpPipelineStatus, mcpRunPipeline, MCPResponse } from "../api/mcpClient";

/**
 * Message types sent to/from webview
 */
interface WebviewMessage {
  command: string;
  payload?: any;
}

/**
 * Creates and manages the Intelligence Cockpit panel
 */
export class CockpitController {
  private panel: vscode.WebviewPanel | undefined;
  private readonly extensionUri: vscode.Uri;

  constructor(extensionUri: vscode.Uri) {
    this.extensionUri = extensionUri;
  }

  /**
   * Show or create the cockpit panel
   */
  public show(): void {
    if (this.panel) {
      this.panel.reveal();
      return;
    }

    this.panel = vscode.window.createWebviewPanel(
      "infinityxCockpit",
      "Intelligence Cockpit",
      vscode.ViewColumn.One,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
        localResourceRoots: [this.extensionUri]
      }
    );

    this.panel.webview.html = this.getWebviewContent();
    this.panel.onDidDispose(() => { this.panel = undefined; });
    this.setupMessageHandling();
  }

  /**
   * Handle messages from webview
   */
  private setupMessageHandling(): void {
    if (!this.panel) return;

    this.panel.webview.onDidReceiveMessage(async (message: WebviewMessage) => {
      switch (message.command) {
        case "runBuilderCycle":
          await this.runBuilderCycle(message.payload?.mode || "DRY_RUN");
          break;

        case "getPipelineStatus":
          await this.getPipelineStatus();
          break;

        case "invokeAgent":
          await this.invokeAgent(
            message.payload?.agent,
            message.payload?.action,
            message.payload?.data
          );
          break;

        case "refresh":
          await this.refreshCockpit();
          break;
      }
    });
  }

  /**
   * Run Auto Builder cycle
   */
  private async runBuilderCycle(mode: "DRY_RUN" | "VALIDATED" | "LIVE"): Promise<void> {
    this.postMessage({ command: "loading", payload: { message: "Starting build cycle..." } });

    try {
      const result = await mcpRunPipeline(mode);
      this.postMessage({ command: "buildResult", payload: result });
    } catch (error) {
      this.postMessage({
        command: "error",
        payload: { message: error instanceof Error ? error.message : String(error) }
      });
    }
  }

  /**
   * Get current pipeline status
   */
  private async getPipelineStatus(): Promise<void> {
    try {
      const status = await mcpPipelineStatus();
      this.postMessage({ command: "pipelineStatus", payload: status });
    } catch (error) {
      this.postMessage({
        command: "pipelineStatus",
        payload: { status: "offline", error: String(error) }
      });
    }
  }

  /**
   * Invoke specific agent
   */
  private async invokeAgent(agent: string, action: string, data: any): Promise<void> {
    this.postMessage({ command: "loading", payload: { message: `Invoking ${agent}...` } });

    try {
      const result = await mcpInvoke(agent, action, data);
      this.postMessage({ command: "agentResult", payload: { agent, result } });
    } catch (error) {
      this.postMessage({
        command: "error",
        payload: { agent, message: error instanceof Error ? error.message : String(error) }
      });
    }
  }

  /**
   * Refresh all cockpit data
   */
  private async refreshCockpit(): Promise<void> {
    await this.getPipelineStatus();
    // Add more refresh calls as needed
  }

  /**
   * Send message to webview
   */
  private postMessage(message: WebviewMessage): void {
    this.panel?.webview.postMessage(message);
  }

  /**
   * Generate webview HTML content
   */
  private getWebviewContent(): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Intelligence Cockpit</title>
  <style>
    :root {
      --bg-primary: #0d1117;
      --bg-secondary: #161b22;
      --text-primary: #c9d1d9;
      --text-secondary: #8b949e;
      --accent: #58a6ff;
      --success: #3fb950;
      --warning: #d29922;
      --error: #f85149;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg-primary);
      color: var(--text-primary);
      margin: 0;
      padding: 20px;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }
    h1 { margin: 0; color: var(--accent); }
    .status-badge {
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
    }
    .status-idle { background: var(--bg-secondary); color: var(--text-secondary); }
    .status-running { background: var(--accent); color: var(--bg-primary); }
    .status-failed { background: var(--error); color: white; }
    .panel {
      background: var(--bg-secondary);
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 16px;
    }
    .panel-title {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 12px;
      color: var(--text-secondary);
    }
    button {
      background: var(--accent);
      color: var(--bg-primary);
      border: none;
      padding: 8px 16px;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
    }
    button:hover { opacity: 0.9; }
    button.secondary {
      background: var(--bg-secondary);
      color: var(--text-primary);
      border: 1px solid var(--text-secondary);
    }
    .agent-list { list-style: none; padding: 0; margin: 0; }
    .agent-item {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid var(--bg-primary);
    }
    .agent-id { font-family: monospace; color: var(--accent); }
    .agent-status { font-size: 12px; color: var(--text-secondary); }
    #output {
      font-family: monospace;
      font-size: 12px;
      background: var(--bg-primary);
      padding: 12px;
      border-radius: 4px;
      max-height: 200px;
      overflow-y: auto;
      white-space: pre-wrap;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🧠 Intelligence Cockpit</h1>
    <span id="status" class="status-badge status-idle">Idle</span>
  </div>

  <div class="panel">
    <div class="panel-title">AUTO BUILDER CONTROLS</div>
    <button onclick="runBuilder('DRY_RUN')">🔍 Dry Run</button>
    <button onclick="runBuilder('VALIDATED')" class="secondary">✅ Validated</button>
    <button onclick="runBuilder('LIVE')" class="secondary">🚀 Live</button>
  </div>

  <div class="panel">
    <div class="panel-title">AGENT PIPELINE</div>
    <ul class="agent-list">
      <li class="agent-item"><span class="agent-id">builder.architect</span><span class="agent-status">Ready</span></li>
      <li class="agent-item"><span class="agent-id">builder.synthesizer</span><span class="agent-status">Ready</span></li>
      <li class="agent-item"><span class="agent-id">builder.critic</span><span class="agent-status">Ready</span></li>
      <li class="agent-item"><span class="agent-id">builder.integrator</span><span class="agent-status">Ready</span></li>
      <li class="agent-item"><span class="agent-id">builder.guardian</span><span class="agent-status">Ready</span></li>
    </ul>
  </div>

  <div class="panel">
    <div class="panel-title">OUTPUT</div>
    <div id="output">Ready for commands...</div>
  </div>

  <script>
    const vscode = acquireVsCodeApi();

    function runBuilder(mode) {
      vscode.postMessage({ command: 'runBuilderCycle', payload: { mode } });
      log('Starting build cycle: ' + mode);
    }

    function log(msg) {
      const output = document.getElementById('output');
      output.textContent += '\\n[' + new Date().toISOString() + '] ' + msg;
      output.scrollTop = output.scrollHeight;
    }

    window.addEventListener('message', event => {
      const { command, payload } = event.data;
      switch (command) {
        case 'loading':
          document.getElementById('status').className = 'status-badge status-running';
          document.getElementById('status').textContent = 'Running';
          log(payload.message);
          break;
        case 'buildResult':
          document.getElementById('status').className = 'status-badge status-idle';
          document.getElementById('status').textContent = 'Idle';
          log('Build result: ' + JSON.stringify(payload, null, 2));
          break;
        case 'error':
          document.getElementById('status').className = 'status-badge status-failed';
          document.getElementById('status').textContent = 'Error';
          log('ERROR: ' + payload.message);
          break;
      }
    });

    // Initial status check
    vscode.postMessage({ command: 'getPipelineStatus' });
  </script>
</body>
</html>`;
  }
}
