import * as vscode from 'vscode';
import * as path from 'path';

export function activate(context: vscode.ExtensionContext) {
	const command = vscode.commands.registerCommand('trading.open', () => {
		const panel = vscode.window.createWebviewPanel(
			'tradingDashboard',
			'🤖 Trading Command Center',
			vscode.ViewColumn.One,
			{
				enableScripts: true,
				retainContextWhenHidden: true,
				localResourceRoots: [
					vscode.Uri.file(path.join(context.extensionPath, 'resources'))
				]
			}
		);

		// Set the webview's initial html content
		panel.webview.html = getWebviewContent(panel.webview, context);

		// Handle messages from the webview
		panel.webview.onDidReceiveMessage(
			message => {
				switch (message.command) {
					case 'log':
						console.log(message.text);
						return;
					case 'chat':
						handleChat(message.text, panel.webview);
						return;
					case 'trade':
						handleTrade(message.data, panel.webview);
						return;
					case 'getPortfolio':
						getPortfolioData(panel.webview);
						return;
				}
			},
			undefined,
			context.subscriptions
		);
	});

	context.subscriptions.push(command);

	// Open panel on startup
	vscode.commands.executeCommand('trading.open');
}

function getWebviewContent(webview: vscode.Webview, context: vscode.ExtensionContext): string {
	return `<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Trading Command Center</title>
	<style>
		* {
			margin: 0;
			padding: 0;
			box-sizing: border-box;
		}

		:root {
			--primary: #39FF14;
			--secondary: #0080FF;
			--accent-yellow: #FFFF00;
			--accent-red: #FF1744;
			--accent-green: #00E676;
			--bg-dark: rgba(0, 0, 0, 0.7);
			--bg-glass: rgba(15, 15, 35, 0.6);
			--border-silver: #C0C0C0;
			--text-primary: #FFFFFF;
			--text-secondary: #A0A0A0;
		}

		html, body {
			width: 100%;
			height: 100vh;
			background: linear-gradient(135deg, #0a0a15 0%, #1a0a2e 50%, #0f0a20 100%);
			color: var(--text-primary);
			font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
			overflow: hidden;
		}

		body {
			display: grid;
			grid-template-columns: 1fr 1fr;
			gap: 2px;
			padding: 10px;
		}

		/* CHAT PANEL */
		.panel {
			display: flex;
			flex-direction: column;
			background: var(--bg-glass);
			border: 1px solid var(--border-silver);
			border-radius: 8px;
			backdrop-filter: blur(10px);
			overflow: hidden;
		}

		.panel-header {
			background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
			padding: 15px;
			font-weight: bold;
			font-size: 1.2em;
			text-shadow: 0 0 10px rgba(57, 255, 20, 0.5);
			display: flex;
			align-items: center;
			gap: 10px;
		}

		.panel-header-icon {
			font-size: 1.5em;
		}

		/* CHAT PANEL */
		#chatPanel {
			display: flex;
			flex-direction: column;
			background: linear-gradient(135deg, var(--bg-glass) 0%, rgba(0, 128, 255, 0.05) 100%);
		}

		#messages {
			flex: 1;
			overflow-y: auto;
			padding: 15px;
			display: flex;
			flex-direction: column;
			gap: 12px;
		}

		.message {
			padding: 12px 15px;
			border-radius: 6px;
			max-width: 90%;
			word-wrap: break-word;
			animation: slideIn 0.3s ease;
		}

		@keyframes slideIn {
			from {
				opacity: 0;
				transform: translateY(10px);
			}
			to {
				opacity: 1;
				transform: translateY(0);
			}
		}

		.message.user {
			align-self: flex-end;
			background: linear-gradient(135deg, var(--secondary) 0%, rgba(0, 128, 255, 0.8) 100%);
			border: 1px solid var(--secondary);
			color: #000;
		}

		.message.ai {
			align-self: flex-start;
			background: linear-gradient(135deg, rgba(57, 255, 20, 0.1) 0%, rgba(57, 255, 20, 0.05) 100%);
			border: 1px solid var(--primary);
			color: var(--primary);
		}

		.message.system {
			align-self: center;
			background: linear-gradient(135deg, var(--accent-yellow) 0%, rgba(255, 255, 0, 0.5) 100%);
			border: 1px solid var(--accent-yellow);
			color: #000;
			width: 90%;
			text-align: center;
		}

		#inputArea {
			padding: 12px;
			border-top: 1px solid var(--border-silver);
			display: flex;
			gap: 8px;
			background: linear-gradient(135deg, rgba(0, 0, 0, 0.3) 0%, rgba(0, 128, 255, 0.05) 100%);
		}

		#chatInput {
			flex: 1;
			background: rgba(0, 0, 0, 0.4);
			border: 1px solid var(--primary);
			color: var(--primary);
			padding: 10px 12px;
			border-radius: 4px;
			font-size: 0.95em;
		}

		#chatInput::placeholder {
			color: var(--text-secondary);
		}

		#chatInput:focus {
			outline: none;
			box-shadow: 0 0 15px rgba(57, 255, 20, 0.5);
			border-color: var(--primary);
		}

		#sendBtn {
			background: linear-gradient(135deg, var(--primary) 0%, var(--accent-green) 100%);
			color: #000;
			border: none;
			padding: 10px 15px;
			border-radius: 4px;
			font-weight: bold;
			cursor: pointer;
			transition: all 0.3s ease;
		}

		#sendBtn:hover {
			transform: scale(1.05);
			box-shadow: 0 0 15px rgba(57, 255, 20, 0.6);
		}

		/* DASHBOARD PANEL */
		#dashPanel {
			display: flex;
			flex-direction: column;
			background: linear-gradient(135deg, var(--bg-glass) 0%, rgba(0, 200, 255, 0.05) 100%);
		}

		.dashboard-content {
			flex: 1;
			overflow-y: auto;
			padding: 15px;
			display: flex;
			flex-direction: column;
			gap: 15px;
		}

		.card {
			background: rgba(0, 0, 0, 0.4);
			border: 1px solid var(--border-silver);
			border-radius: 6px;
			padding: 15px;
			backdrop-filter: blur(5px);
			transition: all 0.3s ease;
		}

		.card:hover {
			background: rgba(0, 128, 255, 0.1);
			box-shadow: 0 0 15px rgba(0, 128, 255, 0.3);
		}

		.card-title {
			color: var(--primary);
			font-weight: bold;
			margin-bottom: 10px;
			font-size: 0.95em;
			text-transform: uppercase;
			letter-spacing: 1px;
		}

		.stat-row {
			display: flex;
			justify-content: space-between;
			margin: 8px 0;
			font-size: 0.9em;
		}

		.stat-label {
			color: var(--text-secondary);
		}

		.stat-value {
			color: var(--primary);
			font-weight: bold;
		}

		.stat-value.positive {
			color: var(--accent-green);
		}

		.stat-value.negative {
			color: var(--accent-red);
		}

		.stat-value.neutral {
			color: var(--secondary);
		}

		.mode-buttons {
			display: grid;
			grid-template-columns: repeat(3, 1fr);
			gap: 10px;
			margin: 0;
		}

		.mode-btn {
			padding: 12px 8px;
			border: 2px solid transparent;
			border-radius: 4px;
			background: rgba(0, 0, 0, 0.3);
			color: var(--text-primary);
			cursor: pointer;
			font-weight: bold;
			font-size: 0.85em;
			transition: all 0.3s ease;
			text-align: center;
		}

		.mode-btn.auto {
			border-color: var(--primary);
		}

		.mode-btn.auto:hover {
			background: rgba(57, 255, 20, 0.2);
			box-shadow: 0 0 15px rgba(57, 255, 20, 0.5);
		}

		.mode-btn.hybrid {
			border-color: var(--accent-yellow);
		}

		.mode-btn.hybrid:hover {
			background: rgba(255, 255, 0, 0.1);
			box-shadow: 0 0 15px rgba(255, 255, 0, 0.4);
		}

		.mode-btn.manual {
			border-color: var(--accent-red);
		}

		.mode-btn.manual:hover {
			background: rgba(255, 23, 68, 0.2);
			box-shadow: 0 0 15px rgba(255, 23, 68, 0.5);
		}

		.positions-list {
			display: flex;
			flex-direction: column;
			gap: 8px;
		}

		.position-item {
			background: rgba(0, 0, 0, 0.5);
			padding: 10px;
			border-left: 3px solid var(--secondary);
			border-radius: 4px;
			font-size: 0.85em;
			display: flex;
			justify-content: space-between;
			align-items: center;
		}

		.position-item.positive {
			border-left-color: var(--accent-green);
		}

		.position-item.negative {
			border-left-color: var(--accent-red);
		}

		.position-asset {
			font-weight: bold;
			color: var(--primary);
		}

		.position-pnl {
			font-weight: bold;
		}

		.scrollbar::-webkit-scrollbar {
			width: 6px;
		}

		.scrollbar::-webkit-scrollbar-track {
			background: rgba(0, 0, 0, 0.2);
			border-radius: 3px;
		}

		.scrollbar::-webkit-scrollbar-thumb {
			background: var(--primary);
			border-radius: 3px;
		}

		.scrollbar::-webkit-scrollbar-thumb:hover {
			background: var(--secondary);
		}

		#messages, .dashboard-content {
			scrollbar-color: var(--primary) rgba(0, 0, 0, 0.2);
			scrollbar-width: thin;
		}

		/* RESPONSIVE */
		@media (max-width: 1000px) {
			body {
				grid-template-columns: 1fr;
			}

			.mode-buttons {
				grid-template-columns: 1fr;
			}
		}
	</style>
</head>
<body>
	<!-- CHAT PANEL -->
	<div id="chatPanel" class="panel">
		<div class="panel-header">
			<span class="panel-header-icon">💬</span>
			<span>AI Chat Assistant</span>
		</div>
		<div id="messages" class="scrollbar"></div>
		<div id="inputArea">
			<input type="text" id="chatInput" placeholder="Ask me anything about trading...">
			<button id="sendBtn">Send</button>
		</div>
	</div>

	<!-- DASHBOARD PANEL -->
	<div id="dashPanel" class="panel">
		<div class="panel-header">
			<span class="panel-header-icon">📊</span>
			<span>Trading Dashboard</span>
		</div>
		<div class="dashboard-content scrollbar">
			<!-- TRADING MODES -->
			<div class="card">
				<div class="card-title">🎮 Trading Mode</div>
				<div class="mode-buttons">
					<button class="mode-btn auto" onclick="selectMode('auto')">🤖 AUTO</button>
					<button class="mode-btn hybrid" onclick="selectMode('hybrid')">🤝 HYBRID</button>
					<button class="mode-btn manual" onclick="selectMode('manual')">👤 MANUAL</button>
				</div>
			</div>

			<!-- ACCOUNT SUMMARY -->
			<div class="card">
				<div class="card-title">💰 Account</div>
				<div class="stat-row">
					<span class="stat-label">Balance</span>
					<span class="stat-value" id="balance">$5,000.00</span>
				</div>
				<div class="stat-row">
					<span class="stat-label">Total Value</span>
					<span class="stat-value" id="totalValue">$5,000.00</span>
				</div>
				<div class="stat-row">
					<span class="stat-label">P&L</span>
					<span class="stat-value neutral" id="pnl">+$0.00</span>
				</div>
				<div class="stat-row">
					<span class="stat-label">Return %</span>
					<span class="stat-value neutral" id="returnPct">+0.00%</span>
				</div>
			</div>

			<!-- PORTFOLIO -->
			<div class="card">
				<div class="card-title">📈 Open Positions</div>
				<div class="stat-row">
					<span class="stat-label">Active Trades</span>
					<span class="stat-value" id="positionCount">21</span>
				</div>
				<div id="positionsList" class="positions-list">
					<div class="position-item">
						<span class="position-asset">BTC</span>
						<span class="position-pnl positive">+2.3%</span>
					</div>
					<div class="position-item">
						<span class="position-asset">MSFT</span>
						<span class="position-pnl positive">+1.8%</span>
					</div>
					<div class="position-item">
						<span class="position-asset">GOLD</span>
						<span class="position-pnl negative">-0.5%</span>
					</div>
				</div>
			</div>

			<!-- STATISTICS -->
			<div class="card">
				<div class="card-title">📊 Statistics</div>
				<div class="stat-row">
					<span class="stat-label">Win Rate</span>
					<span class="stat-value positive">65.2%</span>
				</div>
				<div class="stat-row">
					<span class="stat-label">Avg Trade</span>
					<span class="stat-value positive">+2.1%</span>
				</div>
				<div class="stat-row">
					<span class="stat-label">Max Drawdown</span>
					<span class="stat-value negative">-8.2%</span>
				</div>
			</div>
		</div>
	</div>

	<script>
		const vscode = acquireVsCodeApi();

		// Chat functionality
		const chatInput = document.getElementById('chatInput');
		const sendBtn = document.getElementById('sendBtn');
		const messagesContainer = document.getElementById('messages');

		sendBtn.addEventListener('click', sendMessage);
		chatInput.addEventListener('keypress', (e) => {
			if (e.key === 'Enter') sendMessage();
		});

		function sendMessage() {
			const text = chatInput.value.trim();
			if (!text) return;

			// Add user message to chat
			addMessage(text, 'user');
			
			// Send to extension
			vscode.postMessage({
				command: 'chat',
				text: text
			});

			chatInput.value = '';
		}

		function addMessage(text, sender = 'ai') {
			const messageEl = document.createElement('div');
			messageEl.className = 'message ' + sender;
			messageEl.textContent = text;
			messagesContainer.appendChild(messageEl);
			messagesContainer.scrollTop = messagesContainer.scrollHeight;
		}

		function selectMode(mode) {
			const modes = {
				'auto': '🤖 Full Auto Mode Selected',
				'hybrid': '🤝 Hybrid Mode Selected',
				'manual': '👤 Manual Mode Selected'
			};
			addMessage(modes[mode], 'system');
		}

		// Initial messages
		addMessage('👋 Welcome to Trading Command Center! How can I help you today?', 'ai');
	</script>
</body>
</html>`;
}

function handleChat(message: string, webview: vscode.Webview) {
	// Simulate AI response
	const responses: { [key: string]: string } = {
		'hello': '👋 Hey there! Ready to trade?',
		'help': '📖 I can help with trading, portfolio, or account questions.',
		'portfolio': '📊 Your portfolio currently has 21 positions. Would you like details?',
		'price': '💹 Which asset do you want to know about?',
		'buy': '📈 Which asset would you like to buy?',
		'sell': '📉 Which position would you like to sell?',
		'status': '✅ All systems running smoothly!',
	};

	const lowerMessage = message.toLowerCase();
	let response = '🤔 Interesting question. Can you clarify what you\'d like to know?';

	for (const [key, value] of Object.entries(responses)) {
		if (lowerMessage.includes(key)) {
			response = value;
			break;
		}
	}

	// Send response back to webview
	setTimeout(() => {
		webview.postMessage({
			command: 'addMessage',
			text: response,
			sender: 'ai'
		});
	}, 500);
}

function handleTrade(data: any, webview: vscode.Webview) {
	const message = `📈 Trade executed: ${data.asset} - ${data.action}`;
	webview.postMessage({
		command: 'addMessage',
		text: message,
		sender: 'system'
	});
}

function getPortfolioData(webview: vscode.Webview) {
	webview.postMessage({
		command: 'updatePortfolio',
		data: {
			balance: 2226.11,
			totalValue: 5000,
			pnl: 0,
			positions: 21
		}
	});
}

export function deactivate() {}
