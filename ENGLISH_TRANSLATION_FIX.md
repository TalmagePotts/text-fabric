# English Translation Alignment Fix

## Issue

The English translations were appearing in the browser, but they didn't match the Hebrew words correctly. For example, the first word of Genesis 1:1 (???, "in") was showing "BSB" instead of "In".

## Root Cause

The CSV file `BHSA-with-interlinear-translation.csv` has a header row:
```
BHSsort	BHSA	ETCBCgloss	?BSBsort?BSB?
```

The original `kjv_align.py` loads all lines into memory including the header:
```python
self.ohb_lines = f.readlines()  # Index 0 = header, Index 1 = first data row
```

When accessing by `csv_idx`, it correctly gets the data because:
- `csv_idx = 1` ? `self.ohb_lines[1]` ? second line (first data row)

My implementation was reading line-by-line with:
```python
for i, line in enumerate(f, 1):  # Started counting from 1
    if i == line_num:
```

This caused:
- `line_num = 1` ? first line of file ? **header row** ?

## Fix

Changed the enumeration to start from 0:
```python
for i, line in enumerate(f):  # Start from 0
    if i == line_num:
```

Now:
- `line_num = 1` ? line at index 1 ? second line (first data row) ?

## Verification

```bash
$ python3 -c "from tf.advanced.english import get_english_provider; p = get_english_provider(); print(p.get_translation(1)['english'])"
In

$ python3 -c "from tf.advanced.english import get_english_provider; p = get_english_provider(); print(p.get_translation(3)['english'])"
created
```

Genesis 1:1 first words:
1. ??? ? "In"
2. ????????? ? "the beginning"
3. ??????? ? "created"
4. ????????? ? "God"

? Correct!

## Testing

After restarting the Text-Fabric browser, the English translations should now correctly align with the Hebrew words.

**To test**:
1. Restart the browser (Ctrl+C and restart)
2. Enable "English translation" in Options
3. Run query: `word sp=verb`
4. Expand first result (Genesis 1:1)
5. Should see: ??????? (created)

---

**Fixed**: 2025-11-15
**File Modified**: `tf/advanced/english.py` (line 121)
