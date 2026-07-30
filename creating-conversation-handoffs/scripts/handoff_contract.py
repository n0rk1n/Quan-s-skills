from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Final, NamedTuple


REQUIRED_SECTIONS: Final = (
    "元数据",
    "续接摘要",
    "用户目标与验收标准",
    "必须了解的背景",
    "相对上次交接的变化",
    "事实与证据",
    "已完成事项",
    "当前工作区状态",
    "决策与理由",
    "失败尝试与避坑点",
    "未完成事项与下一步",
    "阻塞项与待确认问题",
    "关键文件、命令与外部资源",
    "来源信息与回查",
    "新对话续接指令",
)
METADATA_KEYS: Final = (
    "Schema 版本",
    "生成时间",
    "任务摘要",
    "旧对话 UUID",
    "项目或 worktree 根目录",
    "上一个快照",
)
VALID_FACT_STATES: Final = frozenset({"已验证", "用户确认", "待核实"})
SNAPSHOT_NAME: Final = re.compile(
    r"^\d{4}-\d{2}-\d{2}-\d{4}-[a-z0-9]+"
    r"(?:-[a-z0-9]+)*(?:-\d{2})?\.md$"
)
TIMESTAMP: Final = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}$")
TOPIC_SLUG: Final = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TEMPLATE_TOKEN: Final = re.compile(r"\{\{[a-z][a-z0-9_]*\}\}")
POSSIBLE_SECRET: Final = re.compile(
    r"(?i)\b(?:password|passwd|token|secret|api[_-]?(?:key|token))\b"
    r"\s*[:=：]\s*(?!<redacted>|已省略|环境变量)\S+"
)
LATEST_LINK: Final = re.compile(r"^- 最新快照：\[[^\]]+\]\(([^)]+)\)$", re.MULTILINE)
METADATA_LINE: Final = re.compile(
    r"^- (Schema 版本|生成时间|任务摘要|旧对话 UUID|"
    r"项目或 worktree 根目录|上一个快照)[：:](.+)$",
    re.MULTILINE,
)


class ValidationIssue(NamedTuple):
    code: str
    message: str


def _read_regular_file(path: Path) -> tuple[str, list[ValidationIssue]]:
    if not path.exists():
        return "", [ValidationIssue("missing-file", f"{path} does not exist")]
    if not path.is_file():
        return "", [ValidationIssue("not-regular-file", f"{path} is not a file")]
    try:
        return path.read_text(encoding="utf-8"), []
    except UnicodeDecodeError as error:
        return "", [ValidationIssue("invalid-utf8", str(error))]
    except OSError as error:
        return "", [ValidationIssue("read-failed", str(error))]


def _metadata(text: str) -> dict[str, str]:
    return {key: value.strip() for key, value in METADATA_LINE.findall(text)}


def _section(text: str, name: str) -> str:
    match = re.search(
        rf"^## {re.escape(name)}\n(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return "" if match is None else match.group(1)


def _valid_source_uuid(value: str) -> bool:
    if re.fullmatch(r"不可用：\S.+", value):
        return True
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def _section_issues(text: str) -> list[ValidationIssue]:
    headings = re.findall(r"^## (.+)$", text, re.MULTILINE)
    missing = [name for name in REQUIRED_SECTIONS if name not in headings]
    if missing:
        return [
            ValidationIssue("missing-section", f"missing section: {name}")
            for name in missing
        ]
    positions = [headings.index(name) for name in REQUIRED_SECTIONS]
    if positions != sorted(positions):
        return [
            ValidationIssue(
                "section-order",
                "required sections are not in the contract order",
            )
        ]
    unexpected = [name for name in headings if name not in REQUIRED_SECTIONS]
    return [
        ValidationIssue(
            "unexpected-section",
            f"unexpected level-two section: {name}",
        )
        for name in unexpected
    ]


def _metadata_issues(text: str) -> list[ValidationIssue]:
    values = _metadata(text)
    issues = [
        ValidationIssue("missing-metadata", f"missing metadata: {key}")
        for key in METADATA_KEYS
        if not values.get(key)
    ]
    if values.get("Schema 版本") not in {None, "1"}:
        issues.append(
            ValidationIssue("unsupported-schema", "Schema 版本 must be 1")
        )
    source_uuid = values.get("旧对话 UUID")
    if source_uuid and not _valid_source_uuid(source_uuid):
        issues.append(
            ValidationIssue(
                "invalid-source-uuid",
                "旧对话 UUID must be a UUID or 不可用：<原因>",
            )
        )
    return issues


def _fact_issues(text: str) -> list[ValidationIssue]:
    facts = _section(text, "事实与证据")
    states: list[str] = []
    for line in facts.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.split("|")[1:-1]]
        if not cells or cells[0] in {"状态", "---"}:
            continue
        states.append(cells[0])
    if not states:
        return [
            ValidationIssue("missing-fact-row", "事实与证据 has no fact rows")
        ]
    return [
        ValidationIssue("invalid-fact-status", f"invalid fact status: {state}")
        for state in states
        if state not in VALID_FACT_STATES
    ]


def validate_snapshot(path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if SNAPSHOT_NAME.fullmatch(path.name) is None:
        issues.append(
            ValidationIssue(
                "invalid-snapshot-name",
                "snapshot name must match YYYY-MM-DD-HHmm-<topic-slug>.md",
            )
        )
    text, read_issues = _read_regular_file(path)
    if read_issues:
        return [*issues, *read_issues]
    issues.extend(_section_issues(text))
    issues.extend(_metadata_issues(text))
    issues.extend(_fact_issues(text))
    if "**首个可执行步骤：**" not in text:
        issues.append(
            ValidationIssue(
                "missing-first-step",
                "missing **首个可执行步骤：** marker",
            )
        )
    if TEMPLATE_TOKEN.search(text):
        issues.append(
            ValidationIssue(
                "unresolved-template-token",
                "snapshot contains an unresolved template token",
            )
        )
    if POSSIBLE_SECRET.search(text):
        issues.append(
            ValidationIssue(
                "possible-secret",
                "snapshot contains a possible secret assignment",
            )
        )
    return issues


def validate_latest(path: Path) -> list[ValidationIssue]:
    text, issues = _read_regular_file(path)
    if issues:
        return issues
    links = LATEST_LINK.findall(text)
    if len(links) != 1:
        return [
            ValidationIssue(
                "invalid-latest-link",
                "LATEST.md must contain exactly one latest snapshot link",
            )
        ]
    target = Path(links[0])
    if target.is_absolute():
        return [
            ValidationIssue(
                "absolute-latest-target",
                "latest snapshot target must be relative",
            )
        ]
    if ".." in target.parts:
        return [
            ValidationIssue(
                "escaping-latest-target",
                "latest snapshot target cannot contain ..",
            )
        ]
    if target.name == "LATEST.md":
        return [
            ValidationIssue(
                "self-referencing-latest",
                "LATEST.md cannot reference itself",
            )
        ]
    directory = path.parent.resolve()
    candidate = path.parent / target
    if not candidate.resolve().is_relative_to(directory):
        return [
            ValidationIssue(
                "escaping-latest-target",
                "latest snapshot target escapes the handoff directory",
            )
        ]
    if not candidate.exists() or not candidate.is_file():
        return [
            ValidationIssue(
                "missing-latest-target",
                "latest snapshot target does not exist",
            )
        ]
    return validate_snapshot(candidate)


def next_snapshot_path(
    directory: Path,
    timestamp: str,
    topic_slug: str,
) -> Path:
    if TIMESTAMP.fullmatch(timestamp) is None:
        raise ValueError("timestamp must be YYYY-MM-DD-HHmm")
    if TOPIC_SLUG.fullmatch(topic_slug) is None:
        raise ValueError("topic must be a lowercase slug")
    base = directory / f"{timestamp}-{topic_slug}.md"
    if not base.exists():
        return base
    sequence = 2
    while True:
        candidate = directory / f"{timestamp}-{topic_slug}-{sequence:02d}.md"
        if not candidate.exists():
            return candidate
        sequence += 1
