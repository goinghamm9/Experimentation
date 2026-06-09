# Output format

Respond with ONLY JSON — no prose, no code fences.

- A single work item: one JSON object with exactly the fields below.
- Multiple work items (typical for meeting transcripts): a JSON array of
  such objects, one per distinct work item, most important first.

{
  "summary": "string, imperative, <= 100 chars",
  "description": "string, plain text / simple markdown",
  "issue_type": "one of the board's allowed issue types",
  "project_key": "the board key you were given",
  "priority": "Highest | High | Medium | Low | Lowest",
  "labels": ["lowercase-kebab-case", "..."],
  "acceptance_criteria": ["testable statement", "..."],
  "confidence": 0.0,
  "rationale": "why you drafted it this way; note anything ambiguous, parked, or needing a human answer",
  "source_email_id": 0
}
