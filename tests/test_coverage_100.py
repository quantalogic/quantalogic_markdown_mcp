"""Tests to reach 100% coverage for ast_utils and types."""
from quantalogic_markdown_mcp.types import ParseError, ParseResult, ErrorLevel, Renderer
from quantalogic_markdown_mcp.ast_utils import walk_tokens, get_headings
import pytest

class DummyRenderer(Renderer):
    def render(self, ast, options=None):
        return "dummy"
    def get_output_format(self):
        return "dummy"

def test_renderer_abstract_methods():
    r = DummyRenderer()
    assert r.render([], {}) == "dummy"
    assert r.get_output_format() == "dummy"

def test_walk_tokens_empty():
    # Should not fail on empty
    walk_tokens([], lambda t, i: None)

def test_walk_tokens_no_children():
    class T:
        children = None
    walk_tokens([T()], lambda t, i: None)

def test_get_headings_malformed():
    # Token missing tag
    class T:
        type = 'heading_open'
        tag = ''
        map = None
    class T2:
        type = 'inline'
        content = 'abc'
    class T3:
        type = 'heading_close'
    tokens = [T(), T2(), T3()]
    hs = get_headings(tokens)
    assert isinstance(hs, list)
    # Token with tag not starting with 'h'
    T.tag = 'div'
    hs2 = get_headings([T(), T2(), T3()])
    assert hs2[0]['level'] == 1

def test_parseerror_str_all_branches():
    # No line/col
    e = ParseError("msg")
    assert str(e)
    # With line only
    e = ParseError("msg", line_number=1)
    assert str(e)
    # With line and col
    e = ParseError("msg", line_number=1, column_number=2)
    assert str(e)
    # With context
    e = ParseError("msg", line_number=1, column_number=2, context="ctx")
    assert str(e)

def test_parseresult_add_error_all_levels():
    pr = ParseResult(ast=[], errors=[], warnings=[], metadata={}, source_text="")
    pr.add_error("err", level=ErrorLevel.ERROR)
    pr.add_error("warn", level=ErrorLevel.WARNING)
    pr.add_error("crit", level=ErrorLevel.CRITICAL)
    assert any("err" in str(e) for e in pr.errors)
    assert any("warn" in str(w) for w in pr.warnings)
    assert any("crit" in str(e) for e in pr.errors)
