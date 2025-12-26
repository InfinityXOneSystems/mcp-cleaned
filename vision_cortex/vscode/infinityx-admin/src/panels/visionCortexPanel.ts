import * as vscode from "vscode";
import { startWebSocketFeed } from "../websocket";

export class VisionCortexPanel {
  static show(uri: vscode.Uri) {
    const p = vscode.window.createWebviewPanel(
      "visionCortex","🧠 Vision Cortex",vscode.ViewColumn.One,{ enableScripts: true }
    );
    p.webview.html = this.html();
    startWebSocketFeed(p,"visionCortex");
  }
  static html() {
    return `
<html>
  <body style="background:#001014;color:#fff;font-family:system-ui;padding:20px;">
    <h2>Vision Cortex</h2>
    <pre id="out">Awaiting feed...</pre>
    <script>
      const vscode = acquireVsCodeApi();
      window.addEventListener("message", e=>{
        document.getElementById("out").innerText = JSON.stringify(e.data,null,2);
      });
    </script>
  </body>
</html>`;
  }
}