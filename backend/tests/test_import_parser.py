import pytest

from app.services.graph.import_parser import parse_import


def test_parse_python_from_import():
    ref = parse_import("from app.services.auth import routes", "app/main.py")
    assert ref.module == "app.services.auth"
    assert "routes" in ref.names


def test_parse_python_relative_import():
    ref = parse_import("from .utils import helper", "app/main.py")
    assert ref.is_relative is True


def test_parse_js_relative():
    ref = parse_import("import utils from './utils'", "src/main.ts")
    assert ref.is_relative is True
