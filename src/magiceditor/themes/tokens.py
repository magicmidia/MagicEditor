"""Chrome color tokens per theme (no Qt). Shared by dialogs and preview."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChromeTokens:
    fg: str
    muted: str
    heading: str
    bg: str
    surface: str
    accent: str
    link: str
    code_bg: str
    border: str


_DARK_DEFAULT = ChromeTokens(
    fg="#E5E2E1",
    muted="#999077",
    heading="#FFF6DF",
    bg="#0E0E0E",
    surface="#201F1F",
    accent="#FFD700",
    link="#82AAFF",
    code_bg="#2A2A2A",
    border="#3A3939",
)

TOKENS: dict[str, ChromeTokens] = {
    "luminous_void": _DARK_DEFAULT,
    "midnight_dark": ChromeTokens(
        fg="#E2E8F0",
        muted="#94A3B8",
        heading="#F1F5F9",
        bg="#0F172A",
        surface="#1E293B",
        accent="#22D3EE",
        link="#67E8F9",
        code_bg="#1E293B",
        border="#334155",
    ),
    "darcula": ChromeTokens(
        fg="#BBBBBB",
        muted="#878787",
        heading="#A9B7C6",
        bg="#2B2B2B",
        surface="#3C3F41",
        accent="#6897BB",
        link="#6897BB",
        code_bg="#313335",
        border="#555555",
    ),
    "cobalt_blue": ChromeTokens(
        fg="#FFFFFF",
        muted="#7BA3C9",
        heading="#FFFFFF",
        bg="#002240",
        surface="#001B33",
        accent="#FFCC00",
        link="#FFCC00",
        code_bg="#00315C",
        border="#0A4A80",
    ),
    "monokai_pro": ChromeTokens(
        fg="#FCFCFA",
        muted="#939293",
        heading="#FCFCFA",
        bg="#19181A",
        surface="#221F22",
        accent="#A9DC76",
        link="#78DCE8",
        code_bg="#2D2A2E",
        border="#5B595C",
    ),
    "clean_light": ChromeTokens(
        fg="#0F172A",
        muted="#64748B",
        heading="#0F172A",
        bg="#FFFFFF",
        surface="#FFFFFF",
        accent="#2563EB",
        link="#1D4ED8",
        code_bg="#F1F5F9",
        border="#E2E8F0",
    ),
    "tokyo_night": ChromeTokens(
        fg="#C0CAF5",
        muted="#565F89",
        heading="#C0CAF5",
        bg="#1A1B26",
        surface="#1F2335",
        accent="#7AA2F7",
        link="#7DCFFF",
        code_bg="#24283B",
        border="#292E42",
    ),
    "catppuccin_mocha": ChromeTokens(
        fg="#CDD6F4",
        muted="#6C7086",
        heading="#CDD6F4",
        bg="#1E1E2E",
        surface="#313244",
        accent="#CBA6F7",
        link="#89B4FA",
        code_bg="#313244",
        border="#45475A",
    ),
    "nord": ChromeTokens(
        fg="#ECEFF4",
        muted="#7B88A1",
        heading="#ECEFF4",
        bg="#2E3440",
        surface="#3B4252",
        accent="#88C0D0",
        link="#81A1C1",
        code_bg="#3B4252",
        border="#4C566A",
    ),
    "rose_pine": ChromeTokens(
        fg="#E0DEF4",
        muted="#6E6A86",
        heading="#E0DEF4",
        bg="#191724",
        surface="#1F1D2E",
        accent="#EBBCBA",
        link="#9CCFD8",
        code_bg="#26233A",
        border="#403D52",
    ),
    "gruvbox_dark": ChromeTokens(
        fg="#EBDBB2",
        muted="#928374",
        heading="#EBDBB2",
        bg="#282828",
        surface="#3C3836",
        accent="#FABD2F",
        link="#FABD2F",
        code_bg="#3C3836",
        border="#504945",
    ),
    "everforest": ChromeTokens(
        fg="#D3C6AA",
        muted="#859289",
        heading="#D3C6AA",
        bg="#2D353B",
        surface="#3D484D",
        accent="#A7C080",
        link="#A7C080",
        code_bg="#3D484D",
        border="#475258",
    ),
    "kanagawa": ChromeTokens(
        fg="#DCD7BA",
        muted="#727169",
        heading="#DCD7BA",
        bg="#1F1F28",
        surface="#2A2A37",
        accent="#7E9CD8",
        link="#7E9CD8",
        code_bg="#2A2A37",
        border="#363646",
    ),
    "solarized_light": ChromeTokens(
        fg="#52666D",
        muted="#93A1A1",
        heading="#073642",
        bg="#FDF6E3",
        surface="#EEE8D5",
        accent="#1666A3",
        link="#1666A3",
        code_bg="#EEE8D5",
        border="#DDD6C1",
    ),
}

LIGHT_THEMES: frozenset[str] = frozenset({"clean_light", "solarized_light"})


def is_light_theme(theme_id: str) -> bool:
    return theme_id in LIGHT_THEMES


def chrome_tokens(theme_id: str) -> ChromeTokens:
    return TOKENS.get(theme_id, _DARK_DEFAULT)
