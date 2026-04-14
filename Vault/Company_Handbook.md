---
last_updated: 2026-03-24
version: "3.0"
tier: Gold
---

# Company Handbook — Gold Tier

## Mission
Operate as a fully autonomous content engine for sustainability, climate, and environment topics — generating verified, Pakistan-focused content drafts for **LinkedIn, Instagram, News, and Facebook**, auto-posting to Facebook via the Meta Graph API, and delivering other platform drafts to the human reviewer via email.

## Tier: Gold
Gold Tier adds on top of Silver:
- **Facebook auto-posting** — verified drafts posted directly to a Facebook Page via Meta Graph API
- **Facebook MCP server** — `gold-facebook` exposes list/post/summary tools callable by Claude Code
- **Auto-post eligibility** — verified drafts with `auto_post_eligible: true` post without HITL when `AUTO_POST_FACEBOOK=true`
- **Multiple MCP servers** — `gold-email` for draft delivery, `gold-facebook` for page management
- **Comprehensive audit logging** — every post attempt logged with Facebook Post ID

---

## Rules of Engagement

### Content Rules
1. AI drafts content — fact-checked by GPT-4o before any post or delivery
2. **Facebook:** auto-posted when `AUTO_POST_FACEBOOK=true` and draft is verified; otherwise requires human to move to `/Approved/`
3. **LinkedIn / Instagram / News:** human reviews emailed draft and posts manually
4. Verified drafts are stored in `/Completed/` as immutable archive
5. All content must include real case studies, verifiable statistics, and credible references

### Content Focus Areas
All content must cover one or more of these themes:
- **Climate Change** — global warming, emissions, IPCC reports, COP summits, net zero
- **Sustainability** — renewable energy, circular economy, green tech, sustainable development
- **Environment** — pollution (air, water, plastic), deforestation, biodiversity loss, conservation
- **Natural Disasters** — floods, droughts, heat waves, glacial melt (climate-linked)
- **Green Solutions** — solar/wind energy, reforestation, waste management, clean water, EVs

### Content Rotation Pattern
Follow this 4-post cycle continuously for each platform:

| Step | Type | Description |
|------|------|-------------|
| 1 | **Local Problem** | Current environmental or climate crisis in Pakistan — facts, figures, case studies, credible references |
| 2 | **Local Hopeful** | Green solutions, sustainability success stories, or environmental initiatives in Pakistan |
| 3 | **Global Problem** | Trending global climate/environmental crisis — connect relevance and lessons for Pakistan |
| 4 | **Global Hopeful** | Global green innovations or climate breakthroughs — how they could inspire action in Pakistan |

### Content Standards
| Platform | Min Words | Tone | Requirements |
|----------|-----------|------|--------------|
| LinkedIn | 500+ | Professional | Facts/stats, citations, Pakistan context, call to action |
| Instagram | 300+ | Engaging | Conversational, image suggestion, hashtags |
| News | 600+ | Journalistic | Policy critique + hopeful angle, verified sources, Pakistan connection |
| Facebook | 400+ | Conversational | Shareable, ends with question/CTA, hashtags, image suggestion |

- All statistics must have inline citations: [1], [2], etc.
- No fabricated or unverifiable numbers — describe qualitatively if uncertain
- Only content from the last 7-14 days should be considered
- Every post must connect to Pakistan's environmental context

### Draft Delivery Schedule
| Platform | Frequency | Trigger | Delivery Method |
|----------|-----------|---------|----------------|
| LinkedIn | Every 2 days | scheduled_run.py via Task Scheduler | Email to reviewer |
| Instagram | Every 2 days | scheduled_run.py via Task Scheduler | Email to reviewer |
| News | Daily | scheduled_run.py via Task Scheduler | Email to reviewer |
| Facebook | Every 2 days | run_facebook.bat via Task Scheduler | Auto-post to Page |

---

## Workflow

### Facebook Auto-Post (Gold Tier)
```
1. Task Scheduler runs run_facebook.bat
         |
         v
2. facebook_watcher.py scans RSS feeds for trending topics
         |
         v
3. FACEBOOK_*.md created in /Inbox/
   + PLAN_*.md created in /Plans/
         |
         v
4. GPT-4o fact-checks draft
   → Verified: copied to /Completed/, status = verified
   → Needs Review: stays in /Needs_Action/, status = needs_review
         |
         v
5. facebook_post.py runs
   → AUTO_POST_FACEBOOK=true:
       Verified + auto_post_eligible: true → auto-moved to /Approved/ → posted to Facebook Page
   → AUTO_POST_FACEBOOK=false:
       Human moves file to /Approved/ → facebook_post.py posts on next run
         |
         v
6. /Completed/FACEBOOK_*.md updated with Post ID and timestamp
7. Dashboard.md updated
```

### LinkedIn / Instagram / News (Silver-style HITL)
```
1. Task Scheduler runs scheduled_run.py
         |
         v
2. Watcher scans RSS feeds for trending topics
         |
         v
3. Draft .md file created in /Needs_Action/
   + Plan .md file created in /Plans/
         |
         v
4. AI fact-checks draft via GPT-4o
   → Verified: copied to /Completed/, status = verified
   → Needs Review: stays in /Needs_Action/, status = needs_review
         |
         v
5. email_drafts.py sends HTML email digest to REVIEWER_EMAIL
         |
         v
6. Reviewer reads email
   → Approved: copy-paste to LinkedIn/Instagram/website manually
   → Rejected: ignore or request revision
         |
         v
7. Dashboard.md updated with current counts
```

---

## Security & Privacy

### Credential Management
- All credentials stored in `.env` — **never committed to git**
- `.gitignore` must include `.env` at all times
- Use `.env.example` as the onboarding template (sanitized, no real values)
- **FB_PAGE_ACCESS_TOKEN** — long-lived token, rotate every 60 days; revoke immediately if exposed
- Rotate all API keys monthly and immediately after any suspected exposure
- Use Gmail App Passwords — never use your main Google account password

### Permission Boundaries
| Action | Auto (AI) | Requires Human |
|--------|-----------|----------------|
| Draft creation | Yes | — |
| AI fact-checking | Yes | — |
| Move to /Completed/ | Yes (verified only) | — |
| Email draft to reviewer | Yes | — |
| Post to Facebook (AUTO_POST=true) | Yes (verified only) | — |
| Post to Facebook (AUTO_POST=false) | No | Yes — move to /Approved/ |
| Post to LinkedIn | No | Yes — always |
| Post to Instagram | No | Yes — always |
| Delete any file | No | Yes — always |

### Audit Logging
- Every action logged to `/Logs/YYYY-MM-DD.json`
- Log fields: timestamp, action_type, actor, target, parameters, result, post_id, error
- Logs are immutable — never deleted or modified
- Retain logs for minimum 90 days

### DRY_RUN Mode
- `DRY_RUN=true` disables all external actions (email sending, Facebook posting)
- All actions are logged as `[DRY RUN]` — safe for testing and development
- Always set `DRY_RUN=true` in a new environment until fully verified

---

## Folder Reference
| Folder | Purpose |
|--------|---------|
| `/Inbox` | Raw task drops and inputs |
| `/Needs_Action` | Drafts awaiting verification and review |
| `/Plans` | AI-generated task plans |
| `/Completed` | Verified and approved/posted content (archived) |
| `/Pending_Approval` | Actions awaiting human sign-off |
| `/Approved` | Human-approved or auto-approved Facebook drafts ready to post |
| `/Rejected` | Rejected actions (archived, never retried automatically) |
| `/Logs` | JSON audit logs |

---
*AI Employee Wavy v2.0 — Gold Tier*
