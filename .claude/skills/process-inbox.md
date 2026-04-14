# Skill: Process Inbox

## Description
Process all files in `/Vault/Inbox/` — move them to `/Needs_Action/` with metadata, then create plans for each item.

## Instructions

When asked to process the inbox:

1. **Scan `/Vault/Inbox/`** for all files
2. **For each file**:
   - Read the file contents
   - Determine the type (content request, raw text, data file)
   - Create a corresponding `.md` file in `/Vault/Needs_Action/` with proper frontmatter
   - Create a plan file in `/Vault/Plans/`
   - Log the action to `/Vault/Logs/`
3. **After processing all files**:
   - Update the Dashboard
   - Report what was processed

### File Type Detection
- `.md` files: Read and categorize by content (LinkedIn, Instagram, News, or general)
- `.txt` files: Convert to `.md` with metadata
- Other files: Create a metadata `.md` file referencing the original

### Frontmatter for Processed Files
```yaml
---
type: inbox_item
original_name: [filename]
received: [ISO timestamp]
status: pending
---
```

### After Processing
- Move or delete the original from `/Inbox/` (user preference)
- Update Dashboard.md with new counts
- Log all actions to daily log file
