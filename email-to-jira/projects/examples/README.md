# Few-shot example store

One YAML per board (`MSA.yaml`, `PV0.yaml`, …), each a list of
`{source, ticket}` pairs. These are merged with the board YAML's inline
`few_shot_examples` and sent to the model with every draft for that board.

Three ways to add examples:
1. **Dashboard → Examples page**: paste a source email/transcript + the ideal
   ticket. This is where exported content from your past Claude/ChatGPT
   drafting chats goes — copy the client email you pasted into the chat as
   `source`, and the final ticket you settled on as the ticket fields.
2. **Dashboard → "Save as few-shot example"** on any reviewed candidate:
   captures the source and the ticket exactly as you edited/approved it.
3. Edit these files by hand.

Format:
```yaml
- source: |
    From: client@example.com
    Subject: Login broken
    ...raw email or transcript excerpt...
  ticket:
    summary: "Fix login redirect loop on Safari"
    description: |
      ...
    issue_type: Bug
    priority: High
    labels: [auth]
    acceptance_criteria:
      - "Safari login lands on the dashboard"
```
