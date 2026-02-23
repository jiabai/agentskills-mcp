import re
from typing import Set

ALLOWED_COMMANDS: Set[str] = {
    "python",
    "python3",
    "node",
    "npm",
    "bash",
    "sh",
}

BLOCKED_PATTERNS: list[str] = [
    r"rm\s+-rf",
    r"sudo",
    r">\s*/etc/",
    r"curl.*\|.*bash",
    r"wget.*\|.*sh",
    r"\.\./",
]


def validate_command(command: str) -> tuple[bool, str]:
    cmd_parts = command.split()
    if not cmd_parts:
        return False, "Empty command"

    base_cmd = cmd_parts[0].split("/")[-1].split("\\")[-1]
    if base_cmd not in ALLOWED_COMMANDS:
        return False, f"Command '{base_cmd}' is not allowed"

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Command contains blocked pattern: {pattern}"

    return True, "OK"
