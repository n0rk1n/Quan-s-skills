# Script input and commands

Requires Python 3.10+ on macOS/Linux. No installation or external libraries are needed.

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

## Output and failure handling

Success exits 0 and prints a JSON object with `verified: true` and absolute `directory`, `transcript`, and `retrospective` paths. Both Markdown files remain permanently. The script never invokes a host archive/close operation.

Invalid data is rejected before creating the daily archive directory. Failures exit nonzero and print `verified: false` and `error`; failures during writing or verification also include the planned paths. A path in an error response does not prove that its file exists. Preserve any partial files, inspect the paths, report the error, and leave the conversation active. Retry only after resolving the cause; retries create a new numbered pair rather than overwrite previous output.

If either final filename already exists, both new filenames use the same numeric suffix. A shared `.archive.lock` serializes this script's writers; exclusive file creation also prevents overwriting files created by other writers. Keep the lock file. Existing and partial archives are never automatically removed.

Preflight returns `writable: true` and the resolved Downloads path on success. It does not guarantee that later writes will succeed (for example, disk space or permissions may change).
