# AI Prompt Template Comparison & Recommendation

## Token Usage Analysis

### Current Template (Original)
- **File:** `ai_prompt_template.md`
- **Size:** ~130 lines, ~800 words
- **Estimated tokens:** ~1,000 tokens
- **Coverage:** Basic syntax, 12 examples, minimal documentation

### Enhanced Template v2 (Comprehensive)
- **File:** `ai_prompt_template_v2.md`
- **Size:** ~700 lines, ~4,500 words
- **Estimated tokens:** ~6,000 tokens
- **Coverage:** Complete syntax, 45 examples, all operators, quantifiers, anti-patterns

### Production Template (Optimized)
- **File:** `ai_prompt_template_production.md`
- **Size:** ~200 lines, ~1,800 words
- **Estimated tokens:** ~2,400 tokens
- **Coverage:** All critical syntax, 20 examples, quantifiers, essential operators

---

## Gemini 2.5 Pro Free Tier Limits

**Rate Limits:**
- 2 requests per minute (RPM)
- 1,000,000 tokens per minute (TPM) - very generous
- 1,500 requests per day (RPD)

**Token Costs (if you go paid):**
- Input: $1.25 per 1M tokens
- Output: $5.00 per 1M tokens

**Analysis:**
- All three templates are well within the 1M TPM limit
- The bottleneck is the 2 RPM limit, not token count
- For free tier, token count doesn't matter much
- For paid tier, production template saves ~60% on input costs

---

## Performance Comparison

### Response Time
| Template | Tokens | Est. Response Time |
|----------|--------|-------------------|
| Original | ~1,000 | ~1-2 seconds |
| Production | ~2,400 | ~2-3 seconds |
| v2 (Full) | ~6,000 | ~3-5 seconds |

### Accuracy (Estimated)
| Template | Quantifiers | Operators | Lexemes | Anti-patterns |
|----------|-------------|-----------|---------|---------------|
| Original | ❌ None | ⚠️ Basic | ✅ Yes | ⚠️ 5 |
| Production | ✅ All 3 | ✅ Complete | ✅ Yes | ✅ 7 |
| v2 (Full) | ✅ All 3 | ✅ Complete | ✅ Yes | ✅ 22 |

---

## Recommendation

### **Use Production Template** (`ai_prompt_template_production.md`)

**Why:**
1. ✅ **Includes all critical features:**
   - Complete quantifier syntax (`/without/`, `/where/`+`/have/`, `/with/`+`/or/`)
   - All essential relational operators
   - ETCBC transcription guide
   - Anti-patterns and validation

2. ✅ **Optimized for performance:**
   - 60% smaller than v2 (2,400 vs 6,000 tokens)
   - Faster response times (2-3s vs 3-5s)
   - Lower costs if you go paid (~$0.003 vs ~$0.0075 per query)

3. ✅ **Still comprehensive:**
   - 20 examples (vs 45 in v2, 12 in original)
   - All quantifier types covered
   - Complete operator reference
   - BHSA feature knowledge

4. ✅ **Free tier friendly:**
   - Well within limits
   - Faster = better user experience
   - Room for lexeme database context

### When to Use Each Template

**Original (`ai_prompt_template.md`):**
- ❌ Don't use - missing quantifiers
- Keep for reference only

**Production (`ai_prompt_template_production.md`):**
- ✅ **RECOMMENDED** for production use
- Best balance of completeness and efficiency
- Ideal for free tier
- Fast response times

**v2 Full (`ai_prompt_template_v2.md`):**
- 📚 Use as reference documentation
- Use for training/debugging
- Use if accuracy issues arise with production template
- Overkill for most queries

---

## Token Budget Breakdown

**Typical query generation:**
```
System prompt (production):  ~2,400 tokens
Lexeme database context:     ~200-500 tokens
User prompt:                 ~50-100 tokens
-------------------------------------------
Total input:                 ~2,650-3,000 tokens
AI response:                 ~100-300 tokens
-------------------------------------------
Total per query:             ~2,750-3,300 tokens
```

**With v2 full template:**
```
System prompt (v2):          ~6,000 tokens
Lexeme database context:     ~200-500 tokens
User prompt:                 ~50-100 tokens
-------------------------------------------
Total input:                 ~6,250-6,600 tokens
AI response:                 ~100-300 tokens
-------------------------------------------
Total per query:             ~6,350-6,900 tokens
```

**Cost comparison (if paid):**
- Production: ~$0.003 per query
- v2 Full: ~$0.008 per query
- **Savings: 62%** with production template

---

## Implementation

**Recommended change in `ai_query.py`:**

```python
def build_system_prompt() -> str:
    """Build the system prompt from production template."""
    template_path = Path(__file__).parent / "ai_prompt_template_production.md"
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    return template
```

**Alternative (if accuracy issues):**
```python
# Use full v2 template for maximum accuracy
template_path = Path(__file__).parent / "ai_prompt_template_v2.md"
```

---

## Summary

| Metric | Original | Production ✅ | v2 Full |
|--------|----------|--------------|---------|
| **Tokens** | ~1,000 | ~2,400 | ~6,000 |
| **Examples** | 12 | 20 | 45 |
| **Quantifiers** | ❌ | ✅ | ✅ |
| **Operators** | Basic | Complete | Complete |
| **Response Time** | Fast | Medium | Slower |
| **Accuracy** | Low | High | Highest |
| **Cost (paid)** | $0.001 | $0.003 | $0.008 |
| **Recommendation** | ❌ Retire | ✅ **USE THIS** | 📚 Reference |

**Bottom line:** Use the **production template** for the best balance of accuracy, performance, and cost-efficiency.
