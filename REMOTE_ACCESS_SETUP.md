# Remote Access Setup for Text-Fabric Browser

## Changes Made

Modified Text-Fabric to bind to `0.0.0.0` instead of `localhost`, allowing remote access via Tailscale.

### Files Modified

1. **`tf/parameters.py`**
   - Changed `HOST = "localhost"` to `HOST = "0.0.0.0"`
   - Added `HOST_DISPLAY = "localhost"` for local browser URL

2. **`tf/browser/start.py`**
   - Updated to use `HOST_DISPLAY` for browser URL
   - Server still binds to `0.0.0.0` for remote access

## How It Works

- **Server Binding**: Flask server binds to `0.0.0.0` (all network interfaces)
- **Local Browser**: Opens `http://localhost:PORT` on the server
- **Remote Access**: Access via `http://TAILSCALE_IP:PORT` from other devices

## Usage

### On Fedora Server (atlas)

1. **Start Text-Fabric**:
   ```bash
   tf etcbc/bhsa
   ```

2. **Note the port number** from the output (e.g., `14897`)

3. **Get your Tailscale IP**:
   ```bash
   tailscale ip -4
   ```
   Example output: `100.x.x.x`

### On Your Mac

1. **Ensure Tailscale is running** and connected to the same network

2. **Open browser** and navigate to:
   ```
   http://TAILSCALE_IP:PORT
   ```
   
   Example:
   ```
   http://100.64.1.2:14897
   ```

3. **Bookmark it** for easy access!

### On Your iPhone

Same as Mac - just open Safari and go to the Tailscale IP:PORT URL.

## Port Numbers

Text-Fabric assigns ports based on the corpus:
- **BHSA**: Typically port `14897`
- Other corpora will use different ports

The port is deterministic - same corpus = same port each time.

## Troubleshooting

### Can't Connect from Mac

1. **Check Tailscale is running on both devices**:
   ```bash
   # On Fedora
   tailscale status
   
   # On Mac
   tailscale status
   ```

2. **Verify the server is running**:
   ```bash
   # On Fedora
   ss -tlnp | grep LISTEN | grep <PORT>
   ```
   Should show: `0.0.0.0:<PORT>`

3. **Check firewall** (shouldn't be needed with Tailscale, but just in case):
   ```bash
   # On Fedora
   sudo firewall-cmd --list-all
   ```

4. **Test with curl**:
   ```bash
   # On Mac
   curl http://TAILSCALE_IP:PORT
   ```

### Wrong Port

If you're not sure what port Text-Fabric is using:

```bash
# On Fedora, while TF is running
ss -tlnp | grep python
```

Look for the line with `0.0.0.0:XXXXX` - that's your port.

### Server Starts But Can't Access

Make sure you're using the **Tailscale IP**, not the local network IP:

```bash
# Get Tailscale IP (on Fedora)
tailscale ip -4
```

This will be something like `100.x.x.x`, NOT `192.168.x.x`.

## Security Notes

### Why This Is Safe

1. **Tailscale Encryption**: All traffic is encrypted via WireGuard
2. **Private Network**: Only devices on your Tailscale network can access
3. **No Firewall Changes**: Tailscale handles networking securely
4. **No Public Exposure**: Server is NOT accessible from the internet

### What's Accessible

- Anyone on your Tailscale network can access the browser
- This includes all devices you've authorized via Tailscale
- No authentication is required (it's a local tool)

### If You Want Authentication

If you want to add authentication later, you could:
1. Use Tailscale ACLs to restrict access
2. Add HTTP basic auth to Flask
3. Use a reverse proxy (nginx) with auth

But for personal use on Tailscale, the current setup is secure.

## Making It Persistent (Optional)

### Option 1: Run in tmux/screen

```bash
# On Fedora
tmux new -s textfabric
tf etcbc/bhsa
# Press Ctrl+B, then D to detach

# Reattach later
tmux attach -t textfabric
```

### Option 2: Systemd Service (Recommended)

Create `/etc/systemd/system/textfabric.service`:

```ini
[Unit]
Description=Text-Fabric BHSA Browser
After=network.target

[Service]
Type=simple
User=teapot
WorkingDirectory=/home/teapot
Environment="PATH=/home/teapot/textfabric-env/bin:/usr/bin"
ExecStart=/home/teapot/textfabric-env/bin/tf etcbc/bhsa -noweb
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable textfabric.service
sudo systemctl start textfabric.service

# Check status
sudo systemctl status textfabric.service

# View logs
sudo journalctl -u textfabric.service -f
```

**Note**: The `-noweb` flag prevents opening a browser on the server.

## Testing

### Quick Test

1. **On Fedora**:
   ```bash
   tf etcbc/bhsa
   ```

2. **On Mac**, open browser to:
   ```
   http://TAILSCALE_IP:14897
   ```

3. **Try a query**:
   - Go to Search pad
   - Enter: `word sp=verb`
   - Click "Go"
   - Should see results!

4. **Test English translations**:
   - Go to Options tab
   - Check "English translation"
   - Expand a result
   - Should see Hebrew with English in parentheses

## Accessing from Multiple Devices

You can access the same Text-Fabric instance from:
- ? Your Mac
- ? Your iPhone
- ? Your iPad
- ? Any other device on your Tailscale network

All simultaneously! They all connect to the same server instance.

## Performance Tips

### On Mac/iPhone

- **Bookmark the URL** for quick access
- **Add to Home Screen** (iPhone): Share ? Add to Home Screen
- **Use Safari** for best compatibility

### On Fedora Server

- **Use SSD storage** for BHSA data (faster queries)
- **Allocate enough RAM** (2GB+ recommended)
- **Keep server running** (use systemd service)

## Next Steps

1. **Test the connection** from your Mac
2. **Set up systemd service** for persistent access
3. **Add bookmark** on your devices
4. **Try the English translation feature**!

---

**Created**: 2025-11-15
**Status**: ? Ready to use
