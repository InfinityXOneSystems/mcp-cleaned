import * as vscode from "vscode";
export class DebateArenaPanel {
  static show(uri: vscode.Uri) {
    const p = vscode.window.createWebviewPanel(
      "debateArena","🪩 Debate Arena",vscode.ViewColumn.One,{ enableScripts: true }
    );
    p.webview.html = `
<html>
  <body style="background:#111;color:#fff;font-family:system-ui;padding:20px;">
    <h2>Debate Arena</h2>
    <div id="log"></div>
    <script>
      const agents=["Visionary","Critic","Strategist","CEO"];
      setInterval(()=>{
        const s=agents[Math.floor(Math.random()*agents.length)];
        const msg=\`\${s}: \${["agree","disagree","reframe"][Math.floor(Math.random()*3)]}\`;
        const el=document.createElement("div");
        el.textContent=msg;
        document.getElementById("log").prepend(el);
      },3000);
    </script>
  </body>
</html>`;
  }
}