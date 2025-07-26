"""Extra tests for edge cases and coverage in ast_utils and types."""
import pytest
from quantalogic_markdown_mcp.types import ParseError, ParseResult, ErrorLevel
from quantalogic_markdown_mcp.ast_utils import ASTWrapper, extract_text_content, get_headings, find_tokens_by_type, create_syntax_tree

class DummyAST:
    def __str__(self):
        return "dummy"


def test_parseerror_str_variants():
    # No line/col
    e1 = ParseError("msg")
    assert "msg" in str(e1)
    # With line
    e2 = ParseError("msg", line_number=2)
    assert "Line 2" in str(e2)
    # With line/col
    e3 = ParseError("msg", line_number=2, column_number=5)
    assert "Line 2, Column 5" in str(e3)


def test_parseresult_add_error():
    pr = ParseResult(ast=[], errors=[], warnings=[], metadata={}, source_text="")
    pr.add_error("err1", level=ErrorLevel.ERROR)
    pr.add_error("warn1", level=ErrorLevel.WARNING)
    assert any("err1" in str(e) for e in pr.errors)
    assert any("warn1" in str(w) for w in pr.warnings)


def test_astwrapper_nonlist_ast():
    dummy = DummyAST()
    pr = ParseResult(ast=dummy, errors=[], warnings=[], metadata={}, source_text="")
    w = ASTWrapper(pr)
    assert "dummy" in w.to_json()
    assert w.get_headings() == []
    assert w.get_text_content() == "dummy"
    assert w.find_tokens("text") == []
    assert w.create_tree() is None


def test_extract_text_content_empty():
    assert extract_text_content([]) == ""


def test_get_headings_empty():
    assert get_headings([]) == []


def test_find_tokens_by_type_empty():
    assert find_tokens_by_type([], "text") == []


def test_create_syntax_tree_empty():
    # Should not error on empty
    tree = create_syntax_tree([])
    assert tree is not None
