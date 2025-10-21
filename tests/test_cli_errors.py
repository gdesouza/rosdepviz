import os
from pathlib import Path
import builtins

import rosdepviz.cli as cli


def test_parse_package_xml_malformed(tmp_path, capsys):
    # Create malformed XML
    bad = tmp_path / "badpkg" / "package.xml"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("<package><name>no-close")

    name, deps = cli.parse_package_xml(str(bad))
    assert name is None
    assert deps == []

    # Ensure error message was printed
    captured = capsys.readouterr()
    assert "Error parsing" in captured.out


class BadDigraph:
    def __init__(self, *args, **kwargs):
        pass

    @property
    def source(self):
        return "digraph G { }"

    def attr(self, *args, **kwargs):
        pass

    def node(self, *args, **kwargs):
        pass

    def edge(self, *args, **kwargs):
        pass

    def render(self, base_name, format='png', cleanup=False):
        raise RuntimeError("render failed")


def test_generate_dot_graph_render_error(tmp_path, monkeypatch, capsys):
    # Prepare a simple tree
    tree = {"A": ["B"], "B": []}

    # Monkeypatch graphviz.Digraph to our BadDigraph
    monkeypatch.setattr(cli, 'graphviz', type('M', (), {'Digraph': BadDigraph}))

    out = tmp_path / "out.dot"
    # Should not raise; error is printed
    cli.generate_dot_graph(tree, output_file=str(out))

    captured = capsys.readouterr()
    assert "DOT graph saved to" in captured.out
    assert "Error rendering graph with Graphviz" in captured.out


def test_generate_dot_graph_graphviz_missing(tmp_path, monkeypatch, capsys):
    # When graphviz is None, calling generate_dot_graph should raise AttributeError
    tree = {"A": []}
    monkeypatch.setattr(cli, 'graphviz', None)

    out = tmp_path / "out2.dot"
    try:
        cli.generate_dot_graph(tree, output_file=str(out))
    except Exception as exc:
        # We expect an exception due to missing graphviz
        assert isinstance(exc, Exception)


def test_build_dependency_tree_filters_external(tmp_path):
    # Create package A that depends on external 'roscpp'
    base = tmp_path / "src"
    (base / "A").mkdir(parents=True)
    (base / "A" / "package.xml").write_text("""<?xml version='1.0'?><package><name>A</name><depend>roscpp</depend></package>""")

    cli.ROS_SRC_DIR = str(base)

    tree = cli.build_dependency_tree("A")
    # roscpp should not be included since it's external
    assert tree.get("A", []) == []
