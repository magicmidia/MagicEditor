"""Regex highlight rules per language (pure — no Qt)."""

from __future__ import annotations

import re
from dataclasses import dataclass

# rule name -> used by UI for colors
TokenKind = str


@dataclass(frozen=True, slots=True)
class Rule:
    kind: TokenKind
    pattern: re.Pattern[str]
    # multipass capture group (0 = whole match)
    group: int = 0


def _compile(kind: str, pattern: str, flags: int = 0, group: int = 0) -> Rule:
    return Rule(kind=kind, pattern=re.compile(pattern, flags), group=group)


def rules_for(lang: str) -> list[Rule]:
    """Return ordered rules (later rules can overlap; first match wins in highlighters)."""
    common_string = [
        _compile("string", r'"""[\s\S]*?"""'),
        _compile("string", r"'''[\s\S]*?'''"),
        _compile("string", r'"(?:\\.|[^"\\])*"'),
        _compile("string", r"'(?:\\.|[^'\\])*'"),
        _compile("string", r"`(?:\\.|[^`\\])*`"),
    ]
    common_number = [
        _compile("number", r"\b(?:0[xX][0-9A-Fa-f]+|\d+\.?\d*(?:[eE][+-]?\d+)?)\b"),
    ]
    hash_comment = [_compile("comment", r"#.*?$", re.M)]
    line_slash = [_compile("comment", r"//.*?$", re.M)]
    block_c = [_compile("comment", r"/\*[\s\S]*?\*/")]

    if lang == "python":
        kws = (
            r"\b(?:False|None|True|and|as|assert|async|await|break|class|continue|"
            r"def|del|elif|else|except|finally|for|from|global|if|import|in|is|"
            r"lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b"
        )
        return [
            *hash_comment,
            *common_string,
            _compile("keyword", kws),
            _compile("decorator", r"@\w+(?:\.\w+)*"),
            *common_number,
        ]

    if lang in {"javascript", "typescript"}:
        kws = (
            r"\b(?:async|await|break|case|catch|class|const|continue|debugger|default|"
            r"delete|do|else|export|extends|finally|for|from|function|if|import|in|"
            r"instanceof|let|new|of|return|static|super|switch|this|throw|try|typeof|"
            r"var|void|while|with|yield|enum|interface|type|implements|private|public|"
            r"protected|readonly|namespace)\b"
        )
        return [*block_c, *line_slash, *common_string, _compile("keyword", kws), *common_number]

    if lang == "json":
        return [
            _compile("string", r'"(?:\\.|[^"\\])*"'),
            _compile("number", r"\b(?:-?\d+\.?\d*(?:[eE][+-]?\d+)?|true|false|null)\b"),
        ]

    if lang == "markdown":
        return [
            _compile("heading", r"^#{1,6}\s+.*$", re.M),
            _compile("code", r"```[\s\S]*?```"),
            _compile("code", r"`[^`\n]+`"),
            _compile("string", r"\*\*[^*]+\*\*|__[^_]+__"),
            _compile("keyword", r"^\s*[-*+]\s+", re.M),
            _compile("link", r"\[[^\]]+\]\([^)]+\)"),
        ]

    if lang in {"html", "xml"}:
        return [
            _compile("comment", r"<!--[\s\S]*?-->"),
            _compile("keyword", r"</?[A-Za-z][\w:-]*"),
            _compile("string", r'"(?:\\.|[^"\\])*"'),
            _compile("string", r"'(?:\\.|[^'\\])*'"),
        ]

    if lang == "css":
        return [
            *block_c,
            _compile("keyword", r"@[\w-]+"),
            _compile("string", r'"(?:\\.|[^"\\])*"'),
            _compile("string", r"'(?:\\.|[^'\\])*'"),
            _compile("number", r"\b\d+\.?\d*(?:px|em|rem|%|vh|vw|s|ms)?\b"),
        ]

    if lang == "sql":
        kws = (
            r"\b(?:SELECT|FROM|WHERE|AND|OR|NOT|INSERT|INTO|VALUES|UPDATE|SET|DELETE|"
            r"CREATE|TABLE|DROP|ALTER|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AS|ORDER|BY|"
            r"GROUP|HAVING|LIMIT|OFFSET|DISTINCT|NULL|TRUE|FALSE|CASE|WHEN|THEN|"
            r"ELSE|END|UNION|ALL|IN|IS|LIKE|BETWEEN|EXISTS|PRIMARY|KEY|FOREIGN|"
            r"REFERENCES|INDEX|VIEW|WITH)\b"
        )
        return [
            _compile("comment", r"--.*?$", re.M),
            *block_c,
            _compile("string", r"'(?:''|[^'])*'"),
            _compile("keyword", kws, re.I),
            *common_number,
        ]

    if lang in {"c", "cpp", "csharp", "java", "go", "rust", "php"}:
        kws_map = {
            "c": r"\b(?:auto|break|case|char|const|continue|default|do|double|else|enum|"
            r"extern|float|for|goto|if|inline|int|long|register|restrict|return|"
            r"short|signed|sizeof|static|struct|switch|typedef|union|unsigned|void|"
            r"volatile|while)\b",
            "cpp": r"\b(?:alignas|alignof|and|and_eq|asm|auto|bitand|bitor|bool|break|"
            r"case|catch|char|class|compl|concept|const|consteval|constexpr|constinit|"
            r"const_cast|continue|co_await|co_return|co_yield|decltype|default|delete|"
            r"do|double|dynamic_cast|else|enum|explicit|export|extern|false|float|for|"
            r"friend|goto|if|inline|int|long|mutable|namespace|new|noexcept|not|not_eq|"
            r"nullptr|operator|or|or_eq|private|protected|public|register|reinterpret_cast|"
            r"requires|return|short|signed|sizeof|static|static_assert|static_cast|struct|"
            r"switch|template|this|thread_local|throw|true|try|typedef|typeid|typename|"
            r"union|unsigned|using|virtual|void|volatile|wchar_t|while|xor|xor_eq)\b",
            "csharp": r"\b(?:abstract|as|base|bool|break|byte|case|catch|char|checked|class|"
            r"const|continue|decimal|default|delegate|do|double|else|enum|event|explicit|"
            r"extern|false|finally|fixed|float|for|foreach|goto|if|implicit|in|int|"
            r"interface|internal|is|lock|long|namespace|new|null|object|operator|out|"
            r"override|params|private|protected|public|readonly|ref|return|sbyte|sealed|"
            r"short|sizeof|stackalloc|static|string|struct|switch|this|throw|true|try|"
            r"typeof|uint|ulong|unchecked|unsafe|ushort|using|virtual|void|volatile|while|"
            r"async|await|var|dynamic|nameof|record)\b",
            "java": r"\b(?:abstract|assert|boolean|break|byte|case|catch|char|class|const|"
            r"continue|default|do|double|else|enum|extends|final|finally|float|for|goto|"
            r"if|implements|import|instanceof|int|interface|long|native|new|package|"
            r"private|protected|public|return|short|static|strictfp|super|switch|"
            r"synchronized|this|throw|throws|transient|try|void|volatile|while|var|"
            r"yield|record|sealed|permits|non-sealed)\b",
            "go": r"\b(?:break|case|chan|const|continue|default|defer|else|fallthrough|for|"
            r"func|go|goto|if|import|interface|map|package|range|return|select|struct|"
            r"switch|type|var)\b",
            "rust": r"\b(?:as|async|await|break|const|continue|crate|dyn|else|enum|extern|"
            r"false|fn|for|if|impl|in|let|loop|match|mod|move|mut|pub|ref|return|self|"
            r"Self|static|struct|super|trait|true|type|unsafe|use|where|while)\b",
            "php": r"\b(?:abstract|and|array|as|break|callable|case|catch|class|clone|const|"
            r"continue|declare|default|do|echo|else|elseif|empty|enddeclare|endfor|"
            r"endforeach|endif|endswitch|endwhile|eval|exit|extends|final|finally|fn|for|"
            r"foreach|function|global|goto|if|implements|include|include_once|instanceof|"
            r"insteadof|interface|isset|list|match|namespace|new|or|print|private|protected|"
            r"public|require|require_once|return|static|switch|throw|trait|try|unset|use|"
            r"var|while|xor|yield)\b",
        }
        return [
            *block_c,
            *line_slash,
            *common_string,
            _compile("keyword", kws_map[lang]),
            *common_number,
        ]

    if lang in {"shell", "powershell", "yaml", "toml", "ini", "ruby", "dockerfile", "makefile", "batch", "cmake"}:
        return [
            *hash_comment,
            *common_string,
            *common_number,
            _compile(
                "keyword",
                r"\b(?:if|then|else|fi|for|while|do|done|case|esac|function|return|"
                r"export|local|true|false|null|FROM|RUN|CMD|COPY|ADD|ENV|WORKDIR|"
                r"ENTRYPOINT|ARG|VOLUME|EXPOSE|USER|ONBUILD)\b",
                re.I,
            ),
        ]

    if lang in {
        "kotlin",
        "swift",
        "dart",
        "lua",
        "r",
        "vue",
        "svelte",
        "graphql",
        "perl",
        "scala",
        "haskell",
        "elixir",
        "erlang",
        "clojure",
        "fsharp",
        "vb",
        "objectivec",
        "julia",
        "nim",
        "zig",
        "solidity",
        "terraform",
        "nginx",
        "apache",
        "diff",
        "git",
        "csv",
        "tsv",
        "properties",
        "env",
        "cmake",
    }:
        kws = (
            r"\b(?:fun|val|var|class|object|interface|if|else|when|for|while|return|"
            r"import|package|true|false|null|func|let|struct|enum|switch|case|"
            r"async|await|const|export|default|type|query|mutation|subscription|"
            r"function|local|end|then|do|repeat|until|library|require|module|"
            r"resource|provider|variable|output|fn|pub|use|match|impl|trait|"
            r"contract|pragma|mapping|address|uint|bytes|def|elif|lambda|"
            r"server|location|upstream|proxy_pass|Select|From|Where)\b"
        )
        return [
            *block_c,
            *line_slash,
            *hash_comment,
            *common_string,
            _compile("keyword", kws, re.I),
            *common_number,
        ]

    return [*hash_comment, *common_string, *common_number]


def tokenize_line(text: str, lang: str) -> list[tuple[int, int, TokenKind]]:
    """Return (start, length, kind) spans for a single line (or block text).

    Non-overlapping: first rule that claims a character wins.
    """
    rules = rules_for(lang)
    if not text or not rules:
        return []
    n = len(text)
    claimed = [False] * n
    spans: list[tuple[int, int, TokenKind]] = []

    for rule in rules:
        for m in rule.pattern.finditer(text):
            try:
                start, end = m.span(rule.group)
            except IndexError:
                start, end = m.span(0)
            if start >= end:
                continue
            if any(claimed[i] for i in range(start, min(end, n))):
                continue
            for i in range(start, min(end, n)):
                claimed[i] = True
            spans.append((start, end - start, rule.kind))

    spans.sort(key=lambda s: s[0])
    return spans
