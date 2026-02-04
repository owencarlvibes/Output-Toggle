# MM Number Extraction for Power Automate

Complete Power Automate solution for extracting MM (Material Master) numbers from emails.

## Quick Start - Copy This Expression

**Single expression that extracts MM number or returns "NO_MM_FOUND":**

```
if(empty(match(concat(triggerOutputs()?['body/subject'], ' ', triggerOutputs()?['body/body']), '(?i)mm[\s:#-]?\s*(\d{7})')), 'NO_MM_FOUND', last(first(match(concat(triggerOutputs()?['body/subject'], ' ', triggerOutputs()?['body/body']), '(?i)mm[\s:#-]?\s*(\d{7})'))))
```

## Regex Pattern

```
(?i)mm[\s:#-]?\s*(\d{7})
```

## Supported MM Formats

| Format | Example |
|--------|---------|
| Space separator | `mm 1234567` |
| No separator | `MM1234567` |
| Hash separator | `mm#1234567` |
| Colon with space | `MM: 1234567` |
| Hyphen separator | `mm-1234567` |
| Colon no space | `mm:1234567` |

## Correctly Ignored (Distractors)

- PO numbers (4900123445)
- Dates (01/15/2026)
- Phone numbers (555-123-4567)
- Quantities (2 units)
- Tracking numbers

## Power Automate Flow Setup

### Option 1: Import Flow
Import `power_automate_flow.json` directly into your tenant.

### Option 2: Build Manually
See `power_automate_expressions.md` for step-by-step instructions.

## Key Expressions

### Extract match from email body:
```
match(triggerOutputs()?['body/body'], '(?i)mm[\s:#-]?\s*(\d{7})')
```

### Get just the 7-digit number:
```
last(first(match(triggerOutputs()?['body/body'], '(?i)mm[\s:#-]?\s*(\d{7})')))
```

### Check if MM was found:
```
not(empty(match(triggerOutputs()?['body/body'], '(?i)mm[\s:#-]?\s*(\d{7})')))
```

## Files

| File | Description |
|------|-------------|
| `power_automate_flow.json` | Importable flow definition |
| `power_automate_expressions.md` | All expressions with setup guide |
| `test_samples.json` | 20 test emails + 3 negative cases |
| `claude_system_prompt.md` | Optional: Claude AI prompt for extraction |
| `mm_extractor.py` | Optional: Python validation script |

## Testing

All 20 sample emails correctly extract `1234567` while ignoring PO numbers, dates, and other distractors.
