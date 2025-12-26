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
/**
 * Creates and manages the Intelligence Cockpit panel
 */
export declare class CockpitController {
    private panel;
    private readonly extensionUri;
    constructor(extensionUri: vscode.Uri);
    /**
     * Show or create the cockpit panel
     */
    show(): void;
    /**
     * Handle messages from webview
     */
    private setupMessageHandling;
    /**
     * Run Auto Builder cycle
     */
    private runBuilderCycle;
    /**
     * Get current pipeline status
     */
    private getPipelineStatus;
    /**
     * Invoke specific agent
     */
    private invokeAgent;
    /**
     * Refresh all cockpit data
     */
    private refreshCockpit;
    /**
     * Send message to webview
     */
    private postMessage;
    /**
     * Generate webview HTML content
     */
    private getWebviewContent;
}
//# sourceMappingURL=CockpitController.d.ts.map