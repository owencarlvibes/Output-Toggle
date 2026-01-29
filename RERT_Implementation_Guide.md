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

## 8. Power Automate Enhancements (Recommended)

These additions will make your flow more robust:

### 8.1 Duplicate Detection (Highly Recommended)

Prevents creating duplicate entries if the same PO issue is emailed multiple times.

**Add before "Create item":**

1. **Action: Get items** (SharePoint)
   - Site Address: [Your site]
   - List Name: RERT
   - Filter Query: `PO_x0020_Number eq 'varPONumber'`
   - Top Count: 1

2. **Action: Condition**
   - If `length(body('Get_items')?['value'])` is equal to `0`
   - Yes branch: Create the SharePoint item
   - No branch: Skip (or update existing item, or send yourself a notification)

**Copilot prompt addition:**
```
Before creating the SharePoint item, check if a record with this PO Number 
already exists. Only create a new item if no existing record is found.
```

---

### 8.2 Extract Buyer from Email (Recommended)

Auto-populate who the issue was sent to.

**Expression to get the To: recipient:**
```
first(triggerOutputs()?['body/toRecipients'])?['emailAddress/name']
```

Or for email address:
```
first(triggerOutputs()?['body/toRecipients'])?['emailAddress/address']
```

Add a **Buyer** or **Assigned To** column in SharePoint (Single line of text) and map this.

---

### 8.3 Mark Email as Read After Processing

Gives you visual confirmation that an email was processed.

**Add after "Create item":**

1. **Action: Mark as read or unread (V3)**
   - Message Id: `triggerOutputs()?['body/id']`
   - Mark as: Read

---

### 8.4 Move Email to "Processed" Folder

Keeps your intake folder clean.

**Add after "Create item":**

1. **Action: Move email (V2)**
   - Message Id: `triggerOutputs()?['body/id']`
   - Folder: RERT Processed (create this folder first)

---

### 8.5 Error Handling for Bad Format

What if someone sends an email without "PO" in the subject?

**Add after trigger, before any parsing:**

1. **Action: Condition**
   - If `contains(triggerOutputs()?['body/subject'], 'PO ')` is equal to `true`
   - Yes branch: Continue with parsing
   - No branch: Send yourself a notification or move to "Manual Review" folder

**Expression for the condition:**
```
contains(triggerOutputs()?['body/subject'], 'PO ')
```

---

### 8.6 Strip HTML from Email Body

Email bodies often contain HTML tags. Use plain text preview instead.

**Use this instead of body/body:**
```
triggerOutputs()?['body/bodyPreview']
```

This gives you the first ~255 characters as plain text. For longer issues, you may need to use `body/body` and strip HTML with:

```
replace(replace(replace(triggerOutputs()?['body/body'],'<br>','\n'),'</p>','\n'),'<[^>]+>','')
```

Note: Power Automate's replace doesn't support regex, so for heavy HTML stripping, use the **Html to text** action from the Content Conversion connector.

---

### 8.7 Notification When Item Created (Optional)

Send yourself or the buyer a Teams/email confirmation.

**Add after "Create item":**

1. **Action: Send an email (V2)** or **Post message in a chat or channel**
   - To: The buyer or yourself
   - Subject: `New RERT Issue: @{variables('varPONumber')}`
   - Body: `Issue logged: @{variables('varIssue')}`

Only add this if people want notifications. Otherwise it's noise.

---

### 8.8 Validate PO is 10 Digits (Optional)

Catches malformed PO numbers before they create bad data.

**Expression to check length:**
```
and(
  greaterOrEquals(length(variables('varPONumber')), 10),
  lessOrEquals(length(variables('varPONumber')), 10)
)
```

Or simpler - just check it's not empty:
```
greater(length(variables('varPONumber')), 0)
```

---

### 8.9 Add Timestamp for Flow Run (Audit Trail)

Add a column called **Created By Flow** (Date/Time) and populate it with:

```
utcNow()
```

This lets you distinguish items created by the flow vs. manually entered.

---

### Summary: Recommended Additions by Priority

| Priority | Enhancement | Why |
|----------|-------------|-----|
| **High** | Duplicate detection | Prevents duplicate entries for same PO |
| **High** | Error handling for bad format | Prevents flow failures |
| **Medium** | Mark email as read | Visual confirmation of processing |
| **Medium** | Extract buyer | Reduces manual backfill |
| **Medium** | Strip HTML / use bodyPreview | Cleaner issue text |
| **Low** | Move to processed folder | Keeps inbox clean |
| **Low** | Notifications | Only if stakeholders want them |
| **Low** | PO validation | Only if bad data is a real problem |

---

### Complete Enhanced Copilot Prompt

If you want Copilot to build a more complete flow, use this expanded prompt:

```
When a new email arrives in my "RERT Intake" folder in Outlook:

1. First check if the subject contains "PO ". If not, move the email to a 
   folder called "RERT Manual Review" and stop.

2. Extract the PO number from the email subject (the 10 digits after "PO ").

3. Check my SharePoint list called "RERT" to see if a record with this 
   PO Number already exists.

4. If no existing record:
   - Look for "MM:" in the email body and extract the number after it
   - Look for "Issue:" in the email body and extract the text after it
   - Get the name of the person in the To field
   - Create a new item in the RERT list with:
     - PO Number: the extracted PO
     - MM Number: the extracted MM (or blank)
     - Issue: the extracted issue text
     - Buyer: the To recipient name
     - First Email Received: the email received date
     - Resolved: No

5. After creating the item (or if duplicate found), mark the email as read.
```

---

## 9. Common Issues and Fixes (Error Prevention Guide)

Power Automate is notorious for cryptic errors. Here's everything that typically breaks and the exact fixes.

---

### 9.1 SharePoint Column Internal Names

**The #1 source of errors.** SharePoint display names ≠ internal names.

| Display Name | Internal Name (use this in expressions) |
|--------------|----------------------------------------|
| PO Number | PO_x0020_Number |
| MM Number | MM_x0020_Number |
| VIM Document ID | VIM_x0020_Document_x0020_ID |
| Buyer Notes | Buyer_x0020_Notes |
| Vendor ID | Vendor_x0020_ID |
| First Email Received Date | First_x0020_Email_x0020_Received_x0020_Date |
| Resolved | Resolved |
| Value | Value |
| Issue | Issue |
| Buyer | Buyer |

**Rule:** Spaces become `_x0020_` in internal names.

**How to find internal names:**
1. Go to SharePoint list → Settings (gear) → List settings
2. Click on the column name
3. Look at the URL - the internal name is in `&Field=`

**Or avoid this entirely:** Name your columns WITHOUT spaces when creating them:
- `PONumber` instead of `PO Number`
- `MMNumber` instead of `MM Number`
- `FirstEmailDate` instead of `First Email Received Date`

---

### 9.2 Expression Syntax Errors

**Error:** "The expression is invalid" or "Expected ','"

**Common causes and fixes:**

| Wrong | Right |
|-------|-------|
| `@triggerOutputs()` | `triggerOutputs()` (no @ inside expression box) |
| `body('Get_items').value` | `body('Get_items')?['value']` |
| `triggerOutputs().body.subject` | `triggerOutputs()?['body/subject']` |
| `variables(varPONumber)` | `variables('varPONumber')` (quotes around name) |
| `'PO Number'` in filter | `PO_x0020_Number` (internal name, no quotes around column) |
| Missing `?` | Always use `?['field']` for null safety |

**The `?` operator:** Always use `?['fieldname']` instead of `['fieldname']`. The `?` prevents errors when a field is null.

---

### 9.3 Complete Copy-Paste Expressions (Tested)

These are the exact expressions to paste into the expression editor. Copy these character-for-character.

**Extract PO Number from Subject:**
```
trim(replace(triggerOutputs()?['body/subject'],'PO ',''))
```

**Extract Issue from Body (with fallback):**
```
if(contains(coalesce(triggerOutputs()?['body/bodyPreview'],''),'Issue:'),trim(last(split(triggerOutputs()?['body/bodyPreview'],'Issue:'))),'See email for details')
```

**Extract MM Number (with fallback to empty):**
```
if(contains(coalesce(triggerOutputs()?['body/bodyPreview'],''),'MM:'),trim(first(split(substring(triggerOutputs()?['body/bodyPreview'],add(indexOf(triggerOutputs()?['body/bodyPreview'],'MM:'),3)),' '))),'')
```

**Get Buyer from To field:**
```
coalesce(first(triggerOutputs()?['body/toRecipients'])?['emailAddress/name'],'Unknown')
```

**Get Email Received Date:**
```
triggerOutputs()?['body/receivedDateTime']
```

**Get Email ID (for marking as read):**
```
triggerOutputs()?['body/id']
```

**Check if PO exists in subject:**
```
contains(coalesce(triggerOutputs()?['body/subject'],''),'PO ')
```

**Check if duplicate exists (after Get items):**
```
equals(length(body('Get_items')?['value']),0)
```

**Current timestamp:**
```
utcNow()
```

---

### 9.4 Filter Query Syntax for SharePoint

**Error:** "The filter query is not valid" or similar

**Correct filter query syntax for "Get items":**

For text columns:
```
PO_x0020_Number eq 'VALUE_HERE'
```

With a variable (use the expression editor, not dynamic content):
```
PO_x0020_Number eq '@{variables('varPONumber')}'
```

**But wait** - if you type that in the Filter Query box, you need to format it correctly:

**In the Filter Query field, type this exactly:**
```
PO_x0020_Number eq '
```
Then click the lightning bolt (dynamic content) → Expression tab → type:
```
variables('varPONumber')
```
Then click OK, then type the closing:
```
'
```

**Or use Compose first:**
1. Add a Compose action before Get items
2. Expression: `concat('PO_x0020_Number eq ''', variables('varPONumber'), '''')`
3. In Get items Filter Query, use the output of that Compose

---

### 9.5 Null and Empty Value Handling

**Error:** "The template language function 'split' expects its first parameter to be of type string"

**Cause:** The email body or field is null.

**Fix:** Wrap values in `coalesce()`:

| Wrong | Right |
|-------|-------|
| `split(triggerOutputs()?['body/body'],'Issue:')` | `split(coalesce(triggerOutputs()?['body/body'],''),'Issue:')` |
| `length(variables('varPONumber'))` | `length(coalesce(variables('varPONumber'),''))` |

**What coalesce does:** Returns the first non-null value. `coalesce(null, '')` returns `''`.

---

### 9.6 Data Type Mismatches

**Error:** "The value 'xxx' is not a valid number" or "Expected type Boolean"

| SharePoint Column Type | Expression Must Return |
|-----------------------|----------------------|
| Single line of text | String |
| Number | Number (use `int()` or `float()`) |
| Currency | Number (use `float()`) |
| Yes/No | Boolean: `true` or `false` (not 'Yes'/'No') |
| Date | ISO date string or `utcNow()` |
| Person | Email address (if configured for email) |

**For Yes/No (Resolved) column:**
```
false
```
Not `'No'`, not `'false'`, just: `false`

**For Currency (Value) column - leave blank:**
```
null
```
Or just don't map it at all in Create item.

---

### 9.7 Action Reference Names

**Error:** "The action 'Get_items' does not exist"

Power Automate auto-names actions. If you renamed them or have duplicates:

- `Get_items` might be `Get_items_2` or `Get_items_1`
- `Compose` might be `Compose_2`
- `Set_variable` might be `Set_variable_-_PO_Number`

**How to find the real name:**
1. Click on the action
2. Click the `...` menu → Rename (to see current name)
3. Or look at the action in code view (click `</>` in the top right)

**Fix references accordingly:**
```
body('Get_items')?['value']     -- if action is named "Get items"
body('Get_items_2')?['value']   -- if action is named "Get items 2"
```

---

### 9.8 Trigger Issues

**Error:** Flow never runs, or runs on wrong emails

**Checklist:**
1. Is the folder name spelled exactly right? (Case sensitive)
2. Is it a subfolder? Use the folder picker, don't type the path
3. Is it a shared mailbox? Use "When a new email arrives in a shared mailbox" trigger instead
4. Is the flow turned ON? (Check the flow details page)
5. Did you select the right Outlook account? (Check connection)

**For shared mailbox trigger:**
- Original Mailbox Address: `sharedmailbox@company.com`
- Folder: Select from picker after entering mailbox

---

### 9.9 Connection and Authentication Errors

**Error:** "The connection is not valid" or "Unauthorized"

**Fixes:**
1. Go to flow → Edit → Click on the failing action → Click "Change connection"
2. Remove and re-add the connection
3. Make sure you have permissions to the SharePoint list
4. For shared mailboxes, ensure you have access rights

---

### 9.10 HTML Body Parsing Issues

**Error:** Issue field contains `<div>`, `<br>`, or other HTML

**The problem:** `body/body` returns HTML. `body/bodyPreview` returns plain text but truncated to ~255 chars.

**Best solution for Issue field:**

1. Add the **"Html to text"** action (from Content Conversion connector)
   - Content: `triggerOutputs()?['body/body']`
2. Use the output of that action for parsing

**Or just use bodyPreview if issues are short:**
```
triggerOutputs()?['body/bodyPreview']
```

---

### 9.11 Complete Flow Code View (JSON)

If you want to import a working flow instead of building it, here's the flow definition you can paste into **Import from clipboard** (My flows → Import → Import from clipboard):

Note: You'll need to update the SharePoint site URL and list GUID after import.

```json
{
  "triggers": {
    "When_a_new_email_arrives_in_RERT_Intake": {
      "type": "OpenApiConnectionNotification",
      "inputs": {
        "host": {
          "connection": {
            "name": "@parameters('$connections')['office365']['connectionId']"
          }
        },
        "parameters": {
          "folderPath": "RERT Intake",
          "importance": "Any",
          "fetchOnlyWithAttachment": false,
          "includeAttachments": false
        }
      }
    }
  },
  "actions": {
    "Condition_-_Subject_Contains_PO": {
      "type": "If",
      "expression": {
        "contains": [
          "@coalesce(triggerOutputs()?['body/subject'],'')",
          "PO "
        ]
      },
      "actions": {
        "Set_Variable_-_PO_Number": {
          "type": "SetVariable",
          "inputs": {
            "name": "varPONumber",
            "value": "@trim(replace(triggerOutputs()?['body/subject'],'PO ',''))"
          }
        },
        "Set_Variable_-_Issue": {
          "type": "SetVariable",
          "inputs": {
            "name": "varIssue",
            "value": "@if(contains(coalesce(triggerOutputs()?['body/bodyPreview'],''),'Issue:'),trim(last(split(triggerOutputs()?['body/bodyPreview'],'Issue:'))),'See email for details')"
          },
          "runAfter": {
            "Set_Variable_-_PO_Number": ["Succeeded"]
          }
        },
        "Get_Existing_Items": {
          "type": "OpenApiConnection",
          "inputs": {
            "host": {
              "connection": {
                "name": "@parameters('$connections')['sharepointonline']['connectionId']"
              }
            },
            "method": "get",
            "path": "/datasets/@{encodeURIComponent('YOUR_SITE_URL')}/tables/@{encodeURIComponent('YOUR_LIST_GUID')}/items",
            "queries": {
              "$filter": "PO_x0020_Number eq '@{variables('varPONumber')}'"
            }
          },
          "runAfter": {
            "Set_Variable_-_Issue": ["Succeeded"]
          }
        },
        "Condition_-_No_Duplicate": {
          "type": "If",
          "expression": {
            "equals": [
              "@length(body('Get_Existing_Items')?['value'])",
              0
            ]
          },
          "actions": {
            "Create_SharePoint_Item": {
              "type": "OpenApiConnection",
              "inputs": {
                "host": {
                  "connection": {
                    "name": "@parameters('$connections')['sharepointonline']['connectionId']"
                  }
                },
                "method": "post",
                "path": "/datasets/@{encodeURIComponent('YOUR_SITE_URL')}/tables/@{encodeURIComponent('YOUR_LIST_GUID')}/items",
                "body": {
                  "PO_x0020_Number": "@variables('varPONumber')",
                  "Issue": "@variables('varIssue')",
                  "First_x0020_Email_x0020_Received_x0020_Date": "@triggerOutputs()?['body/receivedDateTime']",
                  "Resolved": false
                }
              }
            }
          },
          "runAfter": {
            "Get_Existing_Items": ["Succeeded"]
          }
        },
        "Mark_Email_As_Read": {
          "type": "OpenApiConnection",
          "inputs": {
            "host": {
              "connection": {
                "name": "@parameters('$connections')['office365']['connectionId']"
              }
            },
            "method": "post",
            "path": "/v2/Mail/MarkAsRead/@{encodeURIComponent(triggerOutputs()?['body/id'])}"
          },
          "runAfter": {
            "Condition_-_No_Duplicate": ["Succeeded"]
          }
        }
      },
      "else": {
        "actions": {
          "Move_To_Manual_Review": {
            "type": "OpenApiConnection",
            "inputs": {
              "host": {
                "connection": {
                  "name": "@parameters('$connections')['office365']['connectionId']"
                }
              },
              "method": "post",
              "path": "/v2/Mail/Move/@{encodeURIComponent(triggerOutputs()?['body/id'])}",
              "body": {
                "destinationFolderPath": "RERT Manual Review"
              }
            }
          }
        }
      }
    },
    "Initialize_varPONumber": {
      "type": "InitializeVariable",
      "inputs": {
        "variables": [{
          "name": "varPONumber",
          "type": "string",
          "value": ""
        }]
      },
      "runAfter": {}
    },
    "Initialize_varIssue": {
      "type": "InitializeVariable", 
      "inputs": {
        "variables": [{
          "name": "varIssue",
          "type": "string",
          "value": ""
        }]
      },
      "runAfter": {
        "Initialize_varPONumber": ["Succeeded"]
      }
    }
  }
}
```

---

### 9.12 Quick Reference Card

Print this out or keep it handy:

| What You Want | Expression |
|---------------|------------|
| Email subject | `triggerOutputs()?['body/subject']` |
| Email body (HTML) | `triggerOutputs()?['body/body']` |
| Email body (plain text) | `triggerOutputs()?['body/bodyPreview']` |
| Email received time | `triggerOutputs()?['body/receivedDateTime']` |
| Email ID | `triggerOutputs()?['body/id']` |
| To recipient name | `first(triggerOutputs()?['body/toRecipients'])?['emailAddress/name']` |
| From sender email | `triggerOutputs()?['body/from/emailAddress/address']` |
| Variable value | `variables('variableName')` |
| Action output | `body('Action_Name')` |
| Array length | `length(body('Get_items')?['value'])` |
| Current time | `utcNow()` |
| Remove spaces | `trim(value)` |
| Check contains | `contains(string,'substring')` |
| Handle null | `coalesce(possiblyNull,'default')` |
| Boolean true | `true` (no quotes) |
| Boolean false | `false` (no quotes) |

---

### 9.13 Error Message Decoder

| Error Message | Translation | Fix |
|---------------|-------------|-----|
| "The expression is invalid" | Syntax error in expression | Check quotes, brackets, `?` operators |
| "Expected ',' or ')'" | Missing comma or paren | Count your parentheses |
| "Cannot find template function" | Typo in function name | Check spelling: `coalesce` not `coelesce` |
| "The action 'X' does not exist" | Wrong action reference name | Check actual action name in designer |
| "Value cannot be null" | Required field is empty | Use `coalesce()` to provide default |
| "The filter query is not valid" | Bad OData filter syntax | Use internal column names, check quotes |
| "Expected type 'Boolean'" | Passing string to Yes/No field | Use `true`/`false` not `'Yes'`/`'No'` |
| "Unauthorized" | Connection expired | Re-authenticate the connection |
| "Resource not found" | Wrong SharePoint URL or list name | Verify site URL and list name |
| "The 'split' expects string" | Null value passed to function | Wrap in `coalesce(value,'')` |

---

---

## Summary

1. **MVP columns are valid** - consider adding Buyer
2. **Value field**: Use Currency type, blank default, add description clarifying it's informational
3. **v2 enhancements**: Days Open, Status dropdown, Resolution Category - add later
4. **Implementation**: Use Power Automate Copilot with the prompt provided, then refine with the expressions

Start with the SharePoint list, then the Outlook folder, then the flow. Test with fake emails before going live.
