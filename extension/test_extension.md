# Trading Command Center Extension - Testing Guide

## Quick Test

1. **Install the extension**:
   ```powershell
   code --install-extension extension\trading-command-center-1.0.0.vsix
   ```

2. **Activate**:
   - Press `Ctrl+Shift+T` (Windows/Linux) or `Cmd+Shift+T` (Mac)
   - OR run command: `Trading: Open Trading Command Center`

3. **Verify**:
   - ✅ Two-panel dashboard opens (Chat + Dashboard)
   - ✅ Chat input accepts messages
   - ✅ Dashboard shows portfolio stats
   - ✅ Mode buttons (AUTO/HYBRID/MANUAL) respond

## Manual Testing Checklist

- [ ] Extension activates without errors
- [ ] Webview panel loads with correct styling
- [ ] Chat input sends messages
- [ ] AI responses appear after delay
- [ ] Mode buttons trigger system messages
- [ ] Portfolio stats display correctly
- [ ] Scrolling works in both panels
- [ ] Panel persists when hidden/shown

## Development Commands

```powershell
# Compile TypeScript
npm run compile --prefix extension

# Watch mode (auto-compile on save)
npm run watch --prefix extension

# Package extension
npm run package --prefix extension
```

## Troubleshooting

**Extension doesn't activate**: Check VS Code Output panel → "Trading Command Center" for logs.

**Type errors**: Run `npm run compile --prefix extension` to see TypeScript errors.

**Missing dependencies**: Run `npm install --prefix extension`.
