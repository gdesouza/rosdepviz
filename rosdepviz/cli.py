import os
import sys

# trunk-ignore(bandit/B405)
import xml.etree.ElementTree as ET
from collections import defaultdict

import graphviz

# Calculate the default ROS_SRC_DIR relative to the script's location
script_dir = os.path.dirname(__file__)
# Go up two directories (from rosdepviz/cli.py to ROSDepViz/ to parent of ROSDepViz)
# then into ros_indigo/src
ROS_SRC_DIR = os.path.abspath(os.path.join(script_dir, "..", "..", "ros_indigo", "src"))


def parse_package_xml(package_xml_path):
    """Parses a package.xml file and returns the package name and its dependencies."""
    try:
        tree = ET.parse(package_xml_path)
        root = tree.getroot()

        name = root.find("name").text if root.find("name") is not None else None

        dependencies = set()
        for dep_type in ["build_depend", "exec_depend", "depend"]:
            for dep in root.findall(dep_type):
                if dep.text:
                    dependencies.add(dep.text)
        return name, list(dependencies)
    except Exception as e:
        print(f"Error parsing {package_xml_path}: {e}")
        return None, []


def find_package_xml(package_name):
    """Searches for a package.xml file for a given package name within ROS_SRC_DIR."""
    for root, _, files in os.walk(ROS_SRC_DIR):
        if "package.xml" in files:
            package_xml_path = os.path.join(root, "package.xml")
            name, _ = parse_package_xml(package_xml_path)
            if name == package_name:
                return package_xml_path
    return None


def build_dependency_tree(start_package_name):
    """
    Recursively builds the dependency tree for a given package.
    Returns a dictionary where keys are package names and values are lists of their dependencies.
    """
    dependency_tree = defaultdict(list)
    visited = set()

    queue = [start_package_name]

    while queue:
        current_package = queue.pop(0)
        if current_package in visited:  # Only process each package once
            continue

        visited.add(current_package)

        package_xml_path = find_package_xml(current_package)
        if package_xml_path:
            name, deps = parse_package_xml(package_xml_path)
            if name:  # Ensure name is not None
                for dep in deps:
                    # Only add dependencies that are also found within ROS_SRC_DIR
                    # This filters out system dependencies like std_msgs, roscpp etc.
                    if find_package_xml(dep):
                        dependency_tree[name].append(dep)
                        if dep not in visited:  # Add to queue only if not visited
                            queue.append(dep)
        # else:
        # print(f"Warning: package.xml not found for '{current_package}' within {ROS_SRC_DIR}")
        # pass # This is expected for system dependencies

    return dependency_tree


def generate_dot_graph(dependency_tree, output_file="dependency_tree.dot"):
    """Generates a DOT language graph from the dependency tree, highlighting leaf nodes."""
    # Create a new Digraph using the graphviz library
    dot = graphviz.Digraph(comment='Dependency Tree')
    dot.attr(rankdir='LR')  # Left to Right layout
    dot.attr('node', shape='box')  # Default box shape for nodes

    all_packages_in_graph = set()
    packages_with_outgoing_edges = set()

    for package, dependencies in dependency_tree.items():
        all_packages_in_graph.add(package)
        packages_with_outgoing_edges.add(package)
        for dep in dependencies:
            all_packages_in_graph.add(dep)

    leaf_nodes = all_packages_in_graph - packages_with_outgoing_edges

    # Add nodes with styling
    for package in all_packages_in_graph:
        if package in leaf_nodes:
            dot.node(package, style='filled', fillcolor='lightgreen')
        else:
            dot.node(package)

    # Add edges
    for package, dependencies in dependency_tree.items():
        for dep in dependencies:
            dot.edge(package, dep)

    # Save the DOT file and render to PNG
    try:
        # Remove .dot extension from output_file to get the base name
        base_name = output_file.replace(".dot", "")

        # Save the DOT source
        with open(output_file, "w") as f:
            f.write(dot.source)
        print(f"DOT graph saved to {output_file}")

        # Render to PNG
        dot.render(base_name, format='png', cleanup=True)
        print(f"Graph rendered to {base_name}.png")
    except Exception as e:
        print(f"Error rendering graph with Graphviz: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cli.py <package_name>")
        sys.exit(1)

    start_package = sys.argv[1]  # Get package name from command line argument

    print(f"Building dependency tree for '{start_package}'...")
    tree = build_dependency_tree(start_package)

    if tree:
        print("\nDependency Tree (direct dependencies within ros_indigo/src):")
        for pkg, deps in tree.items():
            print(f"  {pkg}: {', '.join(deps)}")

        generate_dot_graph(tree)
    else:
        print(f"Could not build dependency tree for '{start_package}'.")
