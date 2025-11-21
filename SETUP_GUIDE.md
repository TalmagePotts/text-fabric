# Setup Guide - Text-Fabric BHSA Research Assistant

This guide explains how to set up the Text-Fabric BHSA Research Assistant from scratch after cloning the repository.

## What's Included in the Repository

✅ **Core Text-Fabric code** - The main Text-Fabric framework  
✅ **AI Query Generation** - Natural language to Text-Fabric query conversion (using Google Gemini)  
✅ **Lexeme Database** - `bhsa_lexemes.csv` with 8000+ Hebrew lexemes  
✅ **English Translation Integration** - Code for displaying English translations  
✅ **Remote Access Support** - Modified to bind to `0.0.0.0` for remote access  
✅ **Browser UI** - Web interface with AI query generation  

## What's NOT Included (You Need to Add)

❌ **BHSA Corpus Data** - Must be downloaded separately (large dataset)  
❌ **API Keys** - Google Gemini API key (free tier available)  
❌ **English Translation Data** - Optional CSV files for English translations  
❌ **Python Virtual Environment** - Must be created  
❌ **Systemd Service File** - Optional, for persistent hosting  

## Prerequisites

- **Python 3.9+** (Python 3.13 recommended)
- **pip** (Python package manager)
- **Internet connection** (for downloading BHSA corpus and API calls)
- **~2GB free disk space** (for BHSA corpus data)

## Step-by-Step Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/annotation/text-fabric.git
cd text-fabric
```

### Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv textfabric-env

# Activate it (Linux/Mac)
source textfabric-env/bin/activate

# Or on Windows
# textfabric-env\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Install Text-Fabric and core dependencies
pip install -e .

# Install AI dependencies (for query generation)
pip install google-generativeai>=0.3.0 pandas>=1.3.0
```

**Note**: The repository uses `setup.cfg` for dependencies. Core dependencies (Flask, requests, etc.) are included automatically.

### Step 4: Download BHSA Corpus Data

The BHSA (Biblia Hebraica Stuttgartensia Amstelodamensis) corpus must be downloaded. Text-Fabric will do this automatically on first use:

```bash
# Start Text-Fabric (it will download BHSA automatically)
tf etcbc/bhsa
```

**First run will:**
- Download ~1.5GB of BHSA corpus data
- Store it in `~/text-fabric-data/` (or `~/github/etcbc/bhsa/tf/`)
- Take 5-10 minutes depending on internet speed

**Alternative manual download:**
```python
from tf.app import use
A = use('etcbc/bhsa', checkout='clone', silent=False)
```

### Step 5: Get Google Gemini API Key (for AI Query Generation)

1. **Go to**: https://makersuite.google.com/app/apikey
2. **Sign in** with your Google account
3. **Create API key** (free tier available)
4. **Copy the key** (starts with `AIza...`)

**Store the key** (choose one method):

**Option A: Environment Variable (Recommended for servers)**
```bash
# Add to ~/.bashrc or ~/.zshrc
export GEMINI_API_KEY="your-api-key-here"

# Reload shell
source ~/.bashrc
```

**Option B: Browser Storage (Recommended for local use)**
- The browser UI will save it automatically in localStorage
- No setup needed, just enter it in the UI

### Step 6: (Optional) Download English Translation Data

If you want English translations displayed alongside Hebrew text:

1. **Download the translation CSV**:
   - Place `BHSA-with-interlinear-translation.csv` in `English-lineup/` directory
   - Place `bhsa_ohb_offsets.json` in `English-lineup/` directory

2. **Or set environment variables**:
```bash
export TF_ENGLISH_CSV="/path/to/BHSA-with-interlinear-translation.csv"
export TF_ENGLISH_OFFSET="/path/to/bhsa_ohb_offsets.json"
```

**Note**: These files are large (~100MB) and not included in the repository. They're optional - the system works without them.

### Step 7: Start Text-Fabric Browser

```bash
# Make sure virtual environment is activated
source textfabric-env/bin/activate

# Start the browser
tf etcbc/bhsa
```

**Expected output:**
```
This is Text-Fabric 13.0.17
Setting up TF browser for etcbc/bhsa ...
Loading TF corpus data. Please wait ...
✓ Corpus loaded successfully
Starting browser at http://localhost:14897
```

**Note the port number** (e.g., `14897`) - you'll need it for remote access.

### Step 8: Access the Browser

**Local access:**
- Open browser to: `http://localhost:14897`

**Remote access (if on server):**
- The server binds to `0.0.0.0` by default
- Access via: `http://YOUR_SERVER_IP:14897`
- For Tailscale: `http://TAILSCALE_IP:14897`

## Verification

### Test 1: Basic Text-Fabric Query

1. Go to **Search** tab
2. Enter query: `word sp=verb`
3. Click **Search**
4. Should return thousands of verb results

### Test 2: AI Query Generation

1. Go to **AI Query** tab (or look for AI query box)
2. Enter: "Find all plural verbs in Genesis"
3. Enter your Gemini API key (if not in environment)
4. Click **Generate Query**
5. Should generate a valid Text-Fabric query

### Test 3: English Translations (if data installed)

1. Go to **Options** tab
2. Check **"English translation"** checkbox
3. Run any query
4. Expand results - should see English text in gray italics

## Troubleshooting

### Issue: "No TF dataset specified"

**Solution**: Make sure you specify the corpus:
```bash
tf etcbc/bhsa
```

### Issue: "Corpus not found" or download fails

**Solution**: 
- Check internet connection
- Try manual download:
```python
from tf.app import use
A = use('etcbc/bhsa', checkout='clone')
```

### Issue: "API key is required" (AI queries)

**Solution**:
- Set `GEMINI_API_KEY` environment variable, OR
- Enter API key in the browser UI (it will save to localStorage)

### Issue: Can't access from remote machine

**Solution**:
- Check that server binds to `0.0.0.0` (check `tf/parameters.py` - should have `HOST = "0.0.0.0"`)
- Check firewall: `sudo firewall-cmd --list-all`
- For Tailscale: Ensure both devices are connected: `tailscale status`

### Issue: "Lexeme database not found"

**Solution**: 
- Ensure `bhsa_lexemes.csv` is in the repository root
- Check path: `ls bhsa_lexemes.csv`

### Issue: English translations not showing

**Solution**:
- Check that translation CSV files exist in `English-lineup/`
- Or set `TF_ENGLISH_CSV` and `TF_ENGLISH_OFFSET` environment variables
- Check Options tab - "English translation" must be checked

## Optional: Persistent Hosting with Systemd

For 24/7 operation on a Linux server:

### Create Systemd Service File

```bash
sudo nano /etc/systemd/system/textfabric.service
```

**Content:**
```ini
[Unit]
Description=Text-Fabric BHSA Browser
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/text-fabric
Environment="PATH=/path/to/text-fabric/textfabric-env/bin"
Environment="GEMINI_API_KEY=your-api-key-here"
ExecStart=/path/to/text-fabric/textfabric-env/bin/tf etcbc/bhsa --noweb
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Replace:**
- `your-username` - Your Linux username
- `/path/to/text-fabric` - Full path to repository
- `your-api-key-here` - Your Gemini API key (or remove if using browser storage)

### Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable textfabric.service

# Start service
sudo systemctl start textfabric.service

# Check status
sudo systemctl status textfabric.service
```

### View Logs

```bash
# View recent logs
sudo journalctl -u textfabric.service -n 50

# Follow logs
sudo journalctl -u textfabric.service -f
```

## File Structure After Setup

```
text-fabric/
├── bhsa_lexemes.csv          ✅ Included
├── tf/                       ✅ Included (core code)
├── textfabric-env/           ✅ Created (virtual environment)
├── English-lineup/           ⚠️ Optional (add translation files)
│   ├── BHSA-with-interlinear-translation.csv
│   └── bhsa_ohb_offsets.json
└── ~/text-fabric-data/       ✅ Created (BHSA corpus, auto-downloaded)
    └── etcbc/
        └── bhsa/
            └── tf/
```

## Environment Variables Summary

| Variable | Purpose | Required | Default |
|----------|---------|----------|---------|
| `GEMINI_API_KEY` | Google Gemini API for AI queries | Yes (for AI) | None |
| `TF_ENGLISH_CSV` | Path to English translation CSV | No | `English-lineup/BHSA-with-interlinear-translation.csv` |
| `TF_ENGLISH_OFFSET` | Path to offset JSON file | No | `English-lineup/bhsa_ohb_offsets.json` |

## Quick Start Checklist

- [ ] Clone repository
- [ ] Create virtual environment
- [ ] Install dependencies (`pip install -e .` and AI packages)
- [ ] Download BHSA corpus (`tf etcbc/bhsa` - first run)
- [ ] Get Gemini API key
- [ ] Set `GEMINI_API_KEY` or enter in browser
- [ ] (Optional) Add English translation files
- [ ] Start browser: `tf etcbc/bhsa`
- [ ] Test basic query
- [ ] Test AI query generation
- [ ] (Optional) Set up systemd service for persistence

## Next Steps

1. **Read the documentation**:
   - `CLAUDE.md` - Project overview and architecture
   - `ENGLISH_TRANSLATION_README.md` - English translation details
   - `REMOTE_ACCESS_SETUP.md` - Remote access configuration

2. **Try example queries**:
   - Simple: `word sp=verb`
   - Complex: `clause phrase function=Pred word sp=verb`
   - AI: "Find all instances where JHWH appears with a verb"

3. **Customize**:
   - Modify `tf/parameters.py` for different ports
   - Add custom lexemes to `bhsa_lexemes.csv`
   - Extend AI prompts in `tf/browser/ai_query.py`

## Support

- **Text-Fabric Docs**: https://annotation.github.io/text-fabric/tf
- **BHSA Features**: https://etcbc.github.io/bhsa/features/
- **Issues**: GitHub Issues (if repository is public)

---

**Last Updated**: 2025-01-XX  
**Tested On**: Python 3.13, Fedora Linux, Arch Linux
