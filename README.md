<div id="top">

<!-- HEADER STYLE: BANNER -->
<div align="center">

<img src="assets/banner.svg" alt="DearPyGui Constructor Banner" width="100%">

<br>

<!-- BADGES -->
<p align="center">
  <a href="https://github.com/justenotik/dearpygui-constructor/blob/main/LICENSE.md">
    <img src="https://img.shields.io/badge/License-Parity--7.0.0-3B82F6?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="License: Parity-7.0.0">
  </a>
  <img src="https://img.shields.io/github/last-commit/justenotik/dearpygui-constructor?style=for-the-badge&logo=git&logoColor=white&color=00ADD8" alt="last-commit">
  <img src="https://img.shields.io/github/languages/top/justenotik/dearpygui-constructor?style=for-the-badge&logo=python&logoColor=white&color=3776AB" alt="repo-top-language">
  <img src="https://img.shields.io/badge/Widgets-23%20Built--In-10B981?style=for-the-badge" alt="23 Widgets">
</p>

<p align="center">
  <em>Built with the tools and technologies:</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat-square&logo=Python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/DearPyGui-GPU%20GUI-00B4D8.svg?style=flat-square&logo=cplusplus&logoColor=white" alt="DearPyGui">
  <img src="https://img.shields.io/badge/Python%20AST-Code%20Parser-F59E0B.svg?style=flat-square&logo=python&logoColor=white" alt="Python AST">
  <img src="https://img.shields.io/badge/JSON-Config-000000.svg?style=flat-square&logo=json&logoColor=white" alt="JSON">
  <img src="https://img.shields.io/badge/Unittest-Integration%20Suite-10B981.svg?style=flat-square&logo=pytest&logoColor=white" alt="Unittest">
</p>

</div>

---

## 🧭 Table of Contents

- [📍 Overview](#-overview)
- [👾 Features](#-features)
- [🧩 Supported Widgets (23 Types)](#-supported-widgets-23-types)
- [📁 Project Structure](#-project-structure)
  - [📂 Project Index](#-project-index)
- [🚀 Getting Started](#-getting-started)
  - [📋 Prerequisites](#-prerequisites)
  - [⚙️ Installation](#️-installation)
  - [🤖 Usage](#-usage)
  - [🧪 Testing](#-testing)
- [📌 Roadmap](#-roadmap)
- [🔰 Contributing](#-contributing)
- [🎗 License & Commercial Use](#-license--commercial-use)

---

## 📍 Overview

**DearPyGui Constructor** is a visual drag-and-drop interface builder and bidirectional Python code generator built specifically for [DearPyGui](https://github.com/hoffstadt/DearPyGui).

Instead of writing repetitive nested `with dpg.window():`, `with dpg.tab_bar():`, and `with dpg.group(horizontal=True):` blocks by hand and restarting your script on every tweak, you can visually assemble multi-window and multi-tab layouts on a live canvas, inspect and tweak properties in real time, and export clean, ready-to-run Python scripts — or paste existing DearPyGui code back into the editor to reconstruct the visual canvas via Python's `ast` module.

---

## 👾 Features

|      | Feature | Summary |
| :--- | :---: | :--- |
| 🖱️ | **Custom Drag & Drop Engine** | <ul><li>Drag any of the 23 widget types directly from the palette onto target windows or tabs</li><li>Live floating ghost preview showing exact drop target (`New Row`, `Insert into Row`, `Reorder`)</li><li>Drag-move already placed widgets across rows, columns, tabs, and windows with optional position locking (`Lock Drag`)</li></ul> |
| 🪟 | **Multi-Window & Tab Hierarchy** | <ul><li>Create, resize, rename, and manage multiple independent `dpg.window` instances on the canvas</li><li>Add, rename, reorder (`<< Left` / `Right >>`), and delete `dpg.tab` containers inside any window</li><li>Full hierarchy tree in the **Outliner** tab plus a quick outliner in the **Elements** tab</li></ul> |
| 🔍 | **Live Inspector & RMB Context Menu** | <ul><li>Right-click (`RMB`) any widget on the canvas or in the outliner for instant popup editing</li><li>Configure custom widget `tag` (ID), `label`, `default_value`, `min_value`/`max_value`, `items`, `width`/`height`, `wrap`, `enabled`, and `show`</li><li>Fine grid movement controls (`<< Left`, `Right >>`, `^^ Up`, `vv Down`), widget cloning, and row/column deletion</li></ul> |
| 🔄 | **Bidirectional Code Export & AST Import** | <ul><li>One-click generation of clean, human-readable Python code using `dearpygui.dearpygui as dpg`</li><li>Built-in **AST Parser** (`ast.parse`) that imports existing DearPyGui scripts back onto the visual canvas (windows, tabs, horizontal groups, tags, and widget kwargs)</li><li>Direct save/load to `.py` files from the **Export** tab</li></ul> |
| 🎨 | **Customizable Workspace Appearance** | <ul><li>5 built-in theme presets (`Dark Slate`, `Classic Charcoal`, `Deep Cyberpunk`, `Forest Night`, `Light Silver`)</li><li>Custom viewport background image loader (`.png`, `.jpg`, `.jpeg`, `.bmp`) with real-time opacity slider</li><li>Automatic persistence of workspace appearance in `appearance_settings.json` (strictly app-only, never pollutes exported UI code)</li></ul> |
| 🛡️ | **C-Long Overflow & Crash Protection** | <ul><li>Safe numeric clamping (`safe_int`, `safe_float`, `parse_rgba_list`) prevents DearPyGui C-extension `OverflowError` crashes on extreme numeric inputs</li><li>Automatic ID sanitization (`sanitize_id`) ensures valid, collision-free DearPyGui tags</li></ul> |

---

## 🧩 Supported Widgets (23 Types)

| Category | Widgets | DPG Functions |
| :--- | :--- | :--- |
| **Basic & Layout** | `Button`, `Text`, `Separator`, `Spacer`, `LoadingIndicator` | `add_button`, `add_text`, `add_separator`, `add_spacer`, `add_loading_indicator` |
| **Text & Numeric Inputs** | `InputText`, `InputInt`, `InputFloat` | `add_input_text`, `add_input_int`, `add_input_float` |
| **Sliders, Drags & Knobs** | `SliderFloat`, `SliderInt`, `DragFloat`, `DragInt`, `KnobFloat`, `Slider3D` | `add_slider_float`, `add_slider_int`, `add_drag_float`, `add_drag_int`, `add_knob_float`, `add_3d_slider` |
| **Selection & Containers** | `Checkbox`, `RadioButton`, `Combo`, `Listbox`, `ProgressBar` | `add_checkbox`, `add_radio_button`, `add_combo`, `add_listbox`, `add_progress_bar` |
| **Color, Date & Time** | `ColorEdit`, `ColorPicker`, `DatePicker`, `TimePicker` | `add_color_edit`, `add_color_picker`, `add_date_picker`, `add_time_picker` |

---

## 📁 Project Structure

```sh
└── dearpygui-constructor/
    ├── .gitignore
    ├── LICENSE.md
    ├── README.md
    ├── app.py
    ├── appearance_settings.json
    ├── assets/
    │   └── banner.svg
    └── test_app.py
```

### 📂 Project Index

<details open>
	<summary><b><code>DEARPYGUI-CONSTRUCTOR/</code></b></summary>
	<details open>
		<summary><b>__root__</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href="https://github.com/justenotik/dearpygui-constructor/blob/main/app.py">app.py</a></b></td>
				<td>- Core application module containing the centralized 23-widget specification registry (<code>WIDGET_SPECS</code>), state management, custom mouse drag-and-drop engine, RMB context menu, Outliner, Inspector, bidirectional Python code generator, AST parser, and workspace appearance manager.</td>
			</tr>
			<tr>
				<td><b><a href="https://github.com/justenotik/dearpygui-constructor/blob/main/test_app.py">test_app.py</a></b></td>
				<td>- End-to-end integration test suite (<code>unittest</code>) validating all 23 widget types, window/tab lifecycle, RMB context menu, drag-and-drop, AST export/import roundtrips, appearance persistence, and C-long overflow protection.</td>
			</tr>
			<tr>
				<td><b><a href="https://github.com/justenotik/dearpygui-constructor/blob/main/appearance_settings.json">appearance_settings.json</a></b></td>
				<td>- Persists constructor-only workspace appearance settings (theme preset, viewport/window RGBA colors, background image path, and opacity).</td>
			</tr>
			<tr>
				<td><b><a href="https://github.com/justenotik/dearpygui-constructor/blob/main/LICENSE.md">LICENSE.md</a></b></td>
				<td>- Official text of <b>The Parity Public License 7.0.0</b> (<code>SPDX: Parity-7.0.0</code>).</td>
			</tr>
			</table>
		</blockquote>
	</details>
</details>

---

## 🚀 Getting Started

### 📋 Prerequisites

Before getting started with **DearPyGui Constructor**, ensure your environment meets the following requirements:

- **Programming Language:** Python `3.10+`
- **Dependencies:** `dearpygui`

### ⚙️ Installation

1. Clone the repository:
```sh
❯ git clone https://github.com/justenotik/dearpygui-constructor.git
```

2. Navigate to the project directory:
```sh
❯ cd dearpygui-constructor
```

3. Install `dearpygui`:
```sh
❯ pip install dearpygui
```

### 🤖 Usage

Launch the visual constructor:

```sh
❯ python app.py
```

**Quick Workflow:**
1. **Add Widgets:** In the **Elements** tab, drag any widget onto a canvas window (or click `+ Row` / `+ Col`).
2. **Manage Windows & Tabs:** Click `+ Window` or `+ Tab` to create multi-window and tabbed layouts.
3. **Edit Properties:** Left-click any widget to inspect it in the **Inspector** tab, or **Right-Click (RMB)** any placed widget for the quick popup editor.
4. **Export / Import Code:** Open the **Export** tab and click **Export from Canvas** (or **Save .py**) to generate standalone Python code, or paste existing DearPyGui code and click **Import to Canvas**.

### 🧪 Testing

Run the automated integration test suite:

```sh
❯ python -m unittest test_app.py -v
```

---

## 📌 Roadmap

- [X] **`23 Core Widgets`**: Full palette, canvas rendering, and property inspector support.
- [X] **`Multi-Window & Tabs`**: Visual creation, reordering, and management of windows and tab bars.
- [X] **`AST Code Import/Export`**: Bidirectional roundtrip between visual canvas and Python code.
- [ ] **`Callback Stubs Generator`**: Automatic generation of handler functions for button clicks and value changes.
- [ ] **`Custom Widget Themes`**: Per-widget color and rounding overrides with theme export.
- [ ] **`Undo / Redo Stack`**: Full history stack (`Ctrl+Z` / `Ctrl+Y`) for canvas operations.

---

## 🔰 Contributing

Contributions, bug reports, and feature requests are welcome!

- **[Report Issues](https://github.com/justenotik/dearpygui-constructor/issues)**: Submit bugs found or log feature requests.
- **[Submit Pull Requests](https://github.com/justenotik/dearpygui-constructor/pulls)**: Review open PRs and submit your own improvements.

<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Fork the project to your GitHub account.
2. **Clone Locally**:
   ```sh
   git clone https://github.com/justenotik/dearpygui-constructor.git
   ```
3. **Create a Feature Branch**:
   ```sh
   git checkout -b feature/my-improvement
   ```
4. **Run Tests**: Ensure all integration tests pass:
   ```sh
   python -m unittest test_app.py -v
   ```
5. **Submit a Pull Request**: Open a PR with a clear description of your changes.
</details>

---

## 🎗 License & Commercial Use

This project is dual-licensed:

1. **Open-Source License ([The Parity Public License 7.0.0](LICENSE.md) — `SPDX: Parity-7.0.0`):**
   Free to use, modify, and share **only** if all software you develop, operate, or analyze with this tool (including forks and modifications) is publicly released in full source code under compatible open-source terms with attribution to **JustEnotik** (`https://github.com/justenotik/dearpygui-constructor`).
2. **Commercial License (Closed-Source / Proprietary Use):**
   If you wish to use **DearPyGui Constructor** to develop closed-source, proprietary, internal-company, or client software without disclosing your source code under Parity 7.0.0, you must obtain a paid **Commercial License**.
   - **Contact:** **[justenotik@proton.me](mailto:justenotik@proton.me)** *(crypto accepted)*

<div align="right"><a href="#top"><b>↑ Back to Top</b></a></div>
