# MM Number Extraction for Claude & Power Automate

This repository contains resources for extracting MM (Material Master) numbers from email content using Claude AI and Power Automate.

## Overview

MM numbers are 7-digit material identifiers commonly found in procurement/supply chain emails. This solution provides:

1. **Claude System Prompt** - Conditions Claude to accurately extract MM numbers while ignoring distractors
2. **Regex Patterns** - Power Automate-compatible regular expressions
3. **Test Samples** - 20 realistic email samples for validation
4. **Python Validator** - Script to test regex patterns

## Quick Start

### Using the Claude System Prompt

See `claude_system_prompt.md` for the complete system prompt. Key points:
- Copy the prompt into your Claude API call as the `system` parameter
- Claude will return only the 7-digit MM number or "NO_MM_FOUND"

### Using Regex in Power Automate

Primary pattern:
```regex
(?i)\bmm[\s:#-]?\s*(\d{7})\b
```

Power Automate expression:
```
first(match(triggerOutputs()?['body/body'], '(?i)mm[\s:#-]?\s*(\d{7})'))
```

See `power_automate_regex.md` for detailed setup instructions.

## Supported MM Formats

The solution handles these MM number variations:
- `mm 1234567` (space separator)
- `MM1234567` (no separator)
- `mm#1234567` (hash separator)
- `MM: 1234567` (colon with space)
- `mm-1234567` (hyphen separator)
- `mm:1234567` (colon, no space)

## Distractors (Correctly Ignored)

- PO numbers (e.g., 4900123445)
- Dates (e.g., 01/15/2026)
- Phone numbers (e.g., 555-123-4567)
- Quantities (e.g., "2 units")
- Tracking numbers

## Running Tests

```bash
# Run all tests
python3 mm_extractor.py

# Run demo extraction
python3 mm_extractor.py --demo
```

Expected output:
```
Positive Tests: 20/20 passed
Negative Tests: 3/3 passed
Overall: 23/23 (100.0%)
```

## Files

| File | Description |
|------|-------------|
| `claude_system_prompt.md` | Complete Claude system prompt with examples |
| `power_automate_regex.md` | Regex patterns and Power Automate expressions |
| `test_samples.json` | 20 email samples + 3 negative test cases |
| `mm_extractor.py` | Python validation script |

## Integration Tips

1. **Combine subject and body** - MM numbers may appear in either
2. **Handle NO_MM_FOUND** - Include fallback logic in your flow
3. **Log extractions** - Track which emails successfully extracted MM numbers
4. **Test with real data** - Validate against your actual email formats
