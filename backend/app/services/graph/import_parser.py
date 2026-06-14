from dataclasses import dataclass, field
import re


@dataclass
class ImportRef:
    raw: str
    module: str | None = None
    names: list[str] = field(default_factory=list)
    is_relative: bool = False
    relative_segments: int = 0  # number of leading dots in "from .xxx import"
    relative_module: str | None = None  # remainder after dots, e.g. "utils" in "from .utils import x"


_JS_FROM_RE = re.compile(
    r"""import\s+(?:[\w*{}\s,]+\s+from\s+)?['"]([^'"]+)['"]"""
)
_JS_IMPORT_RE = re.compile(r"""import\s+['"]([^'"]+)['"]""")


def parse_import(raw: str, source_path: str) -> ImportRef | None:
    text = raw.strip().strip(";")
    if not text:
        return None

    if text.startswith("import ") and "from" not in text.split()[0:3]:
        # JS: import './x' or import "x"
        js_match = _JS_IMPORT_RE.search(text)
        if js_match:
            return _parse_js_path(js_match.group(1))

    if "from " in text and ("'" in text or '"' in text):
        js_match = _JS_FROM_RE.search(text)
        if js_match:
            return _parse_js_path(js_match.group(1))

    if text.startswith("from ") or text.startswith("import "):
        return _parse_python_import(text, source_path)

    if "./" in text or "../" in text:
        for token in text.replace(";", " ").replace(",", " ").split():
            if token.startswith("./") or token.startswith("../"):
                return ImportRef(raw=text, is_relative=True, relative_module=token)

    return ImportRef(raw=text)


def _parse_js_path(path: str) -> ImportRef:
    path = path.strip()
    if path.startswith("."):
        return ImportRef(raw=path, is_relative=True, relative_module=path)
    return ImportRef(raw=path, module=path)


def _parse_python_import(text: str, source_path: str) -> ImportRef:
    if text.startswith("from "):
        body = text[5:].split(" import ", 1)
        if len(body) != 2:
            return ImportRef(raw=text)
        module_part, names_part = body[0].strip(), body[1].strip()
        names = [n.strip() for n in names_part.replace("(", "").replace(")", "").split(",") if n.strip()]

        if module_part.startswith("."):
            dots = len(module_part) - len(module_part.lstrip("."))
            remainder = module_part[dots:].strip()
            return ImportRef(
                raw=text,
                is_relative=True,
                relative_segments=dots,
                relative_module=remainder or None,
                names=names,
            )

        return ImportRef(raw=text, module=module_part, names=names)

    # import a, b, c
    rest = text[7:].strip()
    modules = [m.strip().split(" as ")[0] for m in rest.split(",")]
    if len(modules) == 1:
        return ImportRef(raw=text, module=modules[0])
    return ImportRef(raw=text, module=modules[0], names=modules[1:])
