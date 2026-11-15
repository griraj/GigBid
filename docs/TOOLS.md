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

Portfolio resources: `portfolio://case/{id}`, `portfolio://proposal/{id}`. Prompt: `answer_screening_question`. Current servers expose stdio transport and do **not** yet implement HTTP bearer authentication, third-party MCP trust integration, or formal annotation/schema snapshots. Upwork should only be trusted after user-authorized OAuth via the official endpoint; GitHub MCP should be authorized read-only with a limited scope.
