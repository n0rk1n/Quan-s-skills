# Cross-Host Skill Portability Design

## Purpose

Make the repository's three active skills use the same core workflow and safety behavior in Codex, OpenCode, and other compatible agent hosts. The skills will describe required capabilities instead of depending on one host's invocation syntax, tool names, conversation storage, or lifecycle API.

The three skills are:

- `archiving-to-devonthink`
- `archiving-douyin-favorites`
- `archiving-bilibili-favorites`

## Goals

- Keep each skill independently installable and understandable from its own directory.
- Preserve the existing archival and destructive-action safety gates.
- Allow Codex and OpenCode to execute the same core workflow when the required capabilities are available.
- Treat host-specific metadata and source parsers as optional adapters rather than core requirements.
- Document installation, invocation, capabilities, and failure behavior for Codex and OpenCode.

## Non-Goals

- Do not create separate Codex and OpenCode copies of each skill.
- Do not add a shared runtime or repository-level compatibility library.
- Do not add an OpenCode private-session parser.
- Do not migrate, rename, or merge existing DEVONthink archive groups.
- Do not provide local-file, AppleScript, Finder, or direct-database fallbacks for unavailable DEVONthink MCP operations.
- Do not weaken exact-ID checks or perform live destructive actions as automated tests.

## Architecture

Each skill remains a self-contained package with two conceptual layers:

1. The host-neutral core in `SKILL.md` and `references/workflow.md` defines purpose, required capabilities, safety invariants, data contracts, workflow, error handling, and completion criteria.
2. Optional host adapters provide presentation or source-specific support. Existing `agents/openai.yaml` files remain optional OpenAI/Codex metadata. The Codex and ChatGPT conversation parsers remain optional high-fidelity input adapters.

OpenCode must be able to understand and execute each skill from `SKILL.md` and files inside the skill directory without reading `agents/openai.yaml`.

The core instructions use semantic capability names rather than mandatory host-specific tool names:

- readable current conversation context;
- optional conversation close or archive operation;
- authenticated browser automation for the target website;
- DEVONthink MCP database, group, record, import, update, tag, and lookup operations as required by the workflow;
- safe temporary-file creation and command execution where transcript export is used.

Host-specific commands and tool names may appear as non-normative mapping examples. A skill must not assume that an example name exists.

## Capability Preflight

Every execution follows the same preflight:

1. Confirm that the user explicitly selected the skill and identify the requested target and scope. Explicit selection means naming or invoking the skill through the host's supported mechanism; it does not require Codex's `$skill-name` syntax.
2. Inspect the current host's available tools and context.
3. Map available tools to the skill's required semantic capabilities.
4. Stop before reading or changing external data when a required capability is missing.
5. Continue with the host-neutral workflow only after preflight succeeds.

Missing optional capabilities must follow the skill's documented degradation path. The agent must never claim an operation happened when the host cannot perform or verify it.

## Favorites Skills

### Required Capabilities

Both favorites skills require:

- an authenticated, automatable browser session for the target website;
- stable extraction and matching of content IDs and canonical URLs;
- the necessary DEVONthink MCP record operations;
- page reload and delayed verification after cleanup.

If browser automation or DEVONthink MCP is unavailable, the skill stops. It must not offer a reduced local archive or direct DEVONthink database access.

### Data Flow

The safety-preserving flow remains:

`read stable IDs and URLs in browser -> write DEVONthink records -> verify one-to-one mapping -> select only verified archived IDs -> inspect final scope and count -> unfavorite -> reload and verify -> write and verify summary`

The existing per-skill batch sizes, destination rules, record fields, and retry limits remain unchanged unless a portability change makes wording host-specific.

### Destructive-Action Contract

- Stable content IDs and canonical URLs are the sole cleanup identities.
- Card order, visible position, broad selection, and assumed page scope are not identities.
- The selected ID set must exactly equal the current verified submission set.
- The final dialog's action and count must match the submission set before confirmation.
- Any ID, URL, count, selection, or mapping mismatch stops cleanup.
- Partial success may retry only unresolved IDs from the same verified archive set, under the existing retry limit.
- Completed archive records remain valid if later cleanup fails; reporting must distinguish verified removals from unresolved IDs.

## Conversation Archive Skill

### Source Selection

For the current conversation, the preferred source is the readable context supplied by the host. The agent generates a faithful lightweight transcript from that context while applying the existing transcript rules.

Optional source adapters may provide higher-fidelity input:

- Codex local rollout or archive JSONL through the existing `codex` exporter mode;
- official ChatGPT exports through the existing `chatgpt` exporter mode.

Codex environment variables, indexes, and local session paths belong only to the optional Codex source path. They are not general prerequisites. No parser will be added for OpenCode's private storage format.

If neither the readable host context nor a selected export source can support a trustworthy original transcript, the skill stops and reports the limitation. It must not label a retrospective or reconstructed summary as the original transcript.

### Naming

New conversation archives use a host-neutral daily group:

```text
YYYY-MM-DD Archived AI Conversations
```

The two generated records use the same concise topic phrase:

```text
YYYY-MM-DD <对话解决的问题>（AI 对话归档）.md
YYYY-MM-DD <对话解决的问题>（AI 对话原文）.md
```

Existing `Archived Codex Conversations` groups and Codex-named records are historical data. The revised skill does not discover them for reuse, migrate them, rename them, or merge them into the new group.

### Data Flow

The conversation flow becomes:

`read current context or optional export source -> generate transcript and retrospective in a safe temporary directory -> import both into the host-neutral DEVONthink daily group -> verify both records and their parent -> delete only verified temporary outputs -> close or archive the source conversation when supported`

The transcript is imported before the retrospective so the retrospective can link to the imported transcript when DEVONthink exposes a usable record link.

### Conversation Closing

Conversation closing is an optional host capability and runs only after both imports, parent verification, and temporary-file cleanup succeed.

- If the host supports closing or archiving the exact source conversation, use that operation and verify or report its result.
- If the capability is unavailable, ask the user to close or archive the conversation manually.
- If the operation fails, keep the verified DEVONthink records, report partial completion, and request manual cleanup.
- Never close a different conversation or executor.

## Documentation and Metadata

The repository README will:

- describe the repository as a cross-host skills collection;
- list all three active skills;
- explain that each skill requires host capabilities, not a particular model;
- provide installation and invocation guidance for both Codex and OpenCode;
- explain required browser and DEVONthink MCP capabilities;
- identify `agents/openai.yaml` as optional OpenAI/Codex interface metadata.

The `agents/openai.yaml` files remain in place. Their prompts and display text will be updated where they present Codex-specific behavior as universal behavior. No speculative OpenCode-specific metadata format will be introduced.

## Error Handling

Errors are classified by stage:

- **Preflight failure:** Stop before external observation or mutation and report the missing capability.
- **Archive write or verification failure:** Preserve confirmed records, do not begin destructive cleanup, and report exact incomplete or ambiguous items.
- **Cleanup mismatch or failure:** Stop or apply the existing bounded retry procedure only to unresolved verified IDs; never expand the set.
- **Summary failure:** Preserve verified bookmarks and cleanup state, report partial completion, and do not claim full completion.
- **Conversation close failure:** Preserve verified DEVONthink imports, report that source cleanup remains incomplete, and request manual action.

Reports must separate verified facts, unresolved state, and unsupported host operations.

## Validation

Implementation validation will include:

- verify valid frontmatter and local references for all three skills;
- verify every skill remains complete when installed independently;
- search for Codex-specific terms and confirm they occur only in optional metadata, installation guidance, source adapters, or clearly labeled examples;
- confirm OpenCode can derive the complete workflow without `agents/openai.yaml`;
- confirm existing Codex and ChatGPT exporter behavior remains unchanged;
- review the following capability scenarios against each applicable workflow:
  - Codex with all required capabilities;
  - OpenCode with browser automation and DEVONthink MCP;
  - a host without browser automation;
  - a host without DEVONthink MCP;
  - a host without conversation closing;
  - a host whose current context is insufficient for a trustworthy transcript.

No automated test will submit a real unfavorite operation. Destructive safety is validated through contract review, exact-set invariants, and non-destructive scenario evaluation.

## Success Criteria

- The three skills no longer require Codex invocation syntax or Codex-only tools in their core workflows.
- OpenCode can use each skill unchanged when its configured tools satisfy the required capabilities.
- Codex-specific metadata and parsers continue to work as optional adapters.
- Missing capabilities lead to explicit safe stops or documented partial completion.
- Existing favorites safety behavior is preserved.
- New conversation archives use host-neutral group and record names without altering historical archives.
