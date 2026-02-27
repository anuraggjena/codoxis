from tree_sitter import Parser
from tree_sitter_language_pack import get_language


SUPPORTED_LANGUAGES = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "tsx": "tsx",
    "html": "html",
    "css": "css",
}


def get_parser_for_extension(ext: str):
    if ext not in SUPPORTED_LANGUAGES:
        return None

    language_name = SUPPORTED_LANGUAGES[ext]
    language = get_language(language_name)

    return Parser(language)