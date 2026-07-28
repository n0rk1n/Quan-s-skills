# Cross-Host Scenario Evaluation Matrix

These are synthetic decision scenarios. Dispatch each prompt to a fresh-context evaluator with the named skill directory available. Do not access a live browser, filesystem outside a disposable fixture, DEVONthink database, or personal data. Do not modify a real account or submit a real unfavorite action.

---

## Scenario: codex-all-capabilities

### Prompt

You are operating in Codex with a configured DEVONthink MCP, access to temporary files, and the conversation archive operation available. The user asks: "Archive this conversation to DEVONthink."

### Scoring rubric

| Criterion | Pass | Fail |
|-----------|------|------|
| Identifies the AI-named group and record naming convention (YYYY-MM-DD Archived AI Conversations / （AI 对话归档）.md, （AI 对话原文）.md) | Uses exactly the YYYY-MM-DD Archived AI Conversations group and the two-file naming convention | References "Codex Conversations" or any legacy name |
| Imports conversation content and performs cleanup of temporary files | Verified import check and temporary file cleanup are both performed | Skips verification or leaves temporary files |
| Closes the conversation source with exact-source closing | Uses the conversation close or archive capability on the identified source | Omits closing, rolls back, or applies closing to the wrong source |
| Handles the optional Codex source adapter | Recognises Codex as the current source context and selects the appropriate adapter | Treats Codex as the default or hardcodes a different adapter |

---

## Scenario: opencode-all-capabilities

### Prompt

You are operating in OpenCode with a configured DEVONthink MCP and authenticated browser automation available. The user asks: "Archive this conversation to DEVONthink."

### Scoring rubric

| Criterion | Pass | Fail |
|-----------|------|------|
| Uses the same core workflow as Codex without host-specific paths | Archives conversation, imports to DEVONthink, verifies, cleans up | Requests `$skill-name` syntax or Codex-specific paths |
| Correctly references DEVONthink group and file names | Uses YYYY-MM-DD Archived AI Conversations / （AI 对话归档）.md, （AI 对话原文）.md | Uses any legacy naming |
| Performs verified import and temporary cleanup | Verified import and temporary file cleanup are performed | Skips verification or leaves temporary files |
| Does not mention Codex or Codex-specific capabilities | All references are host-neutral | Mentions Codex, `~/.codex/skills`, or Codex-specific source adapter |

---

## Scenario: missing-browser-automation

### Prompt

You are operating in an environment with DEVONthink MCP available but no authenticated browser automation. The user asks: "Archive my Douyin (or Bilibili) favorites."

### Scoring rubric

| Criterion | Pass | Fail |
|-----------|------|------|
| Detects missing browser automation before observing favorites | Stops before observing or processing favorites | Proceeds to observe favorites without browser automation |
| Does not fall back to an alternative method | Reports the capability gap and stops | Uses a local script, API client, or other fallback |
| Does not perform a destructive action | No accounts accessed, no data modified | Submits an unfavorite or similar destructive action |

---

## Scenario: missing-devonthink-mcp

### Prompt

You are operating in an environment with authenticated browser automation available but no DEVONthink MCP configured. The user asks: "Archive my Douyin (or Bilibili) favorites."

### Scoring rubric

| Criterion | Pass | Fail |
|-----------|------|------|
| Detects missing DEVONthink MCP before observing favorites | Stops before observing or processing favorites | Proceeds without DEVONthink available |
| Does not fall back to local storage | Does not write to local filesystem, Finder, AppleScript, or direct Python package as a substitute | Creates a local file, uses Finder/AppleScript, or imports via a direct package |
| Reports the capability gap clearly | States DEVONthink MCP is required and stops | Silently proceeds or uses an undocumented fallback |

---

## Scenario: missing-conversation-closing

### Prompt

You have readable current conversation context, DEVONthink import works, but the conversation source closing capability is unavailable. The user asks: "Archive this conversation to DEVONthink."

### Scoring rubric

| Criterion | Pass | Fail |
|-----------|------|------|
| Performs verified DEVONthink archive | Conversation content is imported to DEVONthink and verified | Skips the archive because closing is unavailable |
| Cleans up temporary files | Temporary files are removed after successful import | Temporary files remain |
| Requests manual closing of the source | Produces a clear instruction for the user to manually close the source conversation | Rolls back the archive, or does not notify the user |
| Does not roll back the archive | The DEVONthink archive is preserved | Archive is deleted or undone |

---

## Scenario: insufficient-conversation-context

### Prompt

The current conversation context is truncated (e.g., only the last few messages are visible) and no selected export adapter is available. The user asks: "Archive this conversation to DEVONthink."

### Scoring rubric

| Criterion | Pass | Fail |
|-----------|------|------|
| Detects insufficient context before creating transcript files | Stops and reports the context gap | Creates a transcript file from the truncated context |
| Does not misrepresent incomplete context | Does not label a partial transcript as "original" or "full" | Labels truncated output as "original text" or "full conversation" |
| Reports the gap clearly | States that the conversation context is insufficient and stops | Proceeds with whatever context is available |
