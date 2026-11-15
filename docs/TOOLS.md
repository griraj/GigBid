# MCP tool registry

| Server | Tool | Mode | Guard |
|---|---|---|---|
| Portfolio | search_evidence | read | persona filter, k <= 20 |
| Portfolio | get_case_study | read | stable item id |
| Portfolio | list_skills | read | persona scope |
| Marketplace | search_jobs | read | marketplace port |
| Marketplace | get_job | read | marketplace port |
| Marketplace | get_client_history | read | marketplace port |
| Marketplace | get_connects_balance | read | marketplace port |
| Marketplace | list_messages | read | marketplace port |
| Marketplace | create_proposal_draft | write | idempotency key, dry-run default |
| Marketplace | submit_proposal | write | idempotency key, dry-run default |
| Marketplace | send_message | write | idempotency key, dry-run default |
| Workspace | free_calendar_slots | read | bounded days |
| Workspace | create_interview_hold | write local | no external invitations |
| Workspace | create_email_draft | write local | never sends |

Portfolio resources: `portfolio://case/{id}`, `portfolio://proposal/{id}`. Prompt: `answer_screening_question`. The bid and conversation graphs now use a role-filtered MCP ClientSession over stdio by default. A contract test checks annotations and write schema parameters. Current servers still **do not** implement HTTP bearer authentication or production per-user rate limits. Upwork live access requires official OAuth and approval of the hosting client. GitHub's third-party official MCP server is configurable with a separately authorized read-only token but not connected by default.
