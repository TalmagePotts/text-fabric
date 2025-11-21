# Quick Start - Text-Fabric BHSA

## What You Need

1. **Python 3.9+** (3.13 recommended)
2. **Google Gemini API Key** (free): https://makersuite.google.com/app/apikey
3. **~2GB disk space** (for BHSA corpus)

## Setup (5 minutes)

```bash
# 1. Clone and enter
git clone https://github.com/annotation/text-fabric.git
cd text-fabric

# 2. Create virtual environment
python3 -m venv textfabric-env
source textfabric-env/bin/activate

# 3. Install
pip install -e .
pip install google-generativeai>=0.3.0 pandas>=1.3.0

# 4. Download BHSA corpus (first run, takes 5-10 min)
tf etcbc/bhsa

# 5. Set API key (optional - can enter in browser instead)
export GEMINI_API_KEY="your-key-here"
```

## Run

```bash
source textfabric-env/bin/activate
tf etcbc/bhsa
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
| "No dataset" | Run `tf etcbc/bhsa` (not just `tf`) |
| "API key required" | Set `GEMINI_API_KEY` or enter in browser |
| Can't access remotely | Already binds to `0.0.0.0` - check firewall |
| Corpus download fails | Check internet, try manual: `python -c "from tf.app import use; use('etcbc/bhsa', checkout='clone')"` |

## Full Guide

See `SETUP_GUIDE.md` for detailed instructions.
