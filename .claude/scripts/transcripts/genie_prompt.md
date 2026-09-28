# Genie prompt — build the transcript tables

Paste into Genie (Assistant, agent mode) in a new notebook in the Databricks workspace.

---

Read every JSONL file in the volume `/Volumes/workspace/claude_history/transcripts/raw/` with Spark
and build three Delta tables in `workspace.claude_history`: `sessions`, `turns` and `tool_calls`.
The goal is to find where my Claude Code agent wastes tokens or fails, so the tables must make
failures, retries and token use easy to query.

What the data is:
- Claude Code session transcripts, one JSON record per line. The schema is inconsistent across
  records and versions, so infer it from a sample first, then parse defensively (read as text and
  use `from_json`/`get_json_object`, rather than trusting a single inferred schema).
- The file name is the source path with `__` for folder separators:
  `<project>__<sessionId>.jsonl` for a main session, and
  `<project>__<sessionId>__subagents__...__agent-<id>.jsonl` for a subagent spawned by that session.
  Keep `project`, `session_id`, `is_subagent` and `agent_id` from the file name.
- Useful fields on a record: `type` (user / assistant / system / summary / others), `uuid`,
  `parentUuid`, `sessionId`, `timestamp`, `cwd`, `gitBranch`, `version`, `isSidechain`,
  `message.role`, `message.model`, `message.content` (a string, or an array of blocks with
  `type` = text / thinking / tool_use / tool_result), `message.usage` (`input_tokens`,
  `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`).
- `tool_use` blocks have `id`, `name`, `input`. `tool_result` blocks arrive in a later user record
  and have `tool_use_id`, `content`, `is_error`. Secrets were replaced with `[REDACTED...]`.

Tables:
1. `tool_calls`: one row per tool_use, joined to its tool_result: session, project, is_subagent,
   timestamp, tool name, a short input summary (the command, file path or pattern, truncated to
   500 chars), is_error, the first 500 chars of the result, seconds until the result arrived, and
   whether the same tool was called again with near-identical input within the next 3 calls
   (a retry).
2. `turns`: one row per assistant message: session, timestamp, model, the four usage token counts,
   number of tool calls, whether it had thinking, and text length.
3. `sessions`: one row per file: project, session, is_subagent, start, end, duration, model(s),
   total tokens by type, number of user prompts, tool calls, tool errors, retries, and the first
   user prompt truncated to 300 chars.

Show me the row counts and a sample from each table, then list the ten most common tool errors
grouped by tool and error text. Write the ingestion so re-running it on new files in the volume
appends only files it hasn't loaded yet.
