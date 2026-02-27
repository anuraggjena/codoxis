from .language_loader import get_parser_for_extension
from .symbol_extractor import extract_symbols


def parse_file_content(file_model, content: str, db):
    parser = get_parser_for_extension(file_model.language)

    if not parser:
        return

    tree = parser.parse(bytes(content, "utf8"))

    extract_symbols(tree, file_model, content, db)