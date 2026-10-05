"""화면·내레이션에 나갈 텍스트에서 비밀정보를 **** 로 가린다.

python mask.py <파일...>  → 가려질 항목을 찾아 목록만 출력 (QA용)
"""

import re
import sys

PATTERNS = [
    ("api_key", re.compile(r"\b(sk-(?:proj-|ant-)?[A-Za-z0-9_\-]{16,})")),
    ("github_token", re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("google_key", re.compile(r"\b(AIza[0-9A-Za-z_\-]{30,})")),
    ("aws_key", re.compile(r"\b(AKIA[0-9A-Z]{16})")),
    ("slack_token", re.compile(r"\b(xox[abpr]-[A-Za-z0-9\-]{10,})")),
    ("jwt", re.compile(r"\b(eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,})")),
    ("bearer", re.compile(r"(?i)\bbearer\s+([A-Za-z0-9._\-]{16,})")),
    ("private_key", re.compile(r"(-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----)")),
    # KEY=값, "password": "값" 형태 (.env / 설정)
    ("env_secret", re.compile(
        r"(?i)\b[A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|PWD|CREDENTIAL)[A-Z0-9_]*\s*[:=]\s*[\"']?([^\s\"',}]{4,})")),
    ("email", re.compile(r"\b([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})\b")),
]

# 공개해도 되는 이메일 (예시·noreply)
EMAIL_ALLOW = re.compile(r"(?i)(noreply|no-reply|example\.(com|org)|users\.noreply\.github\.com)")
# KEY=값 에서 값이 비밀이 아닌 경우: 환경변수 이름(대문자_), 코드 참조, 자리표시자
NOT_SECRET_VALUE = re.compile(
    r"^(os\.|process\.env|getenv|env\(|\$|<|\{|your|xxx|none|null|true|false|str|int|\.\.\.)",
    re.IGNORECASE)


def _is_secret(name: str, val: str) -> bool:
    if name == "email":
        return not EMAIL_ALLOW.search(val)
    if name == "env_secret":
        is_code_ref = re.match(r"[A-Za-z_][\w.]*\(", val)  # credentials.Certificate(...) 같은 코드
        return not (re.fullmatch(r"[A-Z][A-Z0-9_]*", val) or NOT_SECRET_VALUE.match(val) or is_code_ref)
    return True


def find_secrets(text: str) -> list[tuple[str, str]]:
    return [(name, m.group(1)) for name, pat in PATTERNS for m in pat.finditer(text)
            if _is_secret(name, m.group(1))]


def mask_text(text: str) -> str:
    """매치된 위치의 값만 가린다 (같은 문자열이 다른 곳에 있어도 건드리지 않음)."""
    for name, pat in PATTERNS:
        def repl(m, name=name):
            val = m.group(1)
            if not _is_secret(name, val):
                return m.group(0)
            s, e = m.span(1)
            base = m.start(0)
            return m.group(0)[: s - base] + "****" + m.group(0)[e - base:]
        text = pat.sub(repl, text)
    return text


if __name__ == "__main__":
    hits = 0
    for path in sys.argv[1:]:
        with open(path, encoding="utf-8", errors="replace") as f:
            for name, val in find_secrets(f.read()):
                hits += 1
                print(f"{path}: [{name}] {val[:6]}…")
    print(f"비밀정보 후보 {hits}건")
