"""Viewport-aware spell checking: tokenization + dictionary + user ignore list.

No Qt. Huge-file safe when callers only pass visible text slices.
Supports one or more dictionary languages (union lexicon).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Word tokens: letters including common Latin accents; skip pure numbers.
_WORD_RE = re.compile(
    r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ']*(?:'[A-Za-zÀ-ÖØ-öø-ÿ]+)?"
)

# Languages that get spell-check by default (prose). Code stays off unless forced.
SPELL_DEFAULT_ON: frozenset[str] = frozenset(
    {
        "plaintext",
        "text",
        "txt",
        "markdown",
        "md",
        "restructuredtext",
        "rst",
        "html",
        "xml",
        "json",
        "yaml",
        "yml",
        "toml",
        "ini",
        "cfg",
        "log",
        "csv",
    }
)

SUPPORTED_SPELL_LANGS: tuple[str, ...] = ("pt_BR", "en_US", "es_ES")


def _words(*parts: str) -> frozenset[str]:
    return frozenset(w.casefold() for w in " ".join(parts).split() if w)


# Embedded lexicons — product works without external packs.
_EMBEDDED: dict[str, frozenset[str]] = {
    "en_US": _words(
        "the a an and or but if in on at to for of is are was were be been being",
        "this that these those with from as by not no yes it its we you they he she",
        "have has had do does did will would can could should may might must",
        "about after all also any because before between both each few more most",
        "other some such than then there when where which who why how",
        "hello world text editor file open save find replace line column",
        "document window menu settings theme language spell check dictionary",
        "new close edit view help copy paste cut undo redo select all print",
        "search project folder workspace tab group color dark light mode",
        "please thanks thank you today tomorrow yesterday now here there",
        "people person time year day way thing man woman life child world",
        "work go come take make get know think see look want use find give",
        "tell work seem feel try leave call keep let begin show hear play run",
        "move like live believe hold bring happen write provide sit stand lose",
        "pay meet include continue set learn change lead understand watch follow",
        "stop create speak read allow add spend grow open walk win offer remember",
        "love consider appear buy wait serve die send expect build stay fall cut",
        "reach kill remain suggest raise pass sell require report decide pull",
        "good bad great little large small big high low long short early late",
        "young old right left same different next last first second important",
        "public private possible able free sure clear simple special complete",
        "magic editor code python java script type style format syntax error",
        "true false null none value key name path size version number string",
    ),
    "pt_BR": _words(
        "o a os as um uma uns umas e ou mas se em no na nos nas de do da dos das",
        "para por com sem sob sobre entre até apos antes quando onde qual quem",
        "como porque que não nao sim eu tu ele ela nos nós voces vocês eles elas",
        "ser estar ter haver fazer poder dever ir vir ver dar ficar parecer",
        "texto editor arquivo abrir salvar buscar substituir linha coluna",
        "documento janela menu configuracoes configurações tema idioma",
        "ortografia dicionario dicionário",
        "ola olá mundo correcao correção verificacao verificação palavra frase",
        "novo fechar editar exibir ajuda copiar colar recortar desfazer refazer",
        "selecionar tudo imprimir pesquisa projeto pasta espaco espaço trabalho",
        "aba grupo cor escuro claro modo por favor obrigado obrigada hoje amanha amanhã",
        "ontem agora aqui ali gente pessoa tempo ano dia forma coisa homem mulher",
        "vida filho filha trabalho ir vir tomar fazer saber pensar ver olhar querer",
        "usar achar dar dizer trabalhar parecer sentir tentar deixar chamar",
        "manter deixar comecar começar mostrar ouvir jogar correr mover gostar",
        "viver acreditar trazer acontecer escrever incluir continuar aprender",
        "mudar entender seguir parar criar falar ler permitir adicionar",
        "bom ruim grande pequeno alto baixo longo curto cedo tarde jovem velho",
        "certo esquerdo mesmo diferente proximo próximo ultimo último primeiro",
        "segundo importante publico público privado possivel possível capaz livre",
        "claro simples especial completo verdadeiro falso nulo valor chave nome",
        "caminho tamanho versao versão numero número string codigo código python",
        "este esta esse essa isto isso aquele aquela aqueles aquelas meu minha",
        "seu sua nosso nossa deles delas muito pouco mais menos bem mal ja já",
        "ainda tambem também sempre nunca talvez talvez porque pois logo entao então",
        "assim cada todo toda todos todas outro outra outros outras qualquer",
        "algum alguma alguns algumas nenhum nenhuma varios vários várias",
        "arquivo pastas sistema usuario usuário janelas abas menus botoes botões",
        "salvar saiu saia saem saida saída entrada erro aviso sucesso falha",
        "alteracoes alterações deseja descartar cancelar sim nao não",
    ),
    "es_ES": _words(
        "el la los las un una unos unas y o pero si en de del al a para por con",
        "sin sobre entre hasta despues después antes cuando donde cual quién como porque",
        "que no si sí yo tu tú el él ella nosotros vosotros ellos ellas",
        "ser estar tener hacer poder deber ir venir ver dar quedar parecer",
        "texto editor archivo abrir guardar buscar reemplazar linea línea columna",
        "documento ventana menu menú ajustes tema idioma ortografia diccionario",
        "hola mundo correccion corrección verificacion verificación palabra frase",
        "nuevo cerrar editar ver ayuda copiar pegar cortar deshacer rehacer",
        "seleccionar todo imprimir buscar proyecto carpeta espacio trabajo",
        "pestaña grupo color oscuro claro modo por favor gracias hoy manana mañana",
        "ayer ahora aqui aquí alli allí gente persona tiempo año dia día forma",
        "cosa hombre mujer vida hijo hija trabajo ir venir tomar hacer saber",
        "pensar ver mirar querer usar encontrar dar decir trabajar parecer",
        "sentir intentar dejar llamar mantener empezar mostrar oir oír jugar",
        "correr mover gustar vivir creer traer ocurrir escribir incluir continuar",
        "aprender cambiar entender seguir parar crear hablar leer permitir",
        "anadir añadir bueno malo grande pequeno pequeño alto bajo largo corto",
        "temprano tarde joven viejo derecho izquierdo mismo diferente proximo próximo",
        "ultimo último primero segundo importante publico público privado posible",
        "capaz libre claro simple especial completo verdadero falso nulo valor",
        "clave nombre ruta tamaño version versión numero número codigo código",
        "este esta ese esa esto eso aquel aquella aquellos aquellas mi tu su",
        "nuestro vuestra mucho poco mas más menos bien mal ya aun aún tambien también",
        "siempre nunca tal vez porque pues luego entonces asi así cada todo toda",
        "todos todas otro otra otros otras cualquier algun algún alguna algunos",
        "ningun ningún ninguna varios varias archivo carpetas sistema usuario",
        "guardar salir entrada error aviso exito éxito fallo cambios desea",
        "descartar cancelar si no sí",
    ),
}


@dataclass
class SpellHit:
    start: int  # char offset in the provided text
    end: int
    word: str


@dataclass
class SpellEngine:
    """Dictionary-backed checker with multi-language union + user ignore / add."""

    language: str = "pt_BR"  # primary (compat)
    languages: list[str] = field(default_factory=list)
    user_words: set[str] = field(default_factory=set)
    ignore_session: set[str] = field(default_factory=set)
    _lexicon: set[str] = field(default_factory=set, repr=False)

    def __post_init__(self) -> None:
        if not self.languages:
            self.languages = [self.language if self.language in _EMBEDDED else "en_US"]
        self.reload_lexicon()

    def active_languages(self) -> list[str]:
        langs = [x for x in self.languages if x in SUPPORTED_SPELL_LANGS]
        return langs or ["en_US"]

    def reload_lexicon(self, extra_path: Path | None = None) -> None:
        words: set[str] = set()
        for lang in self.active_languages():
            words |= set(_EMBEDDED.get(lang, _EMBEDDED["en_US"]))
        words |= {w.casefold() for w in self.user_words}
        if extra_path is not None and extra_path.is_file():
            try:
                raw = extra_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                raw = ""
            for line in raw.splitlines():
                w = line.strip()
                if w and not w.startswith("#"):
                    words.add(w.casefold())
        self._lexicon = words
        # Keep primary language in sync for status display
        if self.languages:
            self.language = self.languages[0]

    def set_language(self, language: str) -> None:
        lang = language if language in SUPPORTED_SPELL_LANGS else "en_US"
        self.language = lang
        self.languages = [lang]
        self.reload_lexicon()

    def set_languages(self, languages: list[str] | tuple[str, ...]) -> None:
        cleaned = [x for x in languages if x in SUPPORTED_SPELL_LANGS]
        self.languages = cleaned or ["en_US"]
        self.language = self.languages[0]
        self.reload_lexicon()

    def add_to_user_dict(self, word: str) -> None:
        w = word.strip()
        if not w:
            return
        self.user_words.add(w)
        self._lexicon.add(w.casefold())

    def ignore_word(self, word: str) -> None:
        w = word.strip()
        if w:
            self.ignore_session.add(w.casefold())

    def is_correct(self, word: str) -> bool:
        if not word:
            return True
        key = word.casefold()
        if key in self.ignore_session or key in self._lexicon:
            return True
        # Allow ALL-CAPS acronyms length <= 6
        if word.isupper() and 1 < len(word) <= 6:
            return True
        # Allow identifiers with digits (code-ish tokens)
        if any(ch.isdigit() for ch in word):
            return True
        # CamelCase / snake-ish mixed tokens
        return "_" in word or any(c.isupper() for c in word[1:])

    def check_text(self, text: str) -> list[SpellHit]:
        """Return misspelled word spans inside ``text`` (viewport slice)."""
        hits: list[SpellHit] = []
        for m in _WORD_RE.finditer(text):
            word = m.group(0)
            if not self.is_correct(word):
                hits.append(SpellHit(start=m.start(), end=m.end(), word=word))
        return hits

    def suggest(self, word: str, *, limit: int = 6) -> list[str]:
        """Return ranked spelling suggestions for a misspelled word.

        Uses a small edit-distance search over the active lexicon (fast for
        embedded dictionaries). Preserves initial capital of *word*.
        """
        w = (word or "").strip()
        if not w or self.is_correct(w):
            return []
        key = w.casefold()
        # Prefer same starting letter / similar length to keep this O(lexicon) cheap
        scored: list[tuple[int, str]] = []
        for cand in self._lexicon:
            if abs(len(cand) - len(key)) > 2:
                continue
            # Skip very short noise
            if len(cand) < 2:
                continue
            dist = _edit_distance_leq(key, cand, max_dist=2)
            if dist is None or dist == 0:
                continue
            # Same first letter is a mild boost (lower score)
            boost = 0 if (cand[:1] == key[:1]) else 1
            scored.append((dist * 10 + boost, cand))
        scored.sort(key=lambda t: (t[0], t[1]))
        out: list[str] = []
        seen: set[str] = set()
        for _score, cand in scored:
            if cand in seen:
                continue
            seen.add(cand)
            # Match capitalization of original
            if w[:1].isupper():
                disp = cand[:1].upper() + cand[1:]
            else:
                disp = cand
            out.append(disp)
            if len(out) >= limit:
                break
        return out


def _edit_distance_leq(a: str, b: str, *, max_dist: int) -> int | None:
    """Levenshtein distance if ≤ max_dist, else None (banded DP)."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if abs(la - lb) > max_dist:
        return None
    # Two-row DP with early abandon
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i] + [0] * lb
        row_min = i
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            cur[j] = min(
                prev[j] + 1,  # delete
                cur[j - 1] + 1,  # insert
                prev[j - 1] + cost,  # substitute
            )
            row_min = min(row_min, cur[j])
        if row_min > max_dist:
            return None
        prev = cur
    d = prev[lb]
    return d if d <= max_dist else None


def spell_enabled_for_language(language: str, *, user_override: bool | None = None) -> bool:
    """Default on for prose languages; off for code. ``user_override`` forces."""
    if user_override is not None:
        return user_override
    key = (language or "plaintext").strip().lower()
    return key in SPELL_DEFAULT_ON


def iter_words(text: str) -> list[tuple[int, int, str]]:
    """Return (start, end, word) for all word tokens."""
    return [(m.start(), m.end(), m.group(0)) for m in _WORD_RE.finditer(text)]
