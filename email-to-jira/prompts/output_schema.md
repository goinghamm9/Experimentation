# Output format

Respond with ONLY a JSON object — no prose, no code fences — with exactly
these fields:

{
  "summary": "string, imperative, <= 100 chars",
  "description": "string, plain text / simple markdown",
  "issue_type": "one of the board's allowed issue types",
  "project_key": "the board key you were given",
  "priority": "Highest | High | Medium | Low | Lowest",
  "labels": ["lowercase-kebab-case", "..."],
  "acceptance_criteria": ["testable statement", "..."],
  "confidence": 0.0,
  "rationale": "why you drafted it this way; note anything ambiguous",
  "source_email_id": 0
}
