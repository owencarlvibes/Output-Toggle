# Power Automate Expressions for MM Number Extraction

Complete copy-paste expressions for your Power Automate flow.

---

## Quick Reference - Copy These Expressions

### 1. Primary Regex Pattern
```
(?i)mm[\s:#-]?\s*(\d{7})
```

### 2. Extract MM Number (Single Expression)
```
if(
  empty(match(concat(triggerOutputs()?['body/subject'], ' ', triggerOutputs()?['body/body']), '(?i)mm[\s:#-]?\s*(\d{7})')),
  'NO_MM_FOUND',
  last(first(match(concat(triggerOutputs()?['body/subject'], ' ', triggerOutputs()?['body/body']), '(?i)mm[\s:#-]?\s*(\d{7})')))
)
```

### 3. Just Get the Match (Compose Action)
```
match(triggerOutputs()?['body/body'], '(?i)mm[\s:#-]?\s*(\d{7})')
```

### 4. Get First Match Only
```
first(match(triggerOutputs()?['body/body'], '(?i)mm[\s:#-]?\s*(\d{7})'))
```

### 5. Extract 7-Digit Number from Match
```
last(first(match(triggerOutputs()?['body/body'], '(?i)mm[\s:#-]?\s*(\d{7})')))
```

---

## Step-by-Step Flow Setup

### Step 1: Trigger
- Add trigger: **When a new email arrives (V3)** (Office 365 Outlook)
- Configure folder: Inbox (or specific folder)

### Step 2: Initialize Variable - EmailContent
- Action: **Initialize variable**
- Name: `EmailContent`
- Type: String
- Value:
```
@{concat(triggerOutputs()?['body/subject'], ' ', triggerOutputs()?['body/body'])}
```

### Step 3: Initialize Variable - MMNumber
- Action: **Initialize variable**
- Name: `MMNumber`
- Type: String
- Value: (leave empty)

### Step 4: Compose - Extract Match
- Action: **Compose**
- Inputs:
```
@match(variables('EmailContent'), '(?i)mm[\s:#-]?\s*(\d{7})')
```

### Step 5: Condition - Check If Found
- Action: **Condition**
- Expression:
```
@not(empty(outputs('Compose')))
```

**If Yes (MM found):**
- Set variable `MMNumber` to:
```
@{last(first(outputs('Compose')))}
```

**If No (MM not found):**
- Set variable `MMNumber` to: `NO_MM_FOUND`

### Step 6: Use the Result
- Variable `MMNumber` now contains:
  - The 7-digit MM number (e.g., `1234567`), OR
  - `NO_MM_FOUND` if no MM number was detected

---

## Alternative Expressions

### For Outlook Connector (body content)
```
match(body('Get_email')?['body'], '(?i)mm[\s:#-]?\s*(\d{7})')
```

### For shared mailbox
```
match(body('Get_email_(V2)')?['body'], '(?i)mm[\s:#-]?\s*(\d{7})')
```

### For HTTP webhook trigger
```
match(triggerBody()?['content'], '(?i)mm[\s:#-]?\s*(\d{7})')
```

### From form/manual input
```
match(triggerBody()['text'], '(?i)mm[\s:#-]?\s*(\d{7})')
```

---

## Handling Multiple MM Numbers

If an email might contain multiple MM numbers:

### Get All Matches
```
match(variables('EmailContent'), '(?i)mm[\s:#-]?\s*(\d{7})')
```
This returns an array of all matches.

### Count Matches
```
length(match(variables('EmailContent'), '(?i)mm[\s:#-]?\s*(\d{7})'))
```

### Loop Through All
Use **Apply to each** on the match output to process each MM number.

---

## Validation Condition Expressions

### Check if valid MM number was found
```
@and(not(empty(variables('MMNumber'))), not(equals(variables('MMNumber'), 'NO_MM_FOUND')))
```

### Check if MM number is exactly 7 digits
```
@equals(length(variables('MMNumber')), 7)
```

### Combined validation
```
@and(
  not(equals(variables('MMNumber'), 'NO_MM_FOUND')),
  equals(length(variables('MMNumber')), 7)
)
```

---

## Common Issues & Solutions

### Issue: Expression returns null
**Solution:** Check that the trigger output path is correct. Use dynamic content picker to verify the exact path.

### Issue: Match returns full pattern instead of just digits
**Solution:** Use `last(first(...))` to get capture group 1 (the 7 digits only).

### Issue: Case sensitivity
**Solution:** The `(?i)` flag makes it case-insensitive. If your tenant doesn't support this, use:
```
match(toLower(variables('EmailContent')), 'mm[\s:#-]?\s*(\d{7})')
```

### Issue: HTML in email body
**Solution:** Strip HTML first:
```
match(
  replace(replace(triggerOutputs()?['body/body'], '<[^>]*>', ''), '&nbsp;', ' '),
  '(?i)mm[\s:#-]?\s*(\d{7})'
)
```

---

## Test Your Expression

Before deploying, test with these sample inputs:

| Input | Expected Output |
|-------|-----------------|
| `mm 1234567` | `1234567` |
| `MM1234567` | `1234567` |
| `mm#1234567` | `1234567` |
| `MM: 1234567` | `1234567` |
| `mm-1234567` | `1234567` |
| `PO 4900123445` | `NO_MM_FOUND` |
| `01/15/2026` | `NO_MM_FOUND` |

---

## Complete Single-Action Expression

For a one-liner that does everything:

```
if(empty(match(concat(coalesce(triggerOutputs()?['body/subject'],''), ' ', coalesce(triggerOutputs()?['body/body'],'')), '(?i)mm[\s:#-]?\s*(\d{7})')), 'NO_MM_FOUND', last(first(match(concat(coalesce(triggerOutputs()?['body/subject'],''), ' ', coalesce(triggerOutputs()?['body/body'],'')), '(?i)mm[\s:#-]?\s*(\d{7})'))))
```

This handles null subject/body gracefully with `coalesce()`.
