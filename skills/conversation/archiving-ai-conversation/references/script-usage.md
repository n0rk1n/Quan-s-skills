# Script input and commands

Requires Python 3.10+ on macOS/Linux. No external Python libraries are needed. Git CLI is required when `artifacts` is nonempty.

```bash
python3 "$SKILL_DIR/scripts/archive_conversation.py" preflight
python3 "$SKILL_DIR/scripts/archive_conversation.py" save --input <archive-input.json>
```

Without `--input`, `save` reads JSON from stdin. Default destination: the current user's `~/Downloads`. `--downloads-dir <absolute-path>` selects an explicitly requested destination, the actual Downloads directory on another host, or a test fixture. The directory must already exist and be readable/writable. The dated child directory is created by the script.

## JSON input

```json
{
  "title": "修复归档链接",
  "messages": [
    {"role": "user", "content": "请修复原文链接。"},
    {"role": "assistant", "content": "已修复链接，并核对目标文件。"}
  ],
  "artifacts": [],
  "sops": [],
  "retrospective": {
    "背景": "原文链接无法打开。",
    "处理过程": "修正链接编码并回读核对。",
    "结果": "链接可以定位到对应原文。",
    "决策": "使用同目录相对链接。",
    "经验教训": "文件名中的特殊字符需要编码。",
    "疑难问题": "无。",
    "后续事项": "无。"
  }
}
```

Use actual conversation content, never copy this example as an archive. Include metrics, estimates, evidence anchors, and follow-ups in the appropriate sections. The seven retrospective keys are required exactly as shown; use an honest “无” when a section does not apply. `原文记录` is generated automatically. Messages must use `user` or `assistant`; omit tool output and hidden reasoning. Each content value must be nonempty text. Embedded Markdown headings become level three; fenced code is preserved, and unclosed fences are rejected.

The script checks shape and storage. The model must still select the correct source, preserve useful wording, judge completeness, omit irrelevant large pastes, and verify the retrospective's accuracy.

## SOP input

Every new archive must explicitly supply `sops` after assessing the conversation. Classify candidates with `scope: "general"` or `scope: "archiving-ai-conversation"`. The latter covers this archiving skill's own use, configuration, implementation, repair, and maintenance; the script excludes these candidates before SOP rendering and records the exclusion. Use `[]` only when no candidates exist. Mixed conversations still produce SOPs for unrelated subjects. For older callers, an omitted field is accepted as an empty list; the script cannot judge whether the model overlooked an SOP.

Each eligible list item has a `title` (the SOP name, with the same restrictions as the archive title), `scope: "general"`, and `sections` containing exactly these five nonempty text fields. Excluded items need only `title` and `scope: "archiving-ai-conversation"`; do not draft their sections. Older callers may omit scope (defaults to general); invalid scopes are rejected. The model must classify the subject honestly; the script does not infer meaning from a title. Example item for a conversation that actually established this procedure:

```json
{
  "title": "数据报告交付校验",
  "scope": "general",
  "sections": {
    "目的与适用场景": "数据报告交付前，核对保存内容是否完整。",
    "前置条件与输入": "已生成的数据报告和对应的已保存文件。",
    "标准步骤或格式": "1. 按 UTF-8 回读每个文件。\n2. 将回读内容与生成内容逐一比较。\n3. 检查文档链接是否指向实际保存文件。",
    "输出与验收标准": "所有内容一致，所有链接指向正确文件后，才记录校验通过。",
    "异常处理与适用边界": "任一检查失败时保留已保存文件和源对话，报告失败路径；本检查不证明内容的事实准确性。"
  }
}
```

The writer generates the SOP title, five section headings, and encoded source link. Standard formats use a copyable template in `标准步骤或格式`; procedures use ordered steps. Label unverified proposals `待验证` and unknown details `待补充`. Each SOP has its own file; the retrospective's generated `SOP 文档` section links to each. An empty list generates `未发现可提炼的标准流程或标准格式。`. Excluded candidates instead generate an explicit archive-skill exclusion finding; `skipped_sops` returns their titles, including in mixed conversations.

## Produced-file input

Every new archive explicitly supplies `artifacts`: an array of absolute paths to actual files produced in the conversation, or `[]` when none exist. Omission remains accepted as `[]` for older callers. For example:

```json
{
  "artifacts": ["/absolute/path/report.pdf", "/absolute/path/figure.png"],
  "sops": [{"title": "归档技能维护", "scope": "archiving-ai-conversation"}]
}
```

This fragment extends the complete input above. The model identifies relevant deliverables, not their Git state. The writer checks each file's own repository index with literal Git pathspecs, including linked worktrees. Files tracked in the index (even modified or staged but uncommitted) are skipped; ignored/untracked and non-repository files are copied. Duplicate resolved paths are handled once. Directories, symlinks, missing files, relative paths, unreadable files, and failed Git checks are rejected, rather than silently omitted. Enumerate relevant files for directory deliverables; provide the actual regular file for a symlink.

After writing the conversation Markdown, the script copies eligible files into the same daily directory with exclusive creation and numeric collision suffixes, preserving bytes and extensions (very long basenames are shortened). It streams data and SHA-256 checks to avoid loading large files into memory. Source and destination must match the pre-copy size/hash. Sources remain in place and are never staged or committed. The script writes `YYYY-MM-DD <对话解决的问题>（文件清单）.json` and adds encoded relative links to copies and manifest in the retrospective. A manifest is created when any copied or Git-tracked candidate exists.

`artifacts` in the result and manifest contains objects with absolute `source`, absolute destination `path`, byte `size`, and `sha256`. `skipped_artifacts` contains `source`, `repository`, and `reason: "git-tracked"`. `artifact_manifest` is an absolute path or `null` when no files were supplied. `verified: true` covers all Markdown/JSON byte read-backs and artifact size/hash checks. The model still checks that every conversation deliverable was supplied and reviews source fidelity; this is not automated semantic discovery.

## Output and failure handling

Success exits 0 and prints a JSON object with `verified: true` and absolute `directory`, `transcript`, and `retrospective` paths. All 2 + N Markdown files, copied artifacts, and the optional manifest remain permanently. The `sops` output is an array of absolute paths, empty when none were supplied. The script never invokes a host archive/close operation.

Invalid data is rejected before creating the daily archive directory. Failures exit nonzero and print `verified: false` and `error`; failures during writing or verification also include the planned paths and artifact metadata (these do not imply successful copying). A path in an error response does not prove that its file exists. Preserve any partial files, inspect the paths, report the error, and leave the conversation active. Retry only after resolving the cause; retries create a new numbered pair rather than overwrite previous output.

If either final filename already exists, both new filenames use the same numeric suffix. A shared `.archive.lock` serializes this script's writers; exclusive file creation also prevents overwriting files created by other writers. Keep the lock file. Existing and partial archives are never automatically removed.

Preflight returns `writable: true` and the resolved Downloads path on success. It does not guarantee that later writes will succeed (for example, disk space or permissions may change).

SOP names are allocated independently under the same lock, including duplicate titles in one input. Existing files and dangling symlinks are treated as collisions. Every SOP participates in exclusive writing and exact byte read-back; any failure returns `verified: false` with all planned SOP paths and preserves partial output. Never close the conversation on partial success.

Artifact copies and the manifest share the archive lock and collision reservations with Markdown outputs. A copy, manifest write, or hash/read-back failure preserves partial output, returns nonzero with `verified: false`, and leaves conversation closing to the host; never close on that result. Resolve missing sources or failed checks before retrying.
