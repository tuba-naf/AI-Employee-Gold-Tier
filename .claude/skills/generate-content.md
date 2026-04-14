# Skill: Generate Content Draft

## Description
Generate a content draft for a specific platform (LinkedIn, Instagram, or News) based on a topic or source. The draft follows the content rotation cycle and is saved to the Obsidian vault.

## Instructions

When the user asks to generate content, follow these steps:

1. **Determine the platform**: LinkedIn, Instagram, or News
2. **Determine the cycle position**: Check existing drafts in `/Vault/Needs_Action/` to determine the next position in the rotation cycle (Local Problem → Local Hopeful → Global Problem → Global Hopeful)
3. **Research the topic**: Use the provided topic or search for trending topics relevant to Pakistan
4. **Generate the draft** following these rules:
   - **LinkedIn**: 500+ words, professional tone, facts/statistics, Pakistan-focused
   - **Instagram**: 300+ words, engaging tone, visual suggestions, hashtags
   - **News**: Analysis with critique and hopeful angle, verified facts, Pakistan connection
5. **Save the draft**: Write the `.md` file to `/Vault/Needs_Action/` with proper frontmatter
6. **Create a plan**: Write a corresponding plan file to `/Vault/Plans/`
7. **Update the dashboard**: Update `/Vault/Dashboard.md` with new counts

### Content Rotation Rules
- One post focuses on a local problem/issue in Pakistan
- The next highlights a local hopeful/positive solution
- The following addresses a global issue, connected back to Pakistan
- The next highlights global hopeful/positive developments
- This sequence repeats continuously

### Frontmatter Template
```yaml
---
platform: [LinkedIn|Instagram|News]
status: pending
cycle_type: [local_problem|local_hopeful|global_problem|global_hopeful]
created: [ISO timestamp]
---
```

### Quality Checklist
- [ ] Facts and statistics are accurate and cited
- [ ] Real case studies or examples included
- [ ] Pakistan context is highlighted
- [ ] Appropriate tone for the platform
- [ ] Word count meets target
- [ ] Sources are verifiable
