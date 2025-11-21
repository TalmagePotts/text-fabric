# Quick Start - Text-Fabric BHSA

## What You Need

1. **Python 3.9+** (3.13 recommended)
2. **Google Gemini API Key** (free): https://aistudio.google.com/
3. **~2GB disk space** (for BHSA corpus)

## Setup (5 minutes)

```bash
# 1. Clone and enter
git clone https://github.com/annotation/text-fabric.git
cd text-fabric

# 2. Create virtual environment
python3 -m venv textfabric-venv

# 3. Activate and install dependencies
source textfabric-venv/bin/activate
pip install -e .
pip install google-generativeai>=0.3.0 pandas>=1.3.0
deactivate

# 4. Run Text-Fabric (downloads BHSA corpus on first run, takes 5-10 min)
textfabric-venv/bin/tf ETCBC/bhsa
```

## Run (After Setup)

```bash
# From the text-fabric directory
textfabric-venv/bin/tf ETCBC/bhsa
```

Open: `http://localhost:14897`

## What's Missing from Repo

- ❌ BHSA corpus data (auto-downloads on first `tf etcbc/bhsa`)
- ❌ API keys (get free Gemini key)
- ❌ English translation CSV (optional)

## Test

1. **Search tab**: Query `word sp=verb` → Should work
2. **AI Query tab**: "Find verbs in Genesis" → Needs API key
3. **Options tab**: Check "English translation" → Needs CSV files (optional)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No dataset" | Run `textfabric-venv/bin/tf ETCBC/bhsa` (not just `tf`) |
| "API key required" | Get free key at https://aistudio.google.com/ and enter in browser |
| Can't access remotely | Already binds to `0.0.0.0` - check firewall |
| Corpus download fails | Check internet, try manual: `textfabric-venv/bin/python -c "from tf.app import use; use('etcbc/bhsa', checkout='clone')"` |
| Missing pandas/google-generativeai | Activate venv and run: `source textfabric-venv/bin/activate && pip install pandas google-generativeai && deactivate` |

## Full Guide

See `SETUP_GUIDE.md` for detailed instructions.
