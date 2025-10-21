import os
from pathlib import Path


import rosdepviz.cli as cli


def write_package_xml(path: Path, name: str, deps: list[str] | None = None):
    deps = deps or []
    content = """<?xml version="1.0"?>
<package>
  <name>{name}</name>
{deps}
</package>
"""
    deps_str = "\n".join(f"  <depend>{d}</depend>" for d in deps)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.format(name=name, deps=deps_str))


def test_parse_package_xml_valid_and_invalid(tmp_path):
    pkg_dir = tmp_path / "pkg"
    pkg_xml = pkg_dir / "package.xml"
    write_package_xml(pkg_xml, "mypkg", deps=["dep1", "dep2"])

    name, deps = cli.parse_package_xml(str(pkg_xml))
    assert name == "mypkg"
    assert set(deps) == {"dep1", "dep2"}

    # Invalid XML should return (None, [])
    bad_xml = tmp_path / "bad" / "package.xml"
    bad_xml.parent.mkdir(parents=True, exist_ok=True)
    bad_xml.write_text("<package><name>no-close")

    name2, deps2 = cli.parse_package_xml(str(bad_xml))
    assert name2 is None
    assert deps2 == []


def test_find_and_build_dependency_tree(tmp_path):
    # Create a simple package layout:
    # A depends on B and std_msgs (external)
    # B depends on C
    # C has no deps
    base = tmp_path / "src"
    write_package_xml(base / "A" / "package.xml", "A", deps=["B", "std_msgs"])
    write_package_xml(base / "B" / "package.xml", "B", deps=["C"])
    write_package_xml(base / "C" / "package.xml", "C", deps=[])

    # Point the module to this temp src dir
    cli.ROS_SRC_DIR = str(base)

    a_path = cli.find_package_xml("A")
    assert a_path is not None
    assert a_path.endswith(os.path.join("A", "package.xml"))

    tree = cli.build_dependency_tree("A")
    # Only internal dependencies should be included (std_msgs is external)
    assert "A" in tree
    assert tree["A"] == ["B"]
    assert "B" in tree
    assert tree["B"] == ["C"]
    # C has no outgoing edges, so it may not appear as a key
    assert "C" not in tree or tree.get("C") == []


def test_build_dependency_tree_with_cycle(tmp_path):
    # A -> B -> A (cycle)
    base = tmp_path / "src2"
    write_package_xml(base / "A" / "package.xml", "A", deps=["B"])
    write_package_xml(base / "B" / "package.xml", "B", deps=["A"])

    cli.ROS_SRC_DIR = str(base)

    tree = cli.build_dependency_tree("A")
    # Should contain both edges but not loop infinitely
    assert tree["A"] == ["B"]
    assert tree["B"] == ["A"]


class FakeDigraph:
    def __init__(self, *args, **kwargs):
        self.nodes = []
        self.edges = []
        self.attrs = []
        self._comment = None

    def attr(self, *args, **kwargs):
        self.attrs.append((args, kwargs))

    def node(self, name, **kwargs):
        self.nodes.append((name, kwargs))

    def edge(self, a, b, **kwargs):
        self.edges.append((a, b, kwargs))

    @property
    def source(self):
        # Minimal DOT source representation for assertions
        lines = ["digraph G {"]
        for n, kw in self.nodes:
            lines.append(f'  "{n}";')
        for a, b, _ in self.edges:
            lines.append(f'  "{a}" -> "{b}";')
        lines.append("}")
        return "\n".join(lines)

    def render(self, base_name, format='png', cleanup=False):
        # Create a fake png file to emulate Graphviz render
        png_path = f"{base_name}.png"
        Path(png_path).write_text("PNG")
        return png_path


def test_generate_dot_graph_monkeypatched(tmp_path, monkeypatch):
    # Prepare a small dependency tree
    tree = {"A": ["B"], "B": []}

    # Monkeypatch the Digraph class used in the module
    monkeypatch.setattr(cli, 'graphviz', type('M', (), {'Digraph': FakeDigraph}))

    out_dot = tmp_path / "out.dot"
    cli.generate_dot_graph(tree, output_file=str(out_dot))

    # Check that the .dot file was written and contains nodes and an edge
    assert out_dot.exists()
    content = out_dot.read_text()
    assert '"A"' in content
    assert '"B"' in content
    assert '"A" -> "B"' in content

    # And that a png was 'rendered' by our fake Digraph
    png = str(out_dot).replace('.dot', '') + '.png'
    assert Path(png).exists()
