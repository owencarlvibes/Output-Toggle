# Power Automate Regex Patterns for MM Number Extraction

This document provides regex patterns and Power Automate expressions for extracting MM numbers from email content.

---

## Primary Regex Pattern

```regex
(?i)\bmm[\s:#-]?\s*(\d{7})\b
```

### Pattern Breakdown:
- `(?i)` - Case-insensitive flag (works in most regex engines)
- `\b` - Word boundary (prevents matching inside longer words)
- `mm` - Literal "mm" text
- `[\s:#-]?` - Optional separator: space, colon, hash, or hyphen
- `\s*` - Zero or more additional spaces (for cases like "MM: 1234567")
- `(\d{7})` - Capture group: exactly 7 digits (the MM number)
- `\b` - Word boundary at the end

---

## Alternative Patterns (if primary doesn't work)

### Pattern A - Without case-insensitive flag:
```regex
\b[Mm][Mm][\s:#-]?\s*(\d{7})\b
```

### Pattern B - Explicit alternatives:
```regex
\b(?:mm|MM|Mm|mM)[\s:#-]?\s*(\d{7})\b
```

### Pattern C - Including "material" keyword:
```regex
\b(?:material\s+)?[Mm]{2}[\s:#-]?\s*(\d{7})\b
```

---

## Power Automate Expressions

### Using `match()` function:

```
match(triggerOutputs()?['body/body'], '(?i)mm[\s:#-]?\s*(\d{7})')
```

### Using `first()` with `match()`:

```
first(match(triggerOutputs()?['body/body'], '(?i)mm[\s:#-]?\s*(\d{7})'))
```

### Extract just the 7-digit number (group 1):

```
if(
  empty(match(body('Get_email'), '(?i)\bmm[\s:#-]?\s*(\d{7})\b')),
  'NO_MM_FOUND',
  last(first(match(body('Get_email'), '(?i)\bmm[\s:#-]?\s*(\d{7})\b')))
)
```

---

## Power Automate Flow Setup

### Step 1: Trigger
- Use "When a new email arrives" trigger

### Step 2: Initialize Variable
```
Name: MMNumber
Type: String
Value: (leave empty)
```

### Step 3: Compose - Extract MM Number
```
Expression:
first(match(triggerOutputs()?['body/body'], '(?i)mm[\s:#-]?\s*(\d{7})'))
```

### Step 4: Condition - Check if MM Found
```
Condition: empty(outputs('Compose_Extract_MM'))
If Yes: Set MMNumber to "NO_MM_FOUND"
If No: Set MMNumber to outputs('Compose_Extract_MM')[1]
```

---

## Full Expression for Direct Use

This single expression handles extraction and returns the MM number or "NO_MM_FOUND":

```
if(
  empty(match(concat(triggerOutputs()?['body/subject'], ' ', triggerOutputs()?['body/body']), '(?i)\bmm[\s:#-]?\s*(\d{7})\b')),
  'NO_MM_FOUND',
  last(first(match(concat(triggerOutputs()?['body/subject'], ' ', triggerOutputs()?['body/body']), '(?i)\bmm[\s:#-]?\s*(\d{7})\b')))
)
```

---

## Validation Test Cases

| Input | Expected Match | Extracted Number |
|-------|----------------|------------------|
| mm 1234567 | Yes | 1234567 |
| MM1234567 | Yes | 1234567 |
| mm#1234567 | Yes | 1234567 |
| MM: 1234567 | Yes | 1234567 |
| mm-1234567 | Yes | 1234567 |
| mm:1234567 | Yes | 1234567 |
| material mm 1234567 | Yes | 1234567 |
| PO 4900123445 | No | - |
| 01/15/2026 | No | - |
| ordered 2 units | No | - |

---

## Notes

1. **Power Automate Regex Limitations**: Power Automate uses .NET regex engine. The `(?i)` flag should work, but if not, use Pattern A or B.

2. **Multiple MM Numbers**: The `match()` function returns the first match. To get all matches, use the `matchAll()` function (available in some Power Automate versions).

3. **Performance**: Place the regex extraction early in your flow and use the result in subsequent conditions to avoid repeated processing.
