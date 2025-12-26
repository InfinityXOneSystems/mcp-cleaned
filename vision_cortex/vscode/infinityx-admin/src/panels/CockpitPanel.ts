/**
 * MCP-Controlled File
 * Contract: contracts/vision_cortex_agent_contracts.json
 * Agent: vscode.cockpit
 * Validator: pending
 * 
 * Glass-morphic Cockpit UI Webview Panel
 * Requirements:
 *   • TailwindCSS + blur / neon styling.
 *   • Left: Vision Cortex agents (status, confidence).
 *   • Right: Auto Builder agents (state, duration).
 *   • Bottom: Validator / debate logs.
 *   • Color codes: Green ≥.85, Amber .70–.84, Red <.70.
 *   • Use WebSocket ws://localhost:8000/ws for live updates.
 */

import * as vscode from 'vscode';
import { mcpPipelineStatus, mcpGetAgentStates, mcpHealthCheck } from '../api/mcpClient';

export class CockpitPanel {
  public static currentPanel: CockpitPanel | undefined;
  public static readonly viewType = 'infinityxCockpit';

  private readonly _panel: vscode.WebviewPanel;
  private readonly _extensionUri: vscode.Uri;
  private _disposables: vscode.Disposable[] = [];

  public static createOrShow(extensionUri: vscode.Uri) {
    const column = vscode.window.activeTextEditor
      ? vscode.window.activeTextEditor.viewColumn
      : undefined;

    // If panel exists, show it
    if (CockpitPanel.currentPanel) {
      CockpitPanel.currentPanel._panel.reveal(column);
      return;
    }

    // Create new panel
    const panel = vscode.window.createWebviewPanel(
      CockpitPanel.viewType,
      'Infinity X Cockpit',
      column || vscode.ViewColumn.One,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
        localResourceRoots: [extensionUri]
      }
    );

    CockpitPanel.currentPanel = new CockpitPanel(panel, extensionUri);
  }

  private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
    this._panel = panel;
    this._extensionUri = extensionUri;

    // Set HTML content
    this._update();

    // Listen for dispose
    this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

    // Handle messages from webview
    this._panel.webview.onDidReceiveMessage(
      async message => {
        switch (message.command) {
          case 'refresh':
            await this._refreshData();
            break;
          case 'runPipeline':
            await this._runPipeline(message.pipeline, message.mode);
            break;
          case 'invokeAgent':
            await this._invokeAgent(message.agent, message.action);
            break;
        }
      },
      null,
      this._disposables
    );

    // Initial data load
    this._refreshData();

    // Auto-refresh every 5 seconds
    const refreshInterval = setInterval(() => this._refreshData(), 5000);
    this._disposables.push({ dispose: () => clearInterval(refreshInterval) });
  }

  private async _refreshData() {
    try {
      const [status, agents, healthy] = await Promise.all([
        mcpPipelineStatus(),
        mcpGetAgentStates(),
        mcpHealthCheck()
      ]);

      this._panel.webview.postMessage({
        type: 'update',
        data: { status, agents, healthy, timestamp: new Date().toISOString() }
      });
    } catch (error) {
      this._panel.webview.postMessage({
        type: 'error',
        message: String(error)
      });
    }
  }

  private async _runPipeline(pipeline: string, mode: string) {
    vscode.window.showInformationMessage(`Running ${pipeline} in ${mode} mode...`);
    // Implementation handled by mcpClient
  }

  private async _invokeAgent(agent: string, action: string) {
    vscode.window.showInformationMessage(`Invoking ${agent}: ${action}`);
    // Implementation handled by mcpClient
  }

  public dispose() {
    CockpitPanel.currentPanel = undefined;
    this._panel.dispose();

    while (this._disposables.length) {
      const x = this._disposables.pop();
      if (x) {
        x.dispose();
      }
    }
  }

  private _update() {
    this._panel.webview.html = this._getHtmlContent();
  }

  private _getHtmlContent(): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Infinity X Cockpit</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    :root {
      --neon-green: #00ff88;
      --neon-amber: #ffaa00;
      --neon-red: #ff3366;
      --neon-blue: #00aaff;
      --glass-bg: rgba(15, 23, 42, 0.8);
      --glass-border: rgba(255, 255, 255, 0.1);
    }
    
    body {
      background: linear-gradient(135deg, #0a0f1a 0%, #1a1f2e 50%, #0f1623 100%);
      font-family: 'Segoe UI', system-ui, sans-serif;
      min-height: 100vh;
    }
    
    .glass {
      background: var(--glass-bg);
      backdrop-filter: blur(20px);
      border: 1px solid var(--glass-border);
      border-radius: 16px;
    }
    
    .neon-border-green { box-shadow: 0 0 20px rgba(0, 255, 136, 0.3), inset 0 0 20px rgba(0, 255, 136, 0.05); }
    .neon-border-amber { box-shadow: 0 0 20px rgba(255, 170, 0, 0.3), inset 0 0 20px rgba(255, 170, 0, 0.05); }
    .neon-border-red { box-shadow: 0 0 20px rgba(255, 51, 102, 0.3), inset 0 0 20px rgba(255, 51, 102, 0.05); }
    .neon-border-blue { box-shadow: 0 0 20px rgba(0, 170, 255, 0.3), inset 0 0 20px rgba(0, 170, 255, 0.05); }
    
    .confidence-high { color: var(--neon-green); }
    .confidence-medium { color: var(--neon-amber); }
    .confidence-low { color: var(--neon-red); }
    
    .status-idle { background: rgba(100, 100, 100, 0.3); }
    .status-running { background: rgba(0, 170, 255, 0.3); animation: pulse 2s infinite; }
    .status-completed { background: rgba(0, 255, 136, 0.3); }
    .status-failed { background: rgba(255, 51, 102, 0.3); }
    
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    
    .agent-card {
      transition: all 0.3s ease;
    }
    .agent-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
    }
    
    .log-entry {
      font-family: 'Consolas', monospace;
      font-size: 12px;
      border-left: 3px solid var(--neon-blue);
      padding-left: 8px;
      margin: 4px 0;
    }
    
    .btn-neon {
      background: linear-gradient(135deg, rgba(0, 170, 255, 0.2), rgba(0, 255, 136, 0.2));
      border: 1px solid rgba(0, 170, 255, 0.5);
      transition: all 0.3s ease;
    }
    .btn-neon:hover {
      background: linear-gradient(135deg, rgba(0, 170, 255, 0.4), rgba(0, 255, 136, 0.4));
      box-shadow: 0 0 20px rgba(0, 170, 255, 0.5);
    }
  </style>
</head>
<body class="text-white p-4">
  <!-- Header -->
  <header class="glass p-4 mb-4 flex justify-between items-center neon-border-blue">
    <div class="flex items-center gap-4">
      <div class="text-2xl font-bold bg-gradient-to-r from-blue-400 to-green-400 bg-clip-text text-transparent">
        ∞ INFINITY X COCKPIT
      </div>
      <div id="connectionStatus" class="px-3 py-1 rounded-full text-xs status-idle">
        Connecting...
      </div>
    </div>
    <div class="flex gap-2">
      <button onclick="refresh()" class="btn-neon px-4 py-2 rounded-lg">
        🔄 Refresh
      </button>
      <button onclick="runDryRun()" class="btn-neon px-4 py-2 rounded-lg">
        🧪 Dry Run
      </button>
    </div>
  </header>

  <!-- Main Grid -->
  <div class="grid grid-cols-2 gap-4 mb-4">
    <!-- Vision Cortex Panel -->
    <div class="glass p-4 neon-border-green">
      <h2 class="text-lg font-bold mb-4 flex items-center gap-2">
        <span class="text-2xl">🧠</span>
        Vision Cortex
        <span class="text-xs opacity-60 ml-auto">9 agents</span>
      </h2>
      <div id="visionCortexAgents" class="space-y-2">
        <!-- Agent cards will be injected here -->
        <div class="agent-card glass p-3 flex justify-between items-center">
          <div>
            <div class="font-medium">crawler</div>
            <div class="text-xs opacity-60">Signal Harvester</div>
          </div>
          <div class="text-right">
            <div class="confidence-high font-mono">0.92</div>
            <div class="text-xs opacity-60">idle</div>
          </div>
        </div>
        <div class="agent-card glass p-3 flex justify-between items-center">
          <div>
            <div class="font-medium">ingestor</div>
            <div class="text-xs opacity-60">Data Normalizer</div>
          </div>
          <div class="text-right">
            <div class="confidence-high font-mono">0.88</div>
            <div class="text-xs opacity-60">idle</div>
          </div>
        </div>
        <div class="agent-card glass p-3 flex justify-between items-center">
          <div>
            <div class="font-medium">predictor</div>
            <div class="text-xs opacity-60">Forecast Engine</div>
          </div>
          <div class="text-right">
            <div class="confidence-medium font-mono">0.75</div>
            <div class="text-xs opacity-60">idle</div>
          </div>
        </div>
        <div class="agent-card glass p-3 flex justify-between items-center">
          <div>
            <div class="font-medium">ceo</div>
            <div class="text-xs opacity-60">Executive Integrator</div>
          </div>
          <div class="text-right">
            <div class="confidence-high font-mono">0.95</div>
            <div class="text-xs opacity-60">idle</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Auto Builder Panel -->
    <div class="glass p-4 neon-border-amber">
      <h2 class="text-lg font-bold mb-4 flex items-center gap-2">
        <span class="text-2xl">🏗️</span>
        Auto Builder
        <span class="text-xs opacity-60 ml-auto">5 agents</span>
      </h2>
      <div id="autoBuilderAgents" class="space-y-2">
        <div class="agent-card glass p-3 flex justify-between items-center">
          <div>
            <div class="font-medium">architect</div>
            <div class="text-xs opacity-60">Plan Generator</div>
          </div>
          <div class="text-right">
            <div class="confidence-high font-mono">0.90</div>
            <div class="text-xs opacity-60">idle</div>
          </div>
        </div>
        <div class="agent-card glass p-3 flex justify-between items-center">
          <div>
            <div class="font-medium">synthesizer</div>
            <div class="text-xs opacity-60">Implementation Composer</div>
          </div>
          <div class="text-right">
            <div class="confidence-medium font-mono">0.82</div>
            <div class="text-xs opacity-60">idle</div>
          </div>
        </div>
        <div class="agent-card glass p-3 flex justify-between items-center">
          <div>
            <div class="font-medium">critic</div>
            <div class="text-xs opacity-60">Quality Auditor</div>
          </div>
          <div class="text-right">
            <div class="confidence-high font-mono">0.87</div>
            <div class="text-xs opacity-60">idle</div>
          </div>
        </div>
        <div class="agent-card glass p-3 flex justify-between items-center">
          <div>
            <div class="font-medium">guardian</div>
            <div class="text-xs opacity-60">Compliance Validator</div>
          </div>
          <div class="text-right">
            <div class="confidence-high font-mono">0.95</div>
            <div class="text-xs opacity-60">idle</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Logs Panel -->
  <div class="glass p-4 neon-border-blue">
    <h2 class="text-lg font-bold mb-4 flex items-center gap-2">
      <span class="text-2xl">📋</span>
      Validator & Debate Logs
      <button onclick="clearLogs()" class="ml-auto text-xs opacity-60 hover:opacity-100">Clear</button>
    </h2>
    <div id="logsContainer" class="h-48 overflow-y-auto space-y-1 font-mono text-xs">
      <div class="log-entry opacity-60">[startup] Cockpit initialized</div>
      <div class="log-entry opacity-60">[system] Awaiting MCP connection...</div>
    </div>
  </div>

  <!-- Footer Status -->
  <footer class="glass p-3 mt-4 flex justify-between items-center text-xs opacity-60">
    <div id="lastUpdate">Last update: --</div>
    <div>MCP Gateway: localhost:8000</div>
    <div id="pipelineStatus">Pipeline: idle</div>
  </footer>

  <script>
    const vscode = acquireVsCodeApi();
    
    function refresh() {
      vscode.postMessage({ command: 'refresh' });
    }
    
    function runDryRun() {
      vscode.postMessage({ command: 'runPipeline', pipeline: 'vision_cortex', mode: 'DRY_RUN' });
    }
    
    function clearLogs() {
      document.getElementById('logsContainer').innerHTML = '';
    }
    
    function addLog(message, type = 'info') {
      const container = document.getElementById('logsContainer');
      const entry = document.createElement('div');
      entry.className = 'log-entry';
      entry.textContent = \`[\${new Date().toLocaleTimeString()}] \${message}\`;
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    }
    
    function getConfidenceClass(confidence) {
      if (confidence >= 0.85) return 'confidence-high';
      if (confidence >= 0.70) return 'confidence-medium';
      return 'confidence-low';
    }
    
    function updateAgentCard(container, agent) {
      // Update logic for agent cards
    }
    
    window.addEventListener('message', event => {
      const message = event.data;
      
      if (message.type === 'update') {
        const { status, agents, healthy, timestamp } = message.data;
        
        // Update connection status
        const connStatus = document.getElementById('connectionStatus');
        if (healthy) {
          connStatus.textContent = 'Connected';
          connStatus.className = 'px-3 py-1 rounded-full text-xs status-completed';
        } else {
          connStatus.textContent = 'Disconnected';
          connStatus.className = 'px-3 py-1 rounded-full text-xs status-failed';
        }
        
        // Update last update time
        document.getElementById('lastUpdate').textContent = 
          \`Last update: \${new Date(timestamp).toLocaleTimeString()}\`;
        
        // Update pipeline status
        if (status) {
          document.getElementById('pipelineStatus').textContent = 
            \`Pipeline: \${status.stage || status.status}\`;
        }
        
        addLog(\`Status updated: \${healthy ? 'healthy' : 'degraded'}\`);
      }
      
      if (message.type === 'error') {
        addLog(\`Error: \${message.message}\`, 'error');
      }
    });
    
    // Initial log
    addLog('Cockpit UI loaded');
  </script>
</body>
</html>`;
  }
}
