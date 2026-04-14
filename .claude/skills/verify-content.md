# Skill: Verify Content Draft

## Description
Verify the factual accuracy of a content draft in `/Vault/Needs_Action/`. Check statistics, case studies, references, and sources for accuracy.

## Instructions

When asked to verify a draft, follow these steps:

1. **Read the draft** from `/Vault/Needs_Action/`
2. **Check each factual claim**:
   - Statistics and numbers match cited sources
   - Case studies are real and recent (within 7-14 days if possible)
   - Expert quotes are properly attributed
   - Organization names and programs are correct
3. **Verify Pakistan connection** is factual and relevant
4. **Check sources** are credible (WHO, UNICEF, government reports, academic research, major news outlets)
5. **Update the draft**:
   - Mark verified items in the checklist
   - Add verification notes
   - Update the `status` frontmatter to `verified` if all checks pass
   - If issues found, add `verification_notes` to frontmatter listing concerns
6. **Log the verification** action

### Verification Standards
- Statistics must come from reports published within the last 2 years
- Case studies must be from identifiable, real events
- Opinions must be clearly distinguished from facts
- Any unverifiable claims should be flagged for human review

### Output Format
Add a `## Verification Results` section to the draft:
```markdown
## Verification Results
- **Status:** Verified / Needs Review
- **Verified Claims:** [count]
- **Flagged Items:** [list any concerns]
- **Verified By:** AI Employee
- **Verified On:** [date]
```
