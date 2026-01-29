# RERT Implementation Guide
## Receiving Exception Resolution Tracker

---

## 1. MVP Column Validation

Your proposed MVP columns are **sufficient and well-designed**. Here's the validation:

| Column | Purpose | Verdict |
|--------|---------|---------|
| PO Number | Primary identifier, parsed from subject | ✅ Essential |
| MM Number | Material Master, optional context | ✅ Good - optional field handles variability |
| VIM Document ID | Links to SAP VIM queue later | ✅ Correct to backfill |
| Issue | Auto-populated problem description | ✅ Essential |
| Buyer Notes | Manual context/resolution notes | ✅ Essential for workflow |
| Vendor ID | Backfilled for filtering/reporting | ✅ Useful for patterns |
| Value | Financial magnitude (informational) | ✅ See section below |
| First Email Received Date | Audit trail, aging metrics | ✅ Essential |
| Resolved | Simple Yes/No closure | ✅ Keeps it operational |

### One Suggested Addition for MVP

| Column | Type | Reason |
|--------|------|--------|
| **Buyer** | Person or Text | So you can filter "my open issues" - extract from To: field or maintain a PO-to-Buyer lookup |

---

## 2. How to Define "Value" to Avoid Confusion

### Recommended Column Definition

```
Column Name: Value
Type: Currency (or Number with 2 decimal places)
Description: "Approximate financial magnitude for prioritization. NOT for accounting. 
             May represent PO net value, invoice value, or estimated line value. 
             Backfilled manually or via later automation."
Default: Blank (not zero - zero implies known zero-value)
```

### Why This Works

1. **Currency type** signals "money-related" but the description clarifies it's not authoritative
2. **Blank default** avoids confusion between "unknown" and "zero-value issue"
3. **Description in SharePoint column settings** serves as documentation

### Column Description Text (paste into SharePoint)

```
Informational only. Approximate financial magnitude for prioritization purposes. 
Not used for accounting, payment, or reconciliation. May be populated later with 
PO net value, invoice value, or estimated line value.
```

---

## 3. Future v2 Enhancements (Without Redesigning v1)

| Enhancement | Description | When to Add |
|-------------|-------------|-------------|
| Days Open | Calculated column: Today minus First Email Date | After MVP stable |
| Status | Replace Yes/No with: Open, In Progress, Blocked, Resolved | If workflow complexity grows |
| Resolution Category | Dropdown: Qty mismatch, Price variance, Missing PO, etc. | For root cause reporting |
| Last Updated | Auto-timestamp on any edit | For stale issue detection |
| Email Thread Link | Hyperlink back to Outlook conversation | If email reference needed |
| Attachment Count | Number indicator | If documents matter |

**Do not add these to v1.** Get the basic loop working first.

---

## 4. HOW TO IMPLEMENT THIS

This is the critical section. Here's exactly how to execute.

### Step 1: Create the SharePoint List (Manual, ~10 minutes)

1. Go to your SharePoint site
2. Click **New** → **List** → **Blank list**
3. Name it: `RERT` or `Receiving Exceptions`
4. Add columns one by one:

| Click "Add column" | Choose Type | Column Name | Settings |
|--------------------|-------------|-------------|----------|
| Single line of text | Text | PO Number | Required: Yes |
| Single line of text | Text | MM Number | Required: No |
| Single line of text | Text | VIM Document ID | Required: No |
| Multiple lines of text | Text | Issue | Required: No |
| Multiple lines of text | Text | Buyer Notes | Required: No |
| Single line of text | Text | Vendor ID | Required: No |
| Currency | Currency | Value | Required: No, Decimals: 2 |
| Date and time | Date | First Email Received | Required: No |
| Yes/No | Boolean | Resolved | Default: No |
| Person | Person | Buyer | Required: No (optional v1 add) |

### Step 2: Create the Outlook Folder (Manual, ~1 minute)

1. In Outlook, create a folder: `RERT Intake`
2. This is where you'll drag/move emails from warehouse

### Step 3: Build the Power Automate Flow

**This is where the automation lives. Here's exactly what to do:**

#### Option A: Use Copilot in Power Automate (Recommended)

Go to [make.powerautomate.com](https://make.powerautomate.com) and click **Create** → **Describe it to design it** (Copilot).

**Paste this prompt into Copilot:**

```
When a new email arrives in my "RERT Intake" folder in Outlook:

1. Extract the PO number from the email subject. The subject format is "PO" followed by a 10-digit number.

2. Look for "MM:" in the email body and extract the number after it if present.

3. Look for "Issue:" in the email body and extract all text after it as the issue description.

4. Create a new item in my SharePoint list called "RERT" with these values:
   - PO Number: the extracted PO number
   - MM Number: the extracted MM number (or leave blank)
   - Issue: the extracted issue text
   - First Email Received: the email received date
   - Resolved: No
```

Copilot will generate a draft flow. You'll need to:
- Connect it to your Outlook account
- Connect it to your SharePoint site
- Test with a sample email

#### Option B: Build Manually Step-by-Step

If Copilot doesn't generate what you need, build it manually:

**Create a new Automated Cloud Flow:**

1. **Trigger:** "When a new email arrives in a shared mailbox" or "When a new email arrives (V3)"
   - Folder: RERT Intake
   - Include Attachments: No

2. **Action: Initialize variable** (for PO Number)
   - Name: `varPONumber`
   - Type: String
   - Value: (leave blank for now)

3. **Action: Initialize variable** (for MM Number)
   - Name: `varMMNumber`
   - Type: String
   - Value: (leave blank)

4. **Action: Initialize variable** (for Issue)
   - Name: `varIssue`
   - Type: String
   - Value: (leave blank)

5. **Action: Compose** (Extract PO from Subject)
   - Inputs: Use this expression:
   ```
   trim(replace(triggerOutputs()?['body/subject'],'PO ',''))
   ```

6. **Action: Set variable** 
   - Name: varPONumber
   - Value: Output from previous Compose

7. **Action: Compose** (Extract Issue from Body)
   - This is trickier. Use expression:
   ```
   if(contains(triggerOutputs()?['body/body'],'Issue:'),
      trim(substring(triggerOutputs()?['body/body'],
           add(indexOf(triggerOutputs()?['body/body'],'Issue:'),6))),
      'See email for details')
   ```

8. **Action: Set variable**
   - Name: varIssue  
   - Value: Output from previous Compose

9. **Action: Create item** (SharePoint)
   - Site Address: [Your SharePoint site]
   - List Name: RERT
   - PO Number: varPONumber
   - Issue: varIssue
   - First Email Received: `triggerOutputs()?['body/receivedDateTime']`
   - Resolved: No

### Step 4: Test the Flow

1. Send yourself a test email with subject: `PO 1234567890`
2. Body: `MM: 100012345 Issue: Quantity received does not match PO`
3. Move the email to your RERT Intake folder
4. Check if a SharePoint item was created
5. Verify the fields populated correctly

---

## 5. Expression Reference for Power Automate

These are copy-paste expressions for the flow:

### Extract PO Number from Subject
```
trim(replace(triggerOutputs()?['body/subject'],'PO ',''))
```

### Extract MM Number (if present)
```
if(
  contains(triggerOutputs()?['body/body'],'MM:'),
  trim(first(split(last(split(triggerOutputs()?['body/body'],'MM:')),' '))),
  ''
)
```

### Extract Issue Text
```
if(
  contains(triggerOutputs()?['body/body'],'Issue:'),
  trim(last(split(triggerOutputs()?['body/body'],'Issue:'))),
  triggerOutputs()?['body/bodyPreview']
)
```

### Get Email Received Date
```
triggerOutputs()?['body/receivedDateTime']
```

---

## 6. Implementation Sequence

| Step | Action | Time |
|------|--------|------|
| 1 | Create SharePoint list with all columns | 10 min |
| 2 | Create Outlook folder | 1 min |
| 3 | Create Power Automate flow using Copilot prompt above | 15-30 min |
| 4 | Test with sample email | 5 min |
| 5 | Adjust expressions if parsing fails | 10-20 min |
| 6 | Go live with real emails | - |

---

## 7. Answering Your Direct Question

> "DO I BREAK IT DOWN INTO PROMPTS TO GIVE TO COPILOT INSIDE POWER AUTOMATE OR HOW DO I EXECUTE WHAT YOU WRITE?"

**Yes, use the Copilot prompt in Section 4, Option A.** That's the fastest path.

If Copilot's output needs adjustment:
1. Let Copilot create the skeleton
2. Click into individual actions to fix expressions
3. Use the expressions from Section 5 as copy-paste fixes

**You do NOT need to:**
- Write code line by line
- Use a programming language
- Install anything

**You DO:**
- Create SharePoint list manually (point and click)
- Create Outlook folder manually
- Use Power Automate's visual designer (or Copilot to generate it)
- Copy-paste expressions into the expression editor when needed

---

## 8. Common Issues and Fixes

| Problem | Solution |
|---------|----------|
| PO number has extra spaces | Wrap extraction in `trim()` |
| Email body is HTML not plain text | Use `body/bodyPreview` instead of `body/body` for simpler parsing |
| MM number not found | The `if(contains(...))` pattern handles this gracefully |
| Flow runs on wrong emails | Check the folder filter in the trigger |
| SharePoint item not created | Check your SharePoint connection and list name spelling |

---

## Summary

1. **MVP columns are valid** - consider adding Buyer
2. **Value field**: Use Currency type, blank default, add description clarifying it's informational
3. **v2 enhancements**: Days Open, Status dropdown, Resolution Category - add later
4. **Implementation**: Use Power Automate Copilot with the prompt provided, then refine with the expressions

Start with the SharePoint list, then the Outlook folder, then the flow. Test with fake emails before going live.
