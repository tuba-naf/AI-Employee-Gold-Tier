# Skill: Review Drafts

## Description
Review all pending drafts in `/Vault/Needs_Action/` and provide a summary of what needs attention. Optionally process a specific draft by verifying and approving it.

## Instructions

When asked to review drafts, follow these steps:

1. **Scan `/Vault/Needs_Action/`** for all `.md` files
2. **Categorize by platform**: LinkedIn, Instagram, News
3. **For each draft, check**:
   - Has proper frontmatter (platform, status, cycle_type)
   - Content has been generated (not just a template)
   - Verification checklist status
4. **Generate a review summary** listing:
   - Total drafts per platform
   - Which drafts are ready for human review
   - Which drafts still need content generation
   - Which drafts have been verified
5. **If asked to approve a specific draft**:
   - Read the full draft content
   - Verify it meets quality standards
   - Move it to `/Vault/Completed/` with updated status
   - Update the Dashboard

### Review Summary Format
```markdown
## Draft Review Summary — [date]

### LinkedIn ([count] drafts)
| File | Cycle Type | Status | Action Needed |
|------|-----------|--------|---------------|
| ... | ... | ... | ... |

### Instagram ([count] drafts)
| File | Cycle Type | Status | Action Needed |
|------|-----------|--------|---------------|
| ... | ... | ... | ... |

### News ([count] drafts)
| File | Cycle Type | Status | Action Needed |
|------|-----------|--------|---------------|
| ... | ... | ... | ... |
```
