import os
import sys
import tempfile
from collections import defaultdict

import graphviz
import defusedxml.ElementTree as ET
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QComboBox, QLabel, QScrollArea, QLineEdit, QPushButton, QFileDialog,
                             QProgressDialog, QMessageBox)
from PyQt5.QtCore import Qt


class DependencyViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ROSDepViz - ROS Package Dependency Viewer")
        self.setGeometry(100, 100, 1000, 700)  # x, y, width, height

        # Apply a basic style sheet
        self.setStyleSheet(
            """
            QWidget {
                background-color: #f0f0f0; /* Light gray background */
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QLabel {
                color: #333333;
            }
            QLabel#current_pkg_name {
                font-size: 24px;
                font-weight: bold;
                color: #0056b3; /* Darker blue for main package */
                padding: 10px;
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: #e0e0e0;
            }
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
                background-color: white;
            }
            QComboBox::drop-down {
                border: 0px; /* Remove the default dropdown border */
            }
            QComboBox::down-arrow {
                /* image: url(./icons/down_arrow.png); */ /* You might need to provide an icon */
            }
            QComboBox QAbstractItemView {
                border: 1px solid #cccccc;
                selection-background-color: #cce5ff; /* Light blue for selected item background */
                selection-color: #333333; /* Dark text for selected item */
            }
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
                background-color: white;
            }
            QPushButton {
                background-color: #007bff; /* Blue button */
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QScrollArea {
                border: 1px solid #dddddd;
                border-radius: 5px;
                background-color: white;
            }
            /* Style for clickable internal package names */
            QLabel.internal_package a {
                color: #007bff; /* Blue for links */
                text-decoration: none; /* No underline */
            }
            QLabel.internal_package a:hover {
                text-decoration: underline;
            }
            /* Style for external package names */
            QLabel.external_package {
                color: #888888; /* Gray for external packages */
                font-style: italic;
            }
            """,
        )

        # Initial ROS_SRC_DIR
        default_ros_src_dir = os.path.abspath(".")
        self.ros_src_dir = default_ros_src_dir

        self.all_packages = {}  # Stores only packages found within self.ros_src_dir
        self.forward_dependencies = defaultdict(list)  # package -> [all deps, internal and external]
        self.reverse_dependencies = defaultdict(list)  # dep -> [internal packages that depend on it]

        self.show_external_packages = True  # New state variable

        self.load_all_package_data()
        self.init_ui()

    def parse_package_xml(self, package_xml_path):
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
        except Exception as exc:
            print(f"Error parsing {package_xml_path}: {exc}")
            return None, []

    def find_package_xml_path(self, package_name):
        """Searches for a package.xml file for a given package name within the current self.ros_src_dir."""
        for root, _, files in os.walk(self.ros_src_dir):
            if "package.xml" in files:
                package_xml_path = os.path.join(root, "package.xml")
                name, _ = self.parse_package_xml(package_xml_path)
                if name == package_name:
                    return package_xml_path
        return None

    def _gather_package_xml_files(self):
        package_xml_files = []
        if os.path.isdir(self.ros_src_dir):
            for root, _, files in os.walk(self.ros_src_dir):
                if "package.xml" in files:
                    package_xml_files.append(os.path.join(root, "package.xml"))
        return package_xml_files

    def _first_pass_load_packages(self, package_xml_files):
        for pkg_xml_path in package_xml_files:
            name, deps = self.parse_package_xml(pkg_xml_path)
            if name:
                self.all_packages[name] = pkg_xml_path  # Only packages found in ROS_SRC_DIR
                self.forward_dependencies[name] = deps  # Store all dependencies

    def _second_pass_build_reverse_dependencies(self):
        for pkg_name, deps in self.forward_dependencies.items():
            for dep in deps:
                if dep in self.all_packages:  # Only if the dependent is an internal package
                    self.reverse_dependencies[dep].append(pkg_name)

    def load_all_package_data(self):
        """Loads all package data and builds dependency maps from the current self.ros_src_dir."""
        print(f"Loading all package data from: {self.ros_src_dir}...")
        self.all_packages = {}
        self.forward_dependencies = defaultdict(list)
        self.reverse_dependencies = defaultdict(list)

        package_xml_files = self._gather_package_xml_files()

        # First pass: get all package names and their direct dependencies
        self._first_pass_load_packages(package_xml_files)

        # Second pass: build reverse dependencies, only for internal packages
        self._second_pass_build_reverse_dependencies()
        print("Package data loaded.")

        # Update the package selector if it exists
        if hasattr(self, "package_selector"):
            current_selected_package = (
                self.package_selector.currentText()
                if self.package_selector.currentIndex() != 0
                else None
            )

            self.package_selector.clear()
            self.package_selector.addItem("Select a package...")
            self.package_selector.addItems(sorted(self.all_packages.keys()))

            if current_selected_package and current_selected_package in self.all_packages:
                idx = self.package_selector.findText(current_selected_package)
                if idx != -1:
                    self.package_selector.setCurrentIndex(idx)
                    self.display_package_info(current_selected_package)
                else:
                    self.package_selector.setCurrentIndex(0)
                    self.display_package_info("<i>No package selected</i>")
            else:
                self.package_selector.setCurrentIndex(0)
                self.display_package_info("<i>No package selected</i>")

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Path Selection
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit(self.ros_src_dir)
        self.path_input.setReadOnly(True)
        self.browse_button = QPushButton("Browse", self)
        self.browse_button.setFixedWidth(80)  # Set fixed width
        self.browse_button.clicked.connect(self.select_ros_src_directory)

        path_layout.addWidget(QLabel("ROS Source Directory:"))
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)
        main_layout.addLayout(path_layout)

        # Package Selector (Dropdown) and Refresh Button
        selector_row_layout = QHBoxLayout()
        self.package_selector = QComboBox(self)

        # Add a placeholder item and then the actual packages
        self.package_selector.addItem("Select a package...")
        self.package_selector.addItems(sorted(self.all_packages.keys()))
        self.package_selector.setCurrentIndex(0)  # Set initial selection to placeholder

        self.package_selector.currentIndexChanged.connect(self.on_package_selected)

        self.refresh_button = QPushButton("Refresh", self)
        self.refresh_button.setFixedWidth(80)  # Set fixed width
        self.refresh_button.clicked.connect(self.refresh_data)

        self.toggle_external_button = QPushButton("Hide External", self)
        self.toggle_external_button.setFixedWidth(120)
        self.toggle_external_button.clicked.connect(self.toggle_external_packages)

        selector_row_layout.addWidget(QLabel("Select Package:"))
        selector_row_layout.addWidget(self.package_selector)
        selector_row_layout.addWidget(self.refresh_button)
        selector_row_layout.addWidget(self.toggle_external_button)
        main_layout.addLayout(selector_row_layout)

        # Content Area
        content_layout = QHBoxLayout()

        # Left Panel: Dependencies
        self.deps_label = QLabel("<b>Dependencies:</b>")
        self.deps_list = QVBoxLayout()
        self.deps_scroll = QScrollArea()
        self.deps_scroll.setWidgetResizable(True)
        deps_widget = QWidget()
        deps_widget.setLayout(self.deps_list)
        self.deps_scroll.setWidget(deps_widget)

        left_panel_layout = QVBoxLayout()
        left_panel_layout.addWidget(self.deps_label)
        left_panel_layout.addWidget(self.deps_scroll)
        content_layout.addLayout(left_panel_layout)

        # Center Panel: Current Package
        center_panel_layout = QVBoxLayout()
        self.current_pkg_label = QLabel("<b>Current Package:</b>")
        self.current_pkg_name = QLabel("<i>No package selected</i>")
        self.current_pkg_name.setObjectName("current_pkg_name")
        self.current_pkg_name.setAlignment(Qt.AlignCenter)

        center_panel_layout.addWidget(self.current_pkg_label)
        center_panel_layout.addWidget(self.current_pkg_name)

        # View graph Button
        self.view_graph_button = QPushButton("View graph", self)
        self.view_graph_button.clicked.connect(self.save_dependency_image)
        center_panel_layout.addWidget(self.view_graph_button)

        center_panel_layout.addStretch(1)
        content_layout.addLayout(center_panel_layout)

        # Right Panel: Dependents
        self.dependents_label = QLabel("<b>Dependents:</b>")
        self.dependents_list = QVBoxLayout()
        self.dependents_scroll = QScrollArea()
        self.dependents_scroll.setWidgetResizable(True)
        dependents_widget = QWidget()
        dependents_widget.setLayout(self.dependents_list)
        self.dependents_scroll.setWidget(dependents_widget)

        right_panel_layout = QVBoxLayout()
        right_panel_layout.addWidget(self.dependents_label)
        right_panel_layout.addWidget(self.dependents_scroll)
        content_layout.addLayout(right_panel_layout)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def display_package_info(self, package_name):
        self.current_pkg_name.setText(package_name)

        # Clear previous lists
        self.clear_layout(self.deps_list)
        self.clear_layout(self.dependents_list)

        # Display Dependencies
        deps = self.forward_dependencies.get(package_name, [])
        if deps:
            for dep in sorted(deps):
                if not self.show_external_packages and dep not in self.all_packages:
                    continue  # Skip external packages if hidden

                dep_label = QLabel()
                dep_label.setTextFormat(Qt.RichText)  # Enable rich text for links

                if dep in self.all_packages:  # Internal package - make clickable
                    dep_label.setOpenExternalLinks(False)
                    dep_label.setText(f"<a href=\"{dep}\">{dep}</a>")
                    dep_label.linkActivated.connect(self.display_package_info)
                    dep_label.setProperty("class", "internal_package")
                else:  # External package - plain text, grayed out
                    dep_label.setText(dep)
                    dep_label.setProperty("class", "external_package")

                self.deps_list.addWidget(dep_label)
        else:
            self.deps_list.addWidget(QLabel("No dependencies found."))
        self.deps_list.addStretch(1)

        # Display Dependents
        dependents = self.reverse_dependencies.get(package_name, [])
        if dependents:
            for dep in sorted(dependents):
                if not self.show_external_packages and dep not in self.all_packages:
                    continue  # This condition should ideally not be met for dependents

                dep_label = QLabel()
                dep_label.setTextFormat(Qt.RichText)  # Enable rich text for links

                if dep in self.all_packages:  # Internal package - make clickable
                    dep_label.setOpenExternalLinks(False)
                    dep_label.setText(f"<a href=\"{dep}\">{dep}</a>")
                    dep_label.linkActivated.connect(self.display_package_info)
                    dep_label.setProperty("class", "internal_package")
                else:  # External package - plain text, grayed out
                    dep_label.setText(dep)
                    dep_label.setProperty("class", "external_package")

                self.dependents_list.addWidget(dep_label)
        else:
            self.dependents_list.addWidget(QLabel("No packages depend on this."))
        self.dependents_list.addStretch(1)

    def on_package_selected(self, index):
        # Check if the selected index is the placeholder (index 0)
        if index == 0:
            self.current_pkg_name.setText("<i>No package selected</i>")
            self.clear_layout(self.deps_list)
            self.clear_layout(self.dependents_list)
            self.deps_list.addWidget(QLabel("-"))
            self.dependents_list.addWidget(QLabel("-"))
            self.deps_list.addStretch(1)
            self.dependents_list.addStretch(1)
            return

        package_name = self.package_selector.currentText()
        self.display_package_info(package_name)

    def select_ros_src_directory(self):
        new_dir = QFileDialog.getExistingDirectory(
            self, "Select ROS Source Directory", self.ros_src_dir
        )
        if new_dir:
            self.ros_src_dir = new_dir
            self.path_input.setText(new_dir)
            self.load_all_package_data()

    def refresh_data(self):
        print("Refresh button clicked. Reloading data...")
        self.load_all_package_data()

    def toggle_external_packages(self):
        self.show_external_packages = not self.show_external_packages
        if self.show_external_packages:
            self.toggle_external_button.setText("Hide External")
        else:
            self.toggle_external_button.setText("Show External")

        # Re-display info for current package to apply the filter
        current_package = self.current_pkg_name.text()
        if current_package and current_package != "<i>No package selected</i>":
            self.display_package_info(current_package)

    def _build_subgraph_for_package(self, start_package):
        """Builds subgraph nodes and edges for `start_package` and returns them."""
        subgraph_nodes = set()
        subgraph_edges = defaultdict(list)

        queue = [start_package]
        visited = set()

        while queue:
            current_pkg = queue.pop(0)
            if current_pkg in visited:
                continue
            visited.add(current_pkg)
            subgraph_nodes.add(current_pkg)

            deps = self.forward_dependencies.get(current_pkg, [])
            for dep in deps:
                subgraph_edges[current_pkg].append(dep)
                if dep in self.all_packages and dep not in visited:
                    queue.append(dep)

        return subgraph_nodes, subgraph_edges

    def save_dependency_image(self):
        current_package = self.current_pkg_name.text()
        if current_package == "<i>No package selected</i>":
            QMessageBox.warning(
                self,
                "No Package Selected",
                "Please select a package first to save its dependency tree as an image.",
            )
            return

        progress_dialog = QProgressDialog("Generating image...", "Cancel", 0, 0, self)
        progress_dialog.setWindowTitle("ROSDepViz")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setCancelButton(None)  # No cancel button
        progress_dialog.show()
        QApplication.processEvents()  # Update GUI

        try:
            dot = graphviz.Digraph(comment="Dependency Tree")
            dot.attr(rankdir="LR")
            dot.attr("node", shape="box")

            # Build the subgraph for the static image
            subgraph_nodes, subgraph_edges = self._build_subgraph_for_package(current_package)

            # Determine leaf nodes within this specific subgraph
            nodes_with_outgoing = set(subgraph_edges.keys())
            all_nodes = set(subgraph_nodes)
            for deps_list in subgraph_edges.values():
                for dep_node in deps_list:
                    all_nodes.add(dep_node)

            leaf_nodes = all_nodes - nodes_with_outgoing

            # Add nodes with styling
            for package in sorted(list(all_nodes)):
                self._style_node(dot, package, current_package, leaf_nodes)

            # Add edges
            for package, dependencies in subgraph_edges.items():
                for dep in dependencies:
                    dot.edge(package, dep)

            # Render the graph and open the image
            png_base = os.path.join(
                tempfile.gettempdir(), f"{current_package}_dependency_tree"
            )
            dot.render(png_base, format="png", cleanup=True)
            png_path = png_base + ".png"

            # Open the image
            import webbrowser

            if sys.platform == "win32":
                os.startfile(png_path)
            else:
                webbrowser.open(f"file://{png_path}")

        except Exception as exc:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {exc}")
        finally:
            progress_dialog.close()

    def _style_node(self, dot, package, current_package, leaf_nodes):
        """Apply styling to `package` nodes in the DOT graph."""
        if package == current_package:
            dot.node(package, style="filled", fillcolor="lightblue")
            return

        if package in leaf_nodes:
            if package not in self.all_packages:
                dot.node(
                    package,
                    style="filled",
                    fillcolor="lightgray",
                    fontcolor="dimgray",
                )
            else:
                dot.node(package, style="filled", fillcolor="lightgreen")
            return

        if package not in self.all_packages:
            dot.node(
                package,
                style="filled",
                fillcolor="lightgray",
                fontcolor="dimgray",
            )
            return

        dot.node(package)


if __name__ == "__main__":
    app = QApplication([])
    viewer = DependencyViewer()
    viewer.show()
    app.exec_()
