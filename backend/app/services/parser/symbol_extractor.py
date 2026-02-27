from app.models.symbol import Symbol


FUNCTION_NODES = {
    "function_definition",
    "function_declaration",
    "method_definition",
}

CLASS_NODES = {
    "class_definition",
    "class_declaration",
}


def extract_symbols(tree, file_model, source_code, db):
    root = tree.root_node
    lines = source_code.splitlines()

    def traverse(node):
        if node.type in FUNCTION_NODES:
            name = extract_identifier(node, lines)

            db.add(Symbol(
                file_id=file_model.id,
                name=name,
                type="function",
                start_line=node.start_point[0],
                end_line=node.end_point[0],
            ))

        elif node.type in CLASS_NODES:
            name = extract_identifier(node, lines)

            db.add(Symbol(
                file_id=file_model.id,
                name=name,
                type="class",
                start_line=node.start_point[0],
                end_line=node.end_point[0],
            ))

        for child in node.children:
            traverse(child)

    traverse(root)


def extract_identifier(node, lines):
    for child in node.children:
        if child.type == "identifier":
            return lines[child.start_point[0]][
                child.start_point[1]:child.end_point[1]
            ]
    return "anonymous"