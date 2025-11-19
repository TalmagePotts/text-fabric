# Testing English Translation in Browser

## Steps to Test

1. **Start Text-Fabric Browser**:
   ```bash
   cd /home/teapot/code/text-fabric
   python3 -m tf.browser.start etcbc/bhsa
   ```

2. **Access in Browser**:
   - On server: `http://localhost:14897`
   - On Mac (via Tailscale): `http://TAILSCALE_IP:14897`

3. **Enable English Translation**:
   - Click the **Options** tab in the left sidebar
   - Scroll down to find the **"English translation"** checkbox
   - Check the box

4. **Run a Query**:
   - Click the **Search** pad (query icon)
   - Enter a simple query: `word sp=verb`
   - Click **Go**

5. **Expand Results**:
   - Click the triangle (?) next to any result to expand it
   - You should see Hebrew words with English translations in parentheses
   - Example: `??????? (created)`

## Troubleshooting

### If checkbox is not visible:

The checkbox should appear in the Options tab. If it's not there:

1. Check that the code changes were applied:
   ```bash
   cd /home/teapot/code/text-fabric
   grep -n "showEnglish" tf/advanced/options.py
   ```
   Should show lines with `showEnglish` definition.

2. Restart the browser completely (Ctrl+C and restart)

### If checkbox is visible but translations don't show:

1. **Check translation files exist**:
   ```bash
   ls -lh /home/teapot/code/text-fabric/English-lineup/
   ```
   Should show:
   - `BHSA-with-interlinear-translation.csv` (~18MB)
   - `bhsa_ohb_offsets.json` (~353 bytes)

2. **Test translation provider**:
   ```bash
   cd /home/teapot/code/text-fabric
   python3 -c "from tf.advanced.english import get_english_provider; p = get_english_provider(); print(f'Enabled: {p.enabled}'); print(f'CSV: {p.csv_path}')"
   ```
   Should show `Enabled: True`

3. **Check browser console for errors**:
   - Open browser Developer Tools (F12)
   - Look for JavaScript errors in Console tab
   - Look for failed requests in Network tab

### If you see errors about missing modules:

The browser might be using a different Python environment. Make sure you're running from the correct directory:

```bash
cd /home/teapot/code/text-fabric
python3 -m tf.browser.start etcbc/bhsa
```

## Expected Output

When working correctly, you should see:

**Plain display** (collapsed results):
```
1. ??????? (created) Genesis 1:1
2. ???????? (was) Genesis 1:2
3. ?????? (said) Genesis 1:3
```

**Pretty display** (expanded results):
```
word:1
  ??????? (created)
  sp=verb
  vs=qal
  vt=perf
  ...
```

## Debug Mode

If you need to see what's happening, you can add debug output:

1. Edit `tf/advanced/render.py` around line 306:
   ```python
   showEnglish = getattr(options, 'showEnglish', False)
   print(f"DEBUG: showEnglish={showEnglish}, nType={nType}")  # ADD THIS
   if showEnglish and nType == "word":
   ```

2. Restart browser and check terminal output when expanding results

## Notes

- English translations only appear for **word** nodes (not phrases, clauses, etc.)
- Translations come from the Berean Study Bible (BSB)
- Some words may not have translations (particles, markers, etc.)
- Translations appear in gray italic text after the Hebrew
