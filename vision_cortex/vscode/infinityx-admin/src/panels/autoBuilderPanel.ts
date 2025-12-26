import * as vscode from "vscode";
import { mcpInvoke } from "../api/mcpClient";

export class AutoBuilderPanel {
  static show(uri: vscode.Uri) {
    const p = vscode.window.createWebviewPanel(
      "autoBuilder","⚙️ Auto Builder",vscode.ViewColumn.One,{ enableScripts: true }
    );
    p.webview.html = `
<html>
  <body style="background:#0a0a0a;color:#0f0;font-family:system-ui;padding:20px;">
    <h2>Auto Builder</h2>
    <button id="run">Run DRY_RUN</button>
    <pre id="out"></pre>
    <script>
      const vscode = acquireVsCodeApi();
      document.getElementById("run").onclick = ()=>vscode.postMessage({cmd:"run"});
      window.addEventListener("message", e=>{
        document.getElementById("out").innerText = JSON.stringify(e.data,null,2);
      });
    </script>
  </body>
</html>`;
    p.webview.onDidReceiveMessage(async m=>{
      if(m.cmd==="run"){
        const res = await mcpInvoke("builder.integrator","build_cycle",{mode:"DRY_RUN"});
        p.webview.postMessage(res);
      }
    });
  }
}