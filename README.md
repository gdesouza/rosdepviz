# ROSDepViz

ROSDepViz (ROS Dependency Visualizer) is a Python-based tool designed to help developers understand and navigate the dependency tree of ROS (Robot Operating System) packages within a specified source directory. It provides a graphical user interface (GUI) to explore package relationships, showing direct dependencies and dependents.

## Features

*   **Interactive GUI:** A user-friendly interface built with PyQt5.
*   **Package Selection:** Easily select any ROS package found in the specified source directory from a dropdown list.
*   **Dependency & Dependent View:** For a selected package, view its direct dependencies (packages it relies on) and its direct dependents (packages that rely on it).
*   **Click-to-Navigate:** Click on any listed dependency or dependent to make it the new central package, allowing for easy exploration of the dependency graph.
*   **Source Directory Selection:** Dynamically change the ROS source directory to analyze different workspaces.
*   **View Dependency Graph (GUI):** Generate and open a static `.png` image of the dependency tree for the currently selected package using Graphviz.
*   **Static Graph Generation (CLI):** A command-line utility to generate a static `.png` image of the dependency tree for a given package using Graphviz.

## Installation

### 1. Clone the Repository (or ensure project structure)

First, ensure you have the `ROSDepViz` project structure set up. If you're starting fresh, you might clone a repository or create the structure manually as discussed.

### 2. Install System Dependencies

ROSDepViz relies on PyQt5 for its GUI and Graphviz for static graph generation.

**On Debian/Ubuntu:**

```bash
sudo apt-get update
sudo apt-get install python3-pyqt5 graphviz build-essential python3-dev qt5-default libqt5svg5-dev
```

### 3. Set up Python Virtual Environment (Recommended)

It's highly recommended to use a Python virtual environment to manage project dependencies. Crucially, enable `--system-site-packages` so your virtual environment can access the system-installed PyQt5.

```bash
# Navigate to your project's root directory (e.g., where ROSDepViz/ is located)
cd /path/to/your/ROSDepViz/project/root

# Create a virtual environment with system site packages
python3 -m venv venv --system-site-packages

# Activate the virtual environment
source venv/bin/activate
```

### 4. Install Python Dependencies

While PyQt5 is installed via `apt`, other Python dependencies should be installed via `pip` within your activated virtual environment.

```bash
# Ensure your virtual environment is activated
pip install -r requirements.txt
```
*(Note: The `requirements.txt` file is currently empty. You might add `lxml` if parsing becomes more complex, but for now, standard library XML parsing is used.)*

## Usage

### A. Using the GUI Application

1.  **Activate your virtual environment:**
    ```bash
    source venv/bin/activate
    ```
2.  **Run the GUI application:**
    ```bash
    python rosdepviz/gui.py
    ```
3.  **Select ROS Source Directory:**
    *   Upon launching, the application will attempt to default the ROS Source Directory to `ros_indigo/src` relative to the `ROSDepViz` project root.
    *   Click the "Browse" button next to "ROS Source Directory" to select a different root directory where your ROS packages are located (e.g., your `catkin_ws/src` or another ROS distribution's `src` folder).
    *   The application will automatically reload package data from the newly selected directory.
4.  **Explore Dependencies:**
    *   Use the "Select Package" dropdown to choose a ROS package.
    *   The center panel will display the selected package.
    *   The left panel will list its direct dependencies (packages it uses).
    *   The right panel will list its direct dependents (packages that use it).
    *   Click on any package name in the left or right panels to make it the new central package and explore its relationships.
5.  **View Dependency Graph:**
    *   After selecting a package, click the "View graph" button below the package name in the center panel.
    *   This will generate a static `.png` image of the dependency tree for the selected package and open it in your system's default image viewer.

### B. Using the Command-Line Static Graph Generator

This utility generates a static `.png` image of the dependency tree for a specified package.

1.  **Activate your virtual environment:**
    ```bash
    source venv/bin/activate
    ```
2.  **Run the command-line script:**
    ```bash
    python rosdepviz/cli.py <package_name>
    ```
    Replace `<package_name>` with the actual name of the ROS package you want to visualize (e.g., `avidbots_web`).

    This will generate `dependency_tree.dot` (Graphviz DOT file) and `dependency_tree.png` (the image) in the directory where you run the command.

## License

This project is licensed under the [LICENSE](LICENSE) file.