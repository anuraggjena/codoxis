from app.models.symbol import Symbol


# --- Node Type Groups ---

FUNCTION_NODES = {
    "function_definition",     # Python
    "function_declaration",    # JS/TS
    "method_definition",       # JS/TS
}

CLASS_NODES = {
    "class_definition",        # Python
    "class_declaration",       # JS/TS
}

IMPORT_NODES = {
    "import_statement",        # Python + JS
    "import_from_statement",   # Python
}

CALL_NODES = {
    "call",                    # Python
    "call_expression",         # JS/TS
}


# --- Main Extraction Function ---

def extract_symbols(tree, file_model, source_code, db):
    root = tree.root_node
    lines = source_code.splitlines()

    def traverse(node):
        # --- Functions ---
        if node.type in FUNCTION_NODES:
            name = extract_identifier(node, lines)

            if name:
                db.add(Symbol(
                    file_id=file_model.id,
                    name=name,
                    type="function",
                    start_line=node.start_point[0],
                    end_line=node.end_point[0],
                ))

        # --- Classes ---
        elif node.type in CLASS_NODES:
            name = extract_identifier(node, lines)

            if name:
                db.add(Symbol(
                    file_id=file_model.id,
                    name=name,
                    type="class",
                    start_line=node.start_point[0],
                    end_line=node.end_point[0],
                ))

        # --- Imports ---
        elif node.type in IMPORT_NODES:
            import_name = extract_import_text(node, lines)

            if import_name:
                db.add(Symbol(
                    file_id=file_model.id,
                    name=import_name,
                    type="import",
                    start_line=node.start_point[0],
                    end_line=node.end_point[0],
                ))

        # --- Function Calls ---
        elif node.type in CALL_NODES:
            call_name = extract_identifier(node, lines)

            if call_name:
                db.add(Symbol(
                    file_id=file_model.id,
                    name=call_name,
                    type="call",
                    start_line=node.start_point[0],
                    end_line=node.end_point[0],
                ))

        # Recursive traversal
        for child in node.children:
            traverse(child)

    traverse(root)


# --- Helper: Extract Identifier ---

def extract_identifier(node, lines):
    """
    Extract identifier from a node.
    Works for functions, classes, and calls.
    """
    for child in node.children:
        if child.type == "identifier":
            return safe_slice(lines, child)

    return None


# --- Helper: Extract Import Text ---

def extract_import_text(node, lines):
    """
    For now, store raw import line.
    We will refine resolution later.
    """
    try:
        return lines[node.start_point[0]].strip()
    except Exception:
        return None


# --- Safe Slice Utility ---

def safe_slice(lines, node):
    try:
        line = lines[node.start_point[0]]
        return line[node.start_point[1]:node.end_point[1]]
    except Exception:
        return None