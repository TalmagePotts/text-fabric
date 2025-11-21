# API Key Storage - Implementation Summary

## What Was Implemented

Added secure API key storage with two options:

### 1. Browser localStorage (Default)
- **Auto-save**: API key is automatically saved to browser's localStorage as you type
- **Auto-load**: Key is automatically loaded when you open the browser
- **Secure**: Stored locally in your browser, never sent to any server except Gemini API
- **Clear button**: Easily remove the key from storage with one click

### 2. Environment Variable (Optional)
- **Server-side**: Set `GEMINI_API_KEY` environment variable
- **Automatic**: If set, you don't need to enter the key in the UI
- **Fallback**: UI key takes precedence if both are provided

## How It Works

### Browser Storage
1. **Enter your API key** in the password field
2. **It's automatically saved** to localStorage (no button needed)
3. **Next time you open the browser**, the key is auto-loaded
4. **Status message shows**: "🔑 API key loaded from browser storage"
5. **To remove**: Click the "Clear Key" button

### Environment Variable (Alternative)
```bash
# Set in your shell profile (~/.bashrc, ~/.zshrc, etc.)
export GEMINI_API_KEY="your-api-key-here"

# Or set when starting the browser
GEMINI_API_KEY="your-key" python -m tf.browser.start etcbc/bhsa
```

## Security Notes

### Is localStorage secure?
- ✅ **Yes for local use**: Data stays on your computer
- ✅ **HTTPS protection**: If using HTTPS, data is encrypted in transit
- ⚠️ **Browser access**: Other JavaScript on the same domain can access it
- ⚠️ **Not encrypted at rest**: Stored as plain text in browser storage

### Best Practices
1. **Use environment variable** if you're concerned about browser storage
2. **Clear the key** when using a shared computer
3. **Don't share your API key** with anyone
4. **Regenerate your key** if you think it's been compromised

## UI Changes

### New Elements
- **"Clear Key" button**: Removes API key from localStorage
- **Help text**: "💾 Your API key is saved securely in your browser and auto-loads next time"
- **Status messages**:
  - "🔑 API key loaded from browser storage" (on load)
  - "🗑️ API key cleared from storage" (after clear)

### Updated Behavior
- API key field now has tooltip: "Your Google Gemini API key (saved in browser)"
- Key is saved automatically as you type (no manual save needed)
- Clearing the field also removes it from storage

## Files Modified

- [index.html](file:///home/teapot/code/text-fabric/tf/browser/templates/index.html) - Added clear button and help text
- [tf3.0.js](file:///home/teapot/code/text-fabric/tf/browser/static/tf3.0.js) - Added localStorage save/load/clear logic
- [web.py](file:///home/teapot/code/text-fabric/tf/browser/web.py) - Added environment variable fallback
- [index.css](file:///home/teapot/code/text-fabric/tf/browser/static/index.css) - Styled clear button

## Testing

Try these scenarios:

1. **Save and reload**:
   - Enter API key
   - Refresh the page
   - Key should auto-load with status message

2. **Clear key**:
   - Click "Clear Key" button
   - Confirm the dialog
   - Key should be removed and field cleared

3. **Environment variable**:
   - Set `GEMINI_API_KEY` in your environment
   - Start browser without entering key in UI
   - Queries should still work

## Why Not System Keychain?

System keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service) would be ideal, but:

1. **Browser limitation**: Web browsers can't access system keychain for security reasons
2. **Cross-platform complexity**: Different OS have different keychain systems
3. **Server-side only**: Would require backend Python code, but API calls are made from browser

**Our solution** (localStorage + environment variable) provides:
- ✅ Convenience (auto-save/load)
- ✅ Security (local storage only)
- ✅ Flexibility (browser or server-side)
- ✅ Cross-platform (works everywhere)
