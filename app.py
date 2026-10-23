import ast
import json
import math
import os
import re
import uuid
import dearpygui.dearpygui as dpg

# ==========================================
# 1. CONFIGURATION, REGISTRY & STATE
# ==========================================
APP_DIR = os.path.dirname(os.path.abspath(__file__))
APPEARANCE_CONFIG_PATH = os.path.join(APP_DIR, "appearance_settings.json")

# Centralized Widget Specification Registry (Single Source of Truth)
# Drives creation, palette, drag preview, canvas rendering, inspector, export, and AST import
# without repetitive 23-branch if/elif ladders.
def _spec(
    dpg_func,
    palette_func,
    palette_kw,
    *,
    label_kw="label",
    val_type=None,
    minmax_type=None,
    width=140,
    height=0,
    default_value="",
    min_value=0,
    max_value=100,
    has_label=True,
    has_width=True,
    has_height=False,
    has_defval=False,
    has_items=False,
    has_minmax=False,
    has_wrap=False,
    supports_enabled=True,
    extra_kw=None,
):
    return {
        "dpg_func": dpg_func,
        "label_kw": label_kw,
        "val_type": val_type,
        "minmax_type": minmax_type,
        "width": width,
        "height": height,
        "default_value": default_value,
        "min_value": min_value,
        "max_value": max_value,
        "has_label": has_label,
        "has_width": has_width,
        "has_height": has_height,
        "has_defval": has_defval,
        "has_items": has_items,
        "has_minmax": has_minmax,
        "has_wrap": has_wrap,
        "supports_enabled": supports_enabled,
        "extra_kw": extra_kw or {},
        "palette_func": palette_func,
        "palette_kw": palette_kw,
    }


WIDGET_SPECS = {
    "Button": _spec("add_button", "add_button", {"label": "Button (Drag)", "width": 185}, has_height=True),
    "Text": _spec("add_text", "add_selectable", {"label": "Text Label (Drag)", "width": 185}, label_kw="default_value", width=0, default_value="Sample text", has_width=False, has_wrap=True, supports_enabled=False),
    "InputText": _spec("add_input_text", "add_input_text", {"default_value": "InputText (Drag)", "width": 185, "readonly": True}, val_type="str", default_value="Sample text", has_defval=True),
    "InputInt": _spec("add_input_int", "add_input_int", {"default_value": 10, "width": 185, "step": 0}, val_type="int", default_value=10, has_defval=True),
    "InputFloat": _spec("add_input_float", "add_input_float", {"default_value": 1.5, "width": 185, "step": 0}, val_type="float", default_value=1.5, has_defval=True),
    "SliderFloat": _spec("add_slider_float", "add_slider_float", {"default_value": 0.5, "width": 185}, val_type="float", minmax_type="float", default_value=0.5, min_value=0.0, max_value=1.0, has_defval=True, has_minmax=True),
    "SliderInt": _spec("add_slider_int", "add_slider_int", {"default_value": 50, "width": 185}, val_type="int", minmax_type="int", default_value=50, min_value=0, max_value=100, has_defval=True, has_minmax=True),
    "DragFloat": _spec("add_drag_float", "add_drag_float", {"default_value": 2.5, "width": 185}, val_type="float", minmax_type="float", default_value=2.5, min_value=0.0, max_value=100.0, has_defval=True, has_minmax=True),
    "DragInt": _spec("add_drag_int", "add_drag_int", {"default_value": 25, "width": 185}, val_type="int", minmax_type="int", default_value=25, min_value=0, max_value=100, has_defval=True, has_minmax=True),
    "KnobFloat": _spec("add_knob_float", "add_button", {"label": "(o) KnobFloat (Drag)", "width": 185}, val_type="float", minmax_type="float", width=0, default_value=0.5, min_value=0.0, max_value=1.0, has_width=False, has_defval=True, has_minmax=True),
    "Checkbox": _spec("add_checkbox", "add_checkbox", {"label": "Checkbox (Drag)", "default_value": True}, val_type="bool", width=0, default_value=True, has_width=False, has_defval=True),
    "RadioButton": _spec("add_radio_button", "add_radio_button", {"items": ["Radio 1", "Radio 2"], "horizontal": True}, label_kw=None, width=0, has_label=False, has_width=False, has_items=True, extra_kw={"horizontal": True}),
    "Combo": _spec("add_combo", "add_combo", {"items": ["Combo 1", "Combo 2"], "default_value": "Combo 1", "width": 185}, val_type="first_item", default_value="Option 1", has_items=True),
    "Listbox": _spec("add_listbox", "add_button", {"label": "[=] Listbox (Drag)", "width": 185}, default_value="Option 1", has_items=True),
    "ProgressBar": _spec("add_progress_bar", "add_progress_bar", {"default_value": 0.6, "overlay": "ProgressBar (Drag)", "width": 185}, label_kw="overlay", val_type="float", default_value=0.6, has_defval=True, supports_enabled=False),
    "ColorEdit": _spec("add_color_edit", "add_color_edit", {"default_value": [100, 180, 255, 255], "width": 185, "no_picker": True}, val_type="rgba", width=160, default_value="100, 180, 255, 255", has_defval=True),
    "ColorPicker": _spec("add_color_picker", "add_button", {"label": "[#] ColorPicker (Drag)", "width": 185}, val_type="rgba", width=160, default_value="100, 180, 255, 255", has_defval=True),
    "DatePicker": _spec("add_date_picker", "add_button", {"label": "[Cal] DatePicker (Drag)", "width": 185}, width=0, has_width=False),
    "TimePicker": _spec("add_time_picker", "add_button", {"label": "[Clk] TimePicker (Drag)", "width": 185}, width=0, has_width=False),
    "LoadingIndicator": _spec("add_loading_indicator", "add_button", {"label": "(*) LoadingSpinner (Drag)", "width": 185}, label_kw=None, width=0, has_label=False, has_width=False, supports_enabled=False, extra_kw={"style": 1, "radius": 2.5}),
    "Slider3D": _spec("add_3d_slider", "add_button", {"label": "[3D] Slider3D (Drag)", "width": 185}, width=110, height=110, has_height=True, extra_kw={"scale": 0.45}),
    "Separator": _spec("add_separator", "add_button", {"label": "--- Separator (Drag) ---", "width": 185}, label_kw=None, width=0, has_label=False, has_width=False, supports_enabled=False),
    "Spacer": _spec("add_spacer", "add_button", {"label": "[ Spacer (Drag) ]", "width": 185}, label_kw=None, width=0, height=15, has_label=False, has_height=True, supports_enabled=False),
}

WIDGET_TYPES = list(WIDGET_SPECS.keys())
DPG_FUNC_TO_TYPE = {spec["dpg_func"]: w_type for w_type, spec in WIDGET_SPECS.items()}

BG_PRESETS = {
    "Dark Slate (Default)": {"vp": [18, 22, 30, 255], "win": [28, 32, 42, 255]},
    "Classic Charcoal": {"vp": [32, 32, 35, 255], "win": [45, 45, 48, 255]},
    "Deep Cyberpunk": {"vp": [12, 10, 24, 255], "win": [22, 18, 42, 255]},
    "Forest Night": {"vp": [14, 24, 18, 255], "win": [24, 38, 30, 255]},
    "Light Silver": {"vp": [215, 220, 228, 255], "win": [240, 242, 245, 255]},
}

state = {
    "windows": [
        {
            "id": "win_main",
            "title": "Main Window",
            "pos": [455, 20],
            "width": 560,
            "height": 480,
            "rows": [
                {
                    "id": "row_init",
                    "widgets": []
                }
            ],
            "tabs": [],          # List of {"id": "tab_xxx", "title": "Tab 1", "rows": [...]}
            "active_tab_id": None
        }
    ],
    "selected_target": {
        "type": "window",        # "window", "tab", or "widget"
        "window_id": "win_main",
        "tab_id": None,          # None = root window rows; or tab["id"]
        "row_id": "row_init",
        "widget_id": None
    },
    # Custom Mouse Drag & Drop state (using wrapper dpg.group for 100% rect_min/rect_max support)
    "drag": {
        "pending": None,         # (mode, payload_val, label_str, (start_x, start_y))
        "active": False,
        "mode": None,            # "NEW" or "MOVE"
        "value": None,           # widget_type (for NEW) or widget_id (for MOVE)
        "label": "",
        "hovered_target": None   # dict describing where the widget will drop
    },
    # App-only Background & Appearance state
    "appearance": {
        "preset": "Dark Slate (Default)",
        "vp_color": [18, 22, 30, 255],
        "win_color": [28, 32, 42, 255],
    },
    "bg_image": {
        "texture_tag": None,
        "path": "",
        "opacity": 1.0,
    }
}

_rendered_canvas_window_ids = set()


# ==========================================
# 2. DATA CONVERSION & STATE HELPERS
# ==========================================
def new_uid(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:6]}"


C_INT_MIN = -2_147_483_647
C_INT_MAX = 2_147_483_647
C_FLOAT_LIMIT = 1e30


def safe_int(val, default=0, min_val=C_INT_MIN, max_val=C_INT_MAX):
    try:
        num = int(float(val))
    except (ValueError, TypeError, OverflowError):
        return default
    return max(min_val, min(max_val, num))


def safe_float(val, default=0.0, min_val=-C_FLOAT_LIMIT, max_val=C_FLOAT_LIMIT):
    try:
        num = float(val)
    except (ValueError, TypeError, OverflowError):
        return default
    if not math.isfinite(num):
        return default
    return max(min_val, min(max_val, num))


def safe_bool(val, default=True):
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "yes", "on")
    return default


def parse_rgba_list(val, default=(100, 180, 255, 255)):
    """Parses a string 'R, G, B, A' or list/tuple into [R, G, B, A] ints (0..255)."""
    if isinstance(val, (list, tuple)):
        nums = [safe_int(x, 255) for x in val[:4]]
    elif isinstance(val, str):
        parts = [p.strip() for p in val.strip("[]() ").split(",") if p.strip()]
        nums = [safe_int(p, 255) for p in parts[:4]]
    else:
        nums = list(default)
    while len(nums) < 4:
        nums.append(255)
    return [max(0, min(255, x)) for x in nums[:4]]


def sanitize_id(raw_id, fallback_prefix="el"):
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", str(raw_id or "").strip())
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"{fallback_prefix}_{cleaned}" if cleaned else new_uid(fallback_prefix)
    return cleaned


def _iter_window_containers(win):
    """Yields (tab_or_None, rows_list) for the root window and each of its tabs."""
    yield None, win["rows"]
    for tab in win.get("tabs", []):
        yield tab, tab["rows"]


def _iter_all_widgets():
    """Yields (win, tab_or_None, row, r_idx, w_idx, widget) across all windows and tabs."""
    for win in state["windows"]:
        for tab, rows in _iter_window_containers(win):
            for r_idx, r in enumerate(rows):
                for w_idx, w in enumerate(r["widgets"]):
                    yield win, tab, r, r_idx, w_idx, w


def is_widget_id_taken(candidate_id, exclude_widget=None):
    return any(w is not exclude_widget and w["id"] == candidate_id for _, _, _, _, _, w in _iter_all_widgets())


def get_window(window_id):
    return next((w for w in state["windows"] if w["id"] == window_id), None)


def get_tab(window_id, tab_id):
    if not tab_id:
        return None
    win = get_window(window_id)
    return next((t for t in win.get("tabs", []) if t["id"] == tab_id), None) if win else None


def get_container_rows(window_id, tab_id=None):
    """Returns the rows list for either a specific tab or the window's root."""
    if tab_id:
        tab = get_tab(window_id, tab_id)
        if tab is not None:
            return tab["rows"]
    win = get_window(window_id)
    return win["rows"] if win else None


def find_widget(widget_id):
    """Returns (win, tab_or_None, row, r_idx, w_idx, widget)."""
    for item in _iter_all_widgets():
        if item[5]["id"] == widget_id:
            return item
    return None, None, None, None, None, None


def sync_window_rects_from_dpg():
    """Keep user-moved window positions and sizes in sync with state."""
    for win in state["windows"]:
        win_tag = f"canvas_{win['id']}"
        if dpg.does_item_exist(win_tag):
            win["pos"] = list(dpg.get_item_pos(win_tag))
            win["width"] = dpg.get_item_width(win_tag)
            win["height"] = dpg.get_item_height(win_tag)


def cleanup_empty_rows():
    """Keep at least one row per window and per tab, removing extra empty rows."""
    for win in state["windows"]:
        for _, rows in _iter_window_containers(win):
            if len(rows) > 1:
                non_empty = [r for r in rows if r["widgets"]]
                rows[:] = non_empty if non_empty else [rows[0]]


def refresh_ui(canvas=True, outliner=True, inspector=True):
    if canvas:
        render_canvas()
    if outliner:
        update_outliner()
    if inspector:
        update_inspector()


def create_widget_data(widget_type):
    spec = WIDGET_SPECS.get(widget_type, WIDGET_SPECS["Button"])
    uid = new_uid("el")
    short_id = uid.split("_")[1][:4]
    return {
        "id": uid,
        "type": widget_type,
        "label": f"{widget_type}_{short_id}",
        "width": spec.get("width", 0),
        "height": spec.get("height", 0),
        "default_value": spec.get("default_value", ""),
        "min_value": spec.get("min_value", 0),
        "max_value": spec.get("max_value", 100),
        "items": ["Option 1", "Option 2", "Option 3"],
        "wrap": 0,
        "enabled": True,
        "show": True,
        "locked": False,
    }


def add_user_window():
    sync_window_rects_from_dpg()
    new_id = new_uid("win")
    idx = len(state["windows"]) + 1
    row_id = new_uid("row")
    new_window = {
        "id": new_id,
        "title": f"Window {idx}",
        "pos": [455 + (idx * 25), 20 + (idx * 25)],
        "width": 520,
        "height": 420,
        "rows": [{"id": row_id, "widgets": []}],
        "tabs": [],
        "active_tab_id": None,
    }
    state["windows"].append(new_window)
    select_window(new_id)


def delete_user_window(window_id=None):
    if len(state["windows"]) <= 1:
        return
    if window_id is None:
        window_id = state["selected_target"]["window_id"]
    sync_window_rects_from_dpg()
    state["windows"] = [w for w in state["windows"] if w["id"] != window_id]
    select_window(state["windows"][0]["id"])


def add_tab_to_window(window_id=None):
    sync_window_rects_from_dpg()
    if window_id is None:
        window_id = state["selected_target"]["window_id"] or state["windows"][0]["id"]
    win = get_window(window_id)
    if not win:
        return None
    win.setdefault("tabs", [])
    idx = len(win["tabs"]) + 1
    tab_id = new_uid("tab")
    row_id = new_uid("row")
    new_tab = {
        "id": tab_id,
        "title": f"Tab {idx}",
        "rows": [{"id": row_id, "widgets": []}],
    }
    win["tabs"].append(new_tab)
    win["active_tab_id"] = tab_id
    select_tab(win["id"], tab_id)
    return tab_id


def delete_tab(window_id, tab_id):
    sync_window_rects_from_dpg()
    win = get_window(window_id)
    if not win or "tabs" not in win:
        return
    win["tabs"] = [t for t in win["tabs"] if t["id"] != tab_id]
    if win.get("active_tab_id") == tab_id:
        win["active_tab_id"] = win["tabs"][0]["id"] if win["tabs"] else None
    if win["tabs"]:
        select_tab(win["id"], win["active_tab_id"])
    else:
        select_window(win["id"])


def delete_selected_tab():
    target = state["selected_target"]
    win_id = target.get("window_id")
    tab_id = target.get("tab_id")
    if not tab_id and win_id:
        win = get_window(win_id)
        if win and win.get("active_tab_id"):
            tab_id = win["active_tab_id"]
    if win_id and tab_id:
        delete_tab(win_id, tab_id)


def move_tab_order(step):
    target = state["selected_target"]
    win = get_window(target.get("window_id"))
    tab_id = target.get("tab_id")
    if not win or not tab_id:
        return
    tabs = win.get("tabs", [])
    idx = next((i for i, t in enumerate(tabs) if t["id"] == tab_id), None)
    if idx is None:
        return
    new_idx = idx + step
    if 0 <= new_idx < len(tabs):
        tabs[idx], tabs[new_idx] = tabs[new_idx], tabs[idx]
        refresh_ui()


def add_new_row_to_container(window_id, tab_id=None, insert_idx=None):
    rows = get_container_rows(window_id, tab_id)
    if rows is None:
        return None
    new_row_id = new_uid("row")
    new_row = {"id": new_row_id, "widgets": []}
    if insert_idx is None or not (0 <= insert_idx <= len(rows)):
        rows.append(new_row)
    else:
        rows.insert(insert_idx, new_row)
    return new_row_id


def add_widget_to_target(window_id, row_id, widget_type, col_index=None, tab_id=None):
    win = get_window(window_id)
    if not win:
        return
    rows = get_container_rows(window_id, tab_id)
    if rows is None:
        return

    row = next((r for r in rows if r["id"] == row_id), None)
    if not row:
        if not rows:
            row_id = add_new_row_to_container(window_id, tab_id=tab_id)
            row = next((r for r in rows if r["id"] == row_id), None)
        else:
            row = rows[-1]
            row_id = row["id"]

    new_widget = create_widget_data(widget_type)
    if col_index is None or not (0 <= col_index <= len(row["widgets"])):
        row["widgets"].append(new_widget)
    else:
        row["widgets"].insert(col_index, new_widget)

    if tab_id:
        win["active_tab_id"] = tab_id

    cleanup_empty_rows()
    select_widget(window_id, row_id, new_widget["id"], tab_id=tab_id)


def add_widget_from_palette(widget_type, new_row=False):
    sync_window_rects_from_dpg()
    target = state["selected_target"]
    win_id = target["window_id"] or state["windows"][0]["id"]
    win = get_window(win_id)
    if not win:
        win = state["windows"][0]
        win_id = win["id"]

    tab_id = target.get("tab_id")
    if tab_id and not get_tab(win_id, tab_id):
        tab_id = None
    if tab_id is None and win.get("tabs") and target["type"] == "window":
        tab_id = win.get("active_tab_id") or win["tabs"][0]["id"]

    rows = get_container_rows(win_id, tab_id)
    if new_row or not rows:
        if rows and not rows[-1]["widgets"]:
            row_id = rows[-1]["id"]
        else:
            row_id = add_new_row_to_container(win_id, tab_id=tab_id)
    else:
        row_id = target["row_id"]
        if not any(r["id"] == row_id for r in rows):
            row_id = rows[-1]["id"]

    add_widget_to_target(win_id, row_id, widget_type, tab_id=tab_id)


def duplicate_selected_widget():
    """Clones the currently selected widget right next to it in the same row."""
    target = state["selected_target"]
    if target["type"] != "widget":
        return
    win, tab, row, _, w_idx, widget = find_widget(target["widget_id"])
    if not widget:
        return
    cloned = dict(widget)
    cloned["id"] = new_uid("el")
    cloned["label"] = f"{widget.get('label', widget['type'])}_copy"
    cloned["items"] = list(widget.get("items", []))
    row["widgets"].insert(w_idx + 1, cloned)
    tab_id = tab["id"] if tab else None
    select_widget(win["id"], row["id"], cloned["id"], tab_id=tab_id)


def move_existing_widget(widget_id, target_win_id, target_row_id, target_col_idx=None, target_tab_id=None):
    _, _, src_row, _, src_w_idx, widget = find_widget(widget_id)
    if not widget or widget.get("locked", False):
        return

    dest_win = get_window(target_win_id)
    if not dest_win:
        return
    dest_rows = get_container_rows(target_win_id, target_tab_id)
    if dest_rows is None:
        return

    dest_row = next((r for r in dest_rows if r["id"] == target_row_id), None)
    if not dest_row:
        if not dest_rows:
            target_row_id = add_new_row_to_container(target_win_id, tab_id=target_tab_id)
            dest_row = next((r for r in dest_rows if r["id"] == target_row_id), None)
        else:
            dest_row = dest_rows[-1]
            target_row_id = dest_row["id"]

    if src_row["id"] == dest_row["id"] and target_col_idx is not None and target_col_idx > src_w_idx:
        target_col_idx -= 1

    src_row["widgets"].remove(widget)

    if target_col_idx is None or not (0 <= target_col_idx <= len(dest_row["widgets"])):
        dest_row["widgets"].append(widget)
    else:
        dest_row["widgets"].insert(target_col_idx, widget)

    if target_tab_id:
        dest_win["active_tab_id"] = target_tab_id

    cleanup_empty_rows()
    select_widget(target_win_id, target_row_id, widget["id"], tab_id=target_tab_id)


def move_widget_fine(direction_axis, step):
    target = state["selected_target"]
    if target["type"] != "widget":
        return
    win, tab, row, r_idx, w_idx, widget = find_widget(target["widget_id"])
    if not widget or widget.get("locked", False):
        return
    tab_id = tab["id"] if tab else None
    rows = tab["rows"] if tab else win["rows"]

    if direction_axis == "horizontal":
        new_w_idx = w_idx + step
        if 0 <= new_w_idx < len(row["widgets"]):
            row["widgets"][w_idx], row["widgets"][new_w_idx] = (
                row["widgets"][new_w_idx],
                row["widgets"][w_idx],
            )
            refresh_ui(inspector=True)

    elif direction_axis == "vertical":
        new_r_idx = r_idx + step
        row["widgets"].pop(w_idx)

        if new_r_idx >= len(rows):
            new_r_id = add_new_row_to_container(win["id"], tab_id=tab_id)
            target_row = next(r for r in rows if r["id"] == new_r_id)
        elif new_r_idx < 0:
            new_r_id = add_new_row_to_container(win["id"], tab_id=tab_id, insert_idx=0)
            target_row = next(r for r in rows if r["id"] == new_r_id)
        else:
            target_row = rows[new_r_idx]

        target_row["widgets"].append(widget)
        state["selected_target"]["row_id"] = target_row["id"]

        cleanup_empty_rows()
        refresh_ui(inspector=True)


def delete_selected_widget():
    """Deletes the selected widget (- Col)."""
    target = state["selected_target"]
    if target["type"] != "widget":
        return
    win, tab, row, _, w_idx, widget = find_widget(target["widget_id"])
    if widget:
        tab_id = tab["id"] if tab else None
        rows = tab["rows"] if tab else win["rows"]
        row["widgets"].remove(widget)
        cleanup_empty_rows()
        if row in rows and row["widgets"]:
            next_w = row["widgets"][min(w_idx, len(row["widgets"]) - 1)]
            select_widget(win["id"], row["id"], next_w["id"], tab_id=tab_id)
        elif tab:
            select_tab(win["id"], tab["id"])
        else:
            select_window(win["id"])


def delete_row(window_id, row_id, tab_id=None):
    """Deletes an entire row (- Row) from a window or tab."""
    rows = get_container_rows(window_id, tab_id)
    if rows is None:
        return
    rows[:] = [r for r in rows if r["id"] != row_id]
    if not rows:
        rows.append({"id": new_uid("row"), "widgets": []})
    if tab_id:
        select_tab(window_id, tab_id)
    else:
        select_window(window_id)


def delete_selected_row():
    target = state["selected_target"]
    win_id = target.get("window_id")
    row_id = target.get("row_id")
    tab_id = target.get("tab_id")
    if win_id and row_id:
        delete_row(win_id, row_id, tab_id=tab_id)


def select_window(window_id):
    win = get_window(window_id)
    if not win:
        return
    row_id = win["rows"][0]["id"] if win["rows"] else None
    state["selected_target"] = {
        "type": "window",
        "window_id": window_id,
        "tab_id": None,
        "row_id": row_id,
        "widget_id": None
    }
    refresh_ui()


def select_tab(window_id, tab_id):
    win = get_window(window_id)
    tab = get_tab(window_id, tab_id)
    if not win or not tab:
        return
    win["active_tab_id"] = tab_id
    row_id = tab["rows"][0]["id"] if tab["rows"] else None
    state["selected_target"] = {
        "type": "tab",
        "window_id": window_id,
        "tab_id": tab_id,
        "row_id": row_id,
        "widget_id": None,
    }
    refresh_ui()


def select_widget(window_id, row_id, widget_id, tab_id=None):
    if tab_id is None:
        _, tab, _, _, _, _ = find_widget(widget_id)
        if tab:
            tab_id = tab["id"]
    win = get_window(window_id)
    if win and tab_id:
        win["active_tab_id"] = tab_id
    state["selected_target"] = {
        "type": "widget",
        "window_id": window_id,
        "tab_id": tab_id,
        "row_id": row_id,
        "widget_id": widget_id
    }
    refresh_ui()


def on_canvas_tab_change(sender, app_data, win_id):
    """Called when the user clicks a tab header directly on the Canvas window."""
    win = get_window(win_id)
    if not win:
        return
    alias = dpg.get_item_alias(app_data) if isinstance(app_data, int) else app_data
    if isinstance(alias, str) and alias.startswith("canvas_tab_"):
        tab_id = alias.replace("canvas_tab_", "")
        tab = get_tab(win_id, tab_id)
        if tab:
            win["active_tab_id"] = tab_id
            state["selected_target"] = {
                "type": "tab",
                "window_id": win_id,
                "tab_id": tab_id,
                "row_id": tab["rows"][0]["id"] if tab["rows"] else None,
                "widget_id": None,
            }
            update_outliner()
            update_inspector()


# ==========================================
# 3. GLOBAL COORDINATE DRAG & DROP SYSTEM
# ==========================================
def _get_group_rect(group_tag):
    """Returns (rx1, ry1, rx2, ry2) for any dpg.group or selectable/tree_node/tab."""
    if not dpg.does_item_exist(group_tag):
        return None
    st = dpg.get_item_state(group_tag)
    if not st.get("visible", True):
        return None
    rmin = st.get("rect_min")
    rmax = st.get("rect_max")
    if rmin and rmax:
        return rmin[0], rmin[1], rmax[0], rmax[1]
    return None


def _is_point_in_group(mx, my, group_tag, pad_x=0, pad_y=0):
    rect = _get_group_rect(group_tag)
    if not rect:
        return False
    rx1, ry1, rx2, ry2 = rect
    return (rx1 - pad_x) <= mx <= (rx2 + pad_x) and (ry1 - pad_y) <= my <= (ry2 + pad_y)


def _build_widget_dpg_kwargs(w):
    """Builds the exact DearPyGui keyword arguments dictionary for widget `w` from WIDGET_SPECS."""
    t = w["type"]
    spec = WIDGET_SPECS.get(t, WIDGET_SPECS["Button"])
    val_converters = {
        "str": lambda v: str(v if v is not None else ""),
        "int": lambda v: safe_int(v, 0),
        "float": lambda v: safe_float(v, 0.5),
        "bool": lambda v: safe_bool(v, True),
        "rgba": parse_rgba_list,
    }
    minmax_converters = {
        "int": (lambda v: safe_int(v, 0), lambda v: safe_int(v, 100)),
        "float": (lambda v: safe_float(v, 0.0), lambda v: safe_float(v, 1.0)),
    }

    kw = {}
    label_kw = spec.get("label_kw")
    if label_kw:
        kw[label_kw] = str(w.get("label", ""))

    if spec.get("has_items"):
        items = list(w.get("items") or ["Option 1", "Option 2"])
        kw["items"] = items
        if t == "Listbox":
            kw["num_items"] = min(4, max(2, len(items)))

    val_type = spec.get("val_type")
    if val_type == "first_item":
        items = kw.get("items") or ["Option 1"]
        kw["default_value"] = items[0] if items else ""
    elif val_type in val_converters:
        kw["default_value"] = val_converters[val_type](w.get("default_value"))

    mm_type = spec.get("minmax_type")
    if spec.get("has_minmax") and mm_type in minmax_converters:
        min_fn, max_fn = minmax_converters[mm_type]
        kw["min_value"] = min_fn(w.get("min_value", spec.get("min_value", 0)))
        kw["max_value"] = max_fn(w.get("max_value", spec.get("max_value", 1)))

    wrap = safe_int(w.get("wrap", 0), 0, 0, 10000)
    if spec.get("has_wrap") and wrap > 0:
        kw["wrap"] = wrap

    if spec.get("extra_kw"):
        kw.update(spec["extra_kw"])

    width = safe_int(w.get("width", 0), 0, 0, 10000)
    height = safe_int(w.get("height", 0), 0, 0, 10000)
    if spec.get("has_width") and width > 0:
        kw["width"] = width
    if spec.get("has_height") and height > 0:
        kw["height"] = height

    return kw


def render_widget_preview(w_type, w_data=None, parent=None):
    """Renders a live visual preview of the widget inside the floating drag ghost using WIDGET_SPECS."""
    sample = dict(w_data) if w_data else create_widget_data(w_type)
    if not w_data:
        sample["label"] = f"Sample {w_type}"
    kw = _build_widget_dpg_kwargs(sample)
    if parent:
        kw["parent"] = parent
    spec = WIDGET_SPECS.get(w_type, WIDGET_SPECS["Button"])
    getattr(dpg, spec["dpg_func"])(**kw)


def _iter_visible_canvas_widgets(win):
    """Yields (tab_id_or_None, row, r_idx, w_idx, w) for currently visible widgets in win."""
    for r_idx, row in enumerate(win["rows"]):
        for w_idx, w in enumerate(row["widgets"]):
            yield None, row, r_idx, w_idx, w
    active_tid = win.get("active_tab_id")
    if active_tid:
        active_tab = get_tab(win["id"], active_tid)
        if active_tab:
            for r_idx, row in enumerate(active_tab["rows"]):
                for w_idx, w in enumerate(row["widgets"]):
                    yield active_tid, row, r_idx, w_idx, w


def on_global_mouse_down(sender, app_data):
    """Detects LMB press on any Palette item, Outliner item, or Canvas widget."""
    mx, my = dpg.get_mouse_pos(local=False)

    # Close RMB context menu if clicking outside of it
    if dpg.does_item_exist("rmb_context_win") and dpg.is_item_shown("rmb_context_win"):
        cx, cy = dpg.get_item_pos("rmb_context_win")
        cw, ch = dpg.get_item_rect_size("rmb_context_win")
        if cx <= mx <= cx + cw and cy <= my <= cy + ch:
            return
        dpg.hide_item("rmb_context_win")

    # 1. Check Palette items
    for w_type in WIDGET_TYPES:
        p_box_tag = f"palette_box_{w_type}"
        if _is_point_in_group(mx, my, p_box_tag, pad_x=2, pad_y=2):
            state["drag"]["pending"] = ("NEW", w_type, f"New {w_type}", (mx, my))
            return

    # 2. Check Outliner items (both on Elements tab mini-list and Outliner tab)
    for prefix in ("outliner_w_", "mini_outliner_w_"):
        for _, _, _, _, _, w in _iter_all_widgets():
            if _is_point_in_group(mx, my, f"{prefix}{w['id']}"):
                if not w.get("locked", False):
                    state["drag"]["pending"] = ("MOVE", w["id"], f"{w['type']}: {w['label']}", (mx, my))
                return

    # 3. Check Canvas Windows & Widgets (from top window to bottom)
    for win in reversed(state["windows"]):
        win_tag = f"canvas_{win['id']}"
        if not dpg.does_item_exist(win_tag):
            continue
        wx, wy = dpg.get_item_pos(win_tag)
        ww = dpg.get_item_width(win_tag)
        wh = dpg.get_item_height(win_tag)

        if wx <= mx <= wx + ww and wy <= my <= wy + wh:
            if my <= wy + 26:
                return
            for tab in win.get("tabs", []):
                if _is_point_in_group(mx, my, f"canvas_tab_{tab['id']}", pad_x=2, pad_y=2):
                    return
            for tab_id, row, _, _, w in _iter_visible_canvas_widgets(win):
                w_box_tag = f"wbox_{w['id']}"
                if _is_point_in_group(mx, my, w_box_tag, pad_x=3, pad_y=3):
                    if not w.get("locked", False):
                        state["drag"]["pending"] = ("MOVE", w["id"], f"{w['type']}: {w['label']}", (mx, my))
                    select_widget(win["id"], row["id"], w["id"], tab_id=tab_id)
                    return
            return


def open_rmb_context_menu(win, tab_id, row, w, mx, my):
    """Populates and shows the floating RMB context popup for the clicked widget."""
    select_widget(win["id"], row["id"], w["id"], tab_id=tab_id)
    if not dpg.does_item_exist("rmb_context_win"):
        return

    w_type = w["type"]
    spec = WIDGET_SPECS.get(w_type, WIDGET_SPECS["Button"])
    dpg.set_value("ctx_wgt_header", f"[{w_type}] ({w['id']})")
    dpg.set_value("ctx_wgt_id_input", w["id"])

    dpg.configure_item("ctx_label_group", show=spec["has_label"])
    if spec["has_label"]:
        dpg.set_value("ctx_wgt_label", w.get("label", ""))

    dpg.configure_item("ctx_defval_group", show=spec["has_defval"])
    if spec["has_defval"]:
        dpg.set_value("ctx_wgt_defval", str(w.get("default_value", "")))

    dpg.configure_item("ctx_items_group", show=spec["has_items"])
    if spec["has_items"]:
        dpg.set_value("ctx_wgt_items", ", ".join(w.get("items", [])))

    dpg.set_value("ctx_wgt_enabled", bool(w.get("enabled", True)))
    dpg.set_value("ctx_wgt_show", bool(w.get("show", True)))
    dpg.set_value("ctx_wgt_locked", bool(w.get("locked", False)))

    vw = dpg.get_viewport_client_width() or 1440
    vh = dpg.get_viewport_client_height() or 840
    px = min(max(10, int(mx)), vw - 290)
    py = min(max(10, int(my)), vh - 350)

    dpg.set_item_pos("rmb_context_win", [px, py])
    dpg.show_item("rmb_context_win")
    dpg.focus_item("rmb_context_win")


def on_global_right_click(sender, app_data):
    """Detects RMB click on any placed widget on Canvas or in Outliner to open its context menu."""
    mx, my = dpg.get_mouse_pos(local=False)

    # 1. Check Outliner items
    for prefix in ("outliner_w_", "mini_outliner_w_"):
        for win, tab, r, _, _, w in _iter_all_widgets():
            if _is_point_in_group(mx, my, f"{prefix}{w['id']}"):
                open_rmb_context_menu(win, tab["id"] if tab else None, r, w, mx, my)
                return

    # 2. Check Canvas widgets
    for win in reversed(state["windows"]):
        win_tag = f"canvas_{win['id']}"
        if not dpg.does_item_exist(win_tag):
            continue
        wx, wy = dpg.get_item_pos(win_tag)
        ww = dpg.get_item_width(win_tag)
        wh = dpg.get_item_height(win_tag)

        if wx <= mx <= wx + ww and wy <= my <= wy + wh:
            for tab_id, row, _, _, w in _iter_visible_canvas_widgets(win):
                w_box_tag = f"wbox_{w['id']}"
                if _is_point_in_group(mx, my, w_box_tag, pad_x=3, pad_y=3):
                    open_rmb_context_menu(win, tab_id, row, w, mx, my)
                    return
            return


def _check_rows_hit(mx, my, win, rows, tab_id=None, context_label=""):
    """Checks if (mx, my) hits a widget or row inside `rows`."""
    prefix_str = f"[{context_label}] " if context_label else ""
    for r_idx, row in enumerate(rows):
        if not row["widgets"]:
            continue
        row_min_y = None
        row_max_y = None
        for w_idx, w in enumerate(row["widgets"]):
            w_box_tag = f"wbox_{w['id']}"
            rect = _get_group_rect(w_box_tag)
            if not rect:
                continue
            rx, ry, rx2, ry2 = rect
            row_min_y = ry if row_min_y is None else min(row_min_y, ry)
            row_max_y = ry2 if row_max_y is None else max(row_max_y, ry2)

            if rx - 6 <= mx <= rx2 + 6 and ry - 4 <= my <= ry2 + 4:
                mid_x = (rx + rx2) / 2.0
                if mx < mid_x:
                    return {
                        "action": "insert_col",
                        "win_id": win["id"],
                        "tab_id": tab_id,
                        "row_id": row["id"],
                        "col_idx": w_idx,
                        "desc": f"{prefix_str}Row {r_idx + 1}: Left of [{w['label']}]",
                    }
                else:
                    return {
                        "action": "insert_col",
                        "win_id": win["id"],
                        "tab_id": tab_id,
                        "row_id": row["id"],
                        "col_idx": w_idx + 1,
                        "desc": f"{prefix_str}Row {r_idx + 1}: Right of [{w['label']}]",
                    }

        if row_min_y is not None and (row_min_y - 4 <= my <= row_max_y + 4):
            return {
                "action": "append_row",
                "win_id": win["id"],
                "tab_id": tab_id,
                "row_id": row["id"],
                "desc": f"{prefix_str}Row {r_idx + 1}: Append to end of row",
            }
    return None


def _compute_drop_target_at(mx, my):
    """Geometry hit-test to find which canvas window, tab, row, or widget is under (mx, my)."""
    # 1. Check Outliner trees (both main Outliner and quick Outliner)
    for row_prefix, w_prefix, tab_prefix in (
        ("outliner_row_", "outliner_w_", "outliner_tab_"),
        ("mini_outliner_row_", "mini_outliner_w_", "mini_outliner_tab_"),
    ):
        for win in state["windows"]:
            for tab, rows in _iter_window_containers(win):
                tid = tab["id"] if tab else None
                t_prefix = f"[{tab['title']}] " if tab else ""
                for r_idx, row in enumerate(rows):
                    for w_idx, w in enumerate(row["widgets"]):
                        if _is_point_in_group(mx, my, f"{w_prefix}{w['id']}"):
                            return {
                                "action": "insert_col",
                                "win_id": win["id"],
                                "tab_id": tid,
                                "row_id": row["id"],
                                "col_idx": w_idx,
                                "desc": f"{t_prefix}Insert before {w['label']} (Row {r_idx + 1})",
                            }
                    if _is_point_in_group(mx, my, f"{row_prefix}{row['id']}"):
                        return {
                            "action": "append_row",
                            "win_id": win["id"],
                            "tab_id": tid,
                            "row_id": row["id"],
                            "desc": f"{t_prefix}Append to Row {r_idx + 1}",
                        }
                if tab and _is_point_in_group(mx, my, f"{tab_prefix}{tid}"):
                    return {
                        "action": "new_row",
                        "win_id": win["id"],
                        "tab_id": tid,
                        "desc": f"Drop into Tab '{tab['title']}' (New Row)",
                    }

    # 2. Check Canvas Windows, Tab headers, & Widget wrapper groups
    for win in reversed(state["windows"]):
        win_tag = f"canvas_{win['id']}"
        if not dpg.does_item_exist(win_tag):
            continue
        wx, wy = dpg.get_item_pos(win_tag)
        ww = dpg.get_item_width(win_tag)
        wh = dpg.get_item_height(win_tag)

        if wx <= mx <= wx + ww and wy <= my <= wy + wh:
            for tab in win.get("tabs", []):
                c_tab_tag = f"canvas_tab_{tab['id']}"
                if _is_point_in_group(mx, my, c_tab_tag, pad_x=2, pad_y=2):
                    if win.get("active_tab_id") != tab["id"]:
                        win["active_tab_id"] = tab["id"]
                        tb_tag = f"canvas_tabbar_{win['id']}"
                        if dpg.does_item_exist(tb_tag):
                            dpg.set_value(tb_tag, c_tab_tag)
                    return {
                        "action": "new_row",
                        "win_id": win["id"],
                        "tab_id": tab["id"],
                        "desc": f"Drop into Tab '{tab['title']}' (New Row)",
                    }

            active_tid = win.get("active_tab_id")
            if win.get("tabs") and active_tid:
                active_tab = get_tab(win["id"], active_tid)
                if active_tab:
                    hit = _check_rows_hit(mx, my, win, active_tab["rows"], tab_id=active_tid, context_label=active_tab["title"])
                    if hit:
                        return hit

            hit_root = _check_rows_hit(mx, my, win, win["rows"], tab_id=None, context_label="")
            if hit_root:
                return hit_root

            if win.get("tabs") and active_tid:
                active_tab = get_tab(win["id"], active_tid)
                t_name = active_tab["title"] if active_tab else "Tab"
                return {
                    "action": "new_row",
                    "win_id": win["id"],
                    "tab_id": active_tid,
                    "desc": f"{win['title']} -> [{t_name}]: Drop as New Row",
                }

            return {
                "action": "new_row",
                "win_id": win["id"],
                "tab_id": None,
                "desc": f"{win['title']}: Drop as New Row",
            }

    return None


def _start_active_drag(mode, value, label):
    drag = state["drag"]
    drag["active"] = True
    drag["mode"] = mode
    drag["value"] = value
    drag["label"] = label

    if dpg.does_item_exist("drag_ghost_preview_box"):
        dpg.delete_item("drag_ghost_preview_box", children_only=True)
        if mode == "NEW":
            render_widget_preview(value, parent="drag_ghost_preview_box")
        elif mode == "MOVE":
            _, _, _, _, _, w_data = find_widget(value)
            if w_data:
                render_widget_preview(w_data["type"], w_data, parent="drag_ghost_preview_box")

    if dpg.does_item_exist("drag_ghost_win"):
        dpg.show_item("drag_ghost_win")
        dpg.focus_item("drag_ghost_win")


def on_global_mouse_move(sender, app_data):
    drag = state["drag"]
    if not drag["pending"] and not drag["active"]:
        return

    mx, my = dpg.get_mouse_pos(local=False)

    if drag["pending"] and not drag["active"]:
        mode, value, label, (sx, sy) = drag["pending"]
        if abs(mx - sx) > 4 or abs(my - sy) > 4:
            _start_active_drag(mode, value, label)

    if drag["active"]:
        target = _compute_drop_target_at(mx, my)
        drag["hovered_target"] = target

        if dpg.does_item_exist("drag_ghost_win"):
            dpg.set_item_pos("drag_ghost_win", [mx + 16, my + 16])
            dpg.focus_item("drag_ghost_win")
        if dpg.does_item_exist("drag_ghost_status"):
            if target:
                dpg.set_value("drag_ghost_status", f"-> {target['desc']}")
                dpg.configure_item("drag_ghost_status", color=(100, 255, 130))
            else:
                dpg.set_value("drag_ghost_status", "Drag onto Canvas Window, Tab, or Outliner to drop")
                dpg.configure_item("drag_ghost_status", color=(255, 190, 90))


def on_global_mouse_release(sender, app_data):
    drag = state["drag"]
    was_active = drag["active"]
    mode = drag["mode"]
    value = drag["value"]
    target = drag["hovered_target"]

    drag["pending"] = None
    drag["active"] = False
    drag["mode"] = None
    drag["value"] = None
    drag["hovered_target"] = None

    if dpg.does_item_exist("drag_ghost_win"):
        dpg.hide_item("drag_ghost_win")

    if not was_active or not target:
        return

    win_id = target["win_id"]
    tab_id = target.get("tab_id")
    action = target["action"]

    if action == "new_row":
        rows = get_container_rows(win_id, tab_id)
        if rows and not rows[-1]["widgets"]:
            row_id = rows[-1]["id"]
        else:
            row_id = add_new_row_to_container(win_id, tab_id=tab_id)
        col_idx = None
    elif action == "append_row":
        row_id = target["row_id"]
        col_idx = None
    elif action == "insert_col":
        row_id = target["row_id"]
        col_idx = target["col_idx"]
    else:
        return

    if mode == "NEW":
        add_widget_to_target(win_id, row_id, value, col_index=col_idx, tab_id=tab_id)
    elif mode == "MOVE":
        move_existing_widget(value, win_id, row_id, target_col_idx=col_idx, target_tab_id=tab_id)


# ==========================================
# 4. CANVAS RENDERER
# ==========================================
def _render_single_widget(w, w_tag):
    t = w["type"]
    spec = WIDGET_SPECS.get(t, WIDGET_SPECS["Button"])
    is_enabled = bool(w.get("enabled", True))
    is_shown = bool(w.get("show", True))

    if not is_shown:
        dpg.add_button(
            label=f"[Hidden {t}] {w.get('label', '')}",
            tag=w_tag,
            enabled=False,
            width=w.get("width", 0) or 140,
        )
        return

    kwargs = _build_widget_dpg_kwargs(w)
    kwargs["tag"] = w_tag
    if not is_enabled:
        if spec["supports_enabled"]:
            kwargs["enabled"] = False
        elif t == "Text":
            kwargs["color"] = (120, 120, 120)

    if t == "Spacer":
        kwargs.setdefault("height", 15)
        kwargs.setdefault("width", 40)

    getattr(dpg, spec["dpg_func"])(**kwargs)
    if t == "Separator":
        dpg.add_spacer(width=80, height=4)


def _render_rows_block(rows):
    for row in rows:
        if not row["widgets"]:
            continue
        row_tag = f"canvas_row_{row['id']}"
        with dpg.group(tag=row_tag, horizontal=True):
            for w in row["widgets"]:
                w_tag = f"widget_{w['id']}"
                w_box_tag = f"wbox_{w['id']}"
                with dpg.group(tag=w_box_tag):
                    _render_single_widget(w, w_tag)

                is_selected = (
                    state["selected_target"]["type"] == "widget"
                    and state["selected_target"]["widget_id"] == w["id"]
                )
                if is_selected:
                    dpg.bind_item_theme(w_tag, "selected_widget_theme")


def render_canvas():
    global _rendered_canvas_window_ids
    sync_window_rects_from_dpg()

    current_window_tags = {f"canvas_{w['id']}" for w in state["windows"]}
    for old_tag in list(_rendered_canvas_window_ids - current_window_tags):
        if dpg.does_item_exist(old_tag):
            dpg.delete_item(old_tag)
    _rendered_canvas_window_ids = current_window_tags

    for win in state["windows"]:
        win_tag = f"canvas_{win['id']}"
        child_tag = f"child_canvas_{win['id']}"

        is_win_selected = (
            state["selected_target"]["type"] in ("window", "tab")
            and state["selected_target"]["window_id"] == win["id"]
        )
        title = f"{'[ACTIVE] ' if is_win_selected else ''}{win['title']}"

        if not dpg.does_item_exist(win_tag):
            dpg.add_window(
                label=title,
                tag=win_tag,
                pos=win["pos"],
                width=win["width"],
                height=win["height"],
                no_close=False,
                on_close=lambda s, a, u=win["id"]: delete_user_window(u)
            )
        else:
            dpg.set_item_label(win_tag, title)
            dpg.set_item_pos(win_tag, win["pos"])
            dpg.set_item_width(win_tag, win["width"])
            dpg.set_item_height(win_tag, win["height"])
            dpg.delete_item(win_tag, children_only=True)

        with dpg.child_window(tag=child_tag, parent=win_tag, border=False, width=-1, height=-1):
            has_root_widgets = any(r["widgets"] for r in win["rows"])
            has_tabs = bool(win.get("tabs"))

            if not has_root_widgets and not has_tabs:
                dpg.add_text(
                    "Drag any widget here from Palette (or click '+ Row' / '+ Col' / '+ Tab').\n"
                    "- Drop on empty area -> adds a New Row\n"
                    "- Drop on existing widget -> inserts Left/Right in the same Row\n"
                    "- Right-click any placed widget for quick parameters!",
                    color=(140, 140, 140),
                )

            _render_rows_block(win["rows"])

            if has_tabs:
                tb_tag = f"canvas_tabbar_{win['id']}"
                with dpg.tab_bar(tag=tb_tag, user_data=win["id"], callback=on_canvas_tab_change):
                    for tab in win["tabs"]:
                        c_tab_tag = f"canvas_tab_{tab['id']}"
                        with dpg.tab(label=tab["title"], tag=c_tab_tag):
                            has_tab_widgets = any(r["widgets"] for r in tab["rows"])
                            if not has_tab_widgets:
                                dpg.add_text(
                                    f"Tab '{tab['title']}' is empty. Drag widgets here or click '+ Row' / '+ Col'.",
                                    color=(140, 140, 140),
                                )
                            else:
                                _render_rows_block(tab["rows"])

                active_tid = win.get("active_tab_id")
                if not active_tid or not get_tab(win["id"], active_tid):
                    active_tid = win["tabs"][0]["id"]
                    win["active_tab_id"] = active_tid
                active_c_tag = f"canvas_tab_{active_tid}"
                if dpg.does_item_exist(active_c_tag):
                    dpg.set_value(tb_tag, active_c_tag)


# ==========================================
# 5. PLACED ELEMENTS LIST (OUTLINER)
# ==========================================
def _render_outliner_rows(win, rows, row_prefix, w_prefix, tab_id=None):
    for r_idx, row in enumerate(rows):
        row_label = f"Row {r_idx + 1} ({len(row['widgets'])} items)"
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="- Row",
                small=True,
                user_data=(win["id"], row["id"], tab_id),
                callback=lambda s, a, u: delete_row(u[0], u[1], tab_id=u[2]),
            )
            with dpg.tree_node(
                label=row_label,
                tag=f"{row_prefix}{row['id']}",
                default_open=True,
            ):
                if not row["widgets"]:
                    dpg.add_text("(empty row - drop widget here)", color=(130, 130, 130))
                for w in row["widgets"]:
                    is_w_sel = (
                        state["selected_target"]["type"] == "widget"
                        and state["selected_target"]["widget_id"] == w["id"]
                    )
                    marker = ">> " if is_w_sel else "   "
                    lock_tag = " [LOCKED]" if w.get("locked") else ""
                    hide_tag = " [HIDDEN]" if not w.get("show", True) else ""
                    u_data = (win["id"], row["id"], w["id"], tab_id)
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="- Col",
                            small=True,
                            user_data=u_data,
                            callback=lambda s, a, u: (
                                select_widget(u[0], u[1], u[2], tab_id=u[3]),
                                delete_selected_widget(),
                            ),
                        )
                        dpg.add_selectable(
                            label=f"{marker}[{w['type']}] {w['label']}{lock_tag}{hide_tag}",
                            tag=f"{w_prefix}{w['id']}",
                            default_value=is_w_sel,
                            user_data=u_data,
                            callback=lambda s, a, u: select_widget(u[0], u[1], u[2], tab_id=u[3]),
                        )


def _populate_outliner_tree(parent_container_tag, row_prefix, w_prefix, tab_prefix):
    if not dpg.does_item_exist(parent_container_tag):
        return
    dpg.delete_item(parent_container_tag, children_only=True)

    for win in state["windows"]:
        is_win_sel = (
            state["selected_target"]["type"] == "window"
            and state["selected_target"]["window_id"] == win["id"]
        )
        win_label = f"{'[ACTIVE] ' if is_win_sel else ''}{win['title']} ({win['id']})"

        with dpg.tree_node(label=win_label, parent=parent_container_tag, default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Select Window",
                    small=True,
                    user_data=win["id"],
                    callback=lambda s, a, u: select_window(u)
                )
                dpg.add_button(
                    label="+ Tab",
                    small=True,
                    user_data=win["id"],
                    callback=lambda s, a, u: add_tab_to_window(u)
                )
                dpg.add_button(
                    label="+ Root Row",
                    small=True,
                    user_data=win["id"],
                    callback=lambda s, a, u: (add_new_row_to_container(u, tab_id=None), refresh_ui())
                )

            if not win.get("tabs") or any(r["widgets"] for r in win["rows"]):
                _render_outliner_rows(win, win["rows"], row_prefix, w_prefix, tab_id=None)

            for t_idx, tab in enumerate(win.get("tabs", [])):
                is_tab_sel = (
                    state["selected_target"]["tab_id"] == tab["id"]
                    and state["selected_target"]["window_id"] == win["id"]
                )
                tab_marker = "[ACTIVE TAB] " if is_tab_sel else ""
                tab_label = f"{tab_marker}Tab {t_idx + 1}: {tab['title']}"
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Edit Tab",
                        small=True,
                        user_data=(win["id"], tab["id"]),
                        callback=lambda s, a, u: select_tab(u[0], u[1]),
                    )
                    dpg.add_button(
                        label="+ Row",
                        small=True,
                        user_data=(win["id"], tab["id"]),
                        callback=lambda s, a, u: (add_new_row_to_container(u[0], tab_id=u[1]), select_tab(u[0], u[1])),
                    )
                    dpg.add_button(
                        label="- Tab",
                        small=True,
                        user_data=(win["id"], tab["id"]),
                        callback=lambda s, a, u: delete_tab(u[0], u[1]),
                    )
                with dpg.tree_node(
                    label=tab_label,
                    tag=f"{tab_prefix}{tab['id']}",
                    default_open=True,
                ):
                    _render_outliner_rows(win, tab["rows"], row_prefix, w_prefix, tab_id=tab["id"])


def update_outliner():
    _populate_outliner_tree("outliner_container", "outliner_row_", "outliner_w_", "outliner_tab_")
    _populate_outliner_tree("mini_outliner_container", "mini_outliner_row_", "mini_outliner_w_", "mini_outliner_tab_")


# ==========================================
# 6. INSPECTOR TAB & APP BACKGROUND APPEARANCE
# ==========================================
def update_inspector():
    target = state["selected_target"]
    target_type = target["type"]

    dpg.hide_item("inspector_empty_label")
    dpg.hide_item("inspector_window_group")
    dpg.hide_item("inspector_tab_group")
    dpg.hide_item("inspector_widget_group")

    if target_type == "window":
        win = get_window(target["window_id"])
        if not win:
            dpg.show_item("inspector_empty_label")
            return

        dpg.show_item("inspector_window_group")
        dpg.set_value("insp_win_info", f"Window: {win['title']} ({win['id']})")
        dpg.set_value("insp_win_title", win["title"])
        dpg.set_value("insp_win_width", win["width"])
        dpg.set_value("insp_win_height", win["height"])

    elif target_type == "tab":
        win = get_window(target["window_id"])
        tab = get_tab(target["window_id"], target["tab_id"])
        if not win or not tab:
            dpg.show_item("inspector_empty_label")
            return

        dpg.show_item("inspector_tab_group")
        dpg.set_value("insp_tab_info", f"Tab: '{tab['title']}' in {win['title']}")
        dpg.set_value("insp_tab_title", tab["title"])

    elif target_type == "widget":
        win, tab, row, r_idx, w_idx, widget = find_widget(target["widget_id"])
        if not widget:
            dpg.show_item("inspector_empty_label")
            return

        dpg.show_item("inspector_widget_group")
        w_type = widget["type"]
        spec = WIDGET_SPECS.get(w_type, WIDGET_SPECS["Button"])
        loc_str = f"Tab '{tab['title']}', " if tab else ""
        dpg.set_value("insp_wgt_id", f"Selected: {w_type} ({loc_str}Row {r_idx + 1}, Col {w_idx + 1})")
        dpg.set_value("insp_wgt_tag_input", widget["id"])

        dpg.configure_item("insp_wgt_label_group", show=spec["has_label"])
        if spec["has_label"]:
            dpg.set_value("insp_wgt_label", widget.get("label", ""))

        dpg.configure_item("insp_wgt_width_group", show=spec["has_width"])
        if spec["has_width"]:
            dpg.set_value("insp_wgt_width", safe_int(widget.get("width", 0), 0, 0, 10000))

        dpg.configure_item("insp_wgt_height_group", show=spec["has_height"])
        if spec["has_height"]:
            dpg.set_value("insp_wgt_height", safe_int(widget.get("height", 0), 0, 0, 10000))

        dpg.configure_item("insp_wgt_defval_group", show=spec["has_defval"])
        if spec["has_defval"]:
            dpg.set_value("insp_wgt_defval", str(widget.get("default_value", "")))

        dpg.configure_item("insp_wgt_minmax_group", show=spec["has_minmax"])
        if spec["has_minmax"]:
            dpg.set_value("insp_wgt_min", safe_float(widget.get("min_value", 0.0)))
            dpg.set_value("insp_wgt_max", safe_float(widget.get("max_value", 100.0)))

        dpg.configure_item("insp_wgt_items_group", show=spec["has_items"])
        if spec["has_items"]:
            dpg.set_value("insp_wgt_items", ", ".join(widget.get("items", [])))

        dpg.configure_item("insp_wgt_wrap_group", show=spec["has_wrap"])
        if spec["has_wrap"]:
            dpg.set_value("insp_wgt_wrap", safe_int(widget.get("wrap", 0), 0, 0, 10000))

        dpg.set_value("insp_wgt_enabled", bool(widget.get("enabled", True)))
        dpg.set_value("insp_wgt_show", bool(widget.get("show", True)))
        dpg.set_value("insp_wgt_locked", bool(widget.get("locked", False)))
    else:
        dpg.show_item("inspector_empty_label")


def on_widget_property_change(sender, value, prop_name):
    target = state["selected_target"]
    if target["type"] != "widget":
        return
    _, _, _, _, _, widget = find_widget(target["widget_id"])
    if not widget:
        return

    if prop_name == "items":
        widget["items"] = [item.strip() for item in value.split(",") if item.strip()]
    elif prop_name == "id":
        new_id = sanitize_id(value, fallback_prefix="el")
        if new_id and not is_widget_id_taken(new_id, exclude_widget=widget):
            widget["id"] = new_id
            state["selected_target"]["widget_id"] = new_id
    elif prop_name in ("width", "height", "wrap"):
        widget[prop_name] = safe_int(value, 0, 0, 10000)
    elif prop_name in ("min_value", "max_value"):
        widget[prop_name] = safe_float(value, 0.0)
    else:
        widget[prop_name] = value

    refresh_ui(inspector=True)


def on_tab_property_change(sender, value, prop_name):
    target = state["selected_target"]
    if target["type"] != "tab":
        return
    tab = get_tab(target["window_id"], target["tab_id"])
    if not tab:
        return
    if prop_name == "title":
        tab["title"] = value
        c_tab_tag = f"canvas_tab_{tab['id']}"
        if dpg.does_item_exist(c_tab_tag):
            dpg.set_item_label(c_tab_tag, value)
        update_outliner()


def on_window_property_change(sender, value, prop_name):
    target = state["selected_target"]
    if target["type"] != "window":
        return
    win = get_window(target["window_id"])
    if not win:
        return

    tag = f"canvas_{win['id']}"
    if prop_name == "title":
        win["title"] = value
        if dpg.does_item_exist(tag):
            dpg.set_item_label(tag, f"[ACTIVE] {value}")
    elif prop_name == "width":
        win["width"] = safe_int(value, 560, 100, 10000)
        if dpg.does_item_exist(tag):
            dpg.set_item_width(tag, win["width"])
    elif prop_name == "height":
        win["height"] = safe_int(value, 480, 80, 10000)
        if dpg.does_item_exist(tag):
            dpg.set_item_height(tag, win["height"])

    update_outliner()


def _to_int_rgba(val):
    if not val:
        return [20, 24, 32, 255]
    res = []
    is_normalized = all(isinstance(x, float) and 0.0 <= x <= 1.0 for x in val[:3]) and max(val[:3]) <= 1.0
    for x in val[:4]:
        c = int(round(x * 255)) if is_normalized else int(round(x))
        res.append(max(0, min(255, c)))
    while len(res) < 4:
        res.append(255)
    return res


def save_appearance_settings():
    """Saves current appearance settings to appearance_settings.json in the same folder as app.py."""
    data = {
        "preset": state["appearance"].get("preset", "Dark Slate (Default)"),
        "vp_color": state["appearance"].get("vp_color", [18, 22, 30, 255]),
        "win_color": state["appearance"].get("win_color", [28, 32, 42, 255]),
        "bg_image_path": state["bg_image"].get("path", ""),
        "bg_image_opacity": state["bg_image"].get("opacity", 1.0),
    }
    try:
        with open(APPEARANCE_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def load_appearance_settings():
    """Loads saved appearance settings from appearance_settings.json if it exists."""
    if not os.path.exists(APPEARANCE_CONFIG_PATH):
        return
    try:
        with open(APPEARANCE_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError, TypeError):
        return

    if not isinstance(data, dict):
        return

    preset = data.get("preset", "Dark Slate (Default)")
    vp_col = _to_int_rgba(data.get("vp_color", [18, 22, 30, 255]))
    win_col = _to_int_rgba(data.get("win_color", [28, 32, 42, 255]))
    img_path = str(data.get("bg_image_path", "") or "").strip()
    img_opacity = safe_float(data.get("bg_image_opacity", 1.0), 1.0)

    state["appearance"]["preset"] = preset
    state["appearance"]["vp_color"] = vp_col
    state["appearance"]["win_color"] = win_col
    state["bg_image"]["opacity"] = max(0.05, min(1.0, img_opacity))

    dpg.set_viewport_clear_color(vp_col)
    if dpg.does_item_exist("global_win_bg_color"):
        dpg.set_value("global_win_bg_color", win_col)
    if dpg.does_item_exist("combo_bg_preset") and preset in BG_PRESETS:
        dpg.set_value("combo_bg_preset", preset)
    if dpg.does_item_exist("picker_vp_bg"):
        dpg.set_value("picker_vp_bg", vp_col)
    if dpg.does_item_exist("picker_win_bg"):
        dpg.set_value("picker_win_bg", win_col)
    if dpg.does_item_exist("slider_bg_opacity"):
        dpg.set_value("slider_bg_opacity", state["bg_image"]["opacity"])

    if img_path and os.path.isfile(img_path):
        apply_background_image(img_path, save_config=False)


def on_viewport_bg_change(sender, app_data):
    rgba = _to_int_rgba(app_data)
    state["appearance"]["vp_color"] = rgba
    dpg.set_viewport_clear_color(rgba)
    save_appearance_settings()


def on_win_bg_change(sender, app_data):
    rgba = _to_int_rgba(app_data)
    state["appearance"]["win_color"] = rgba
    if dpg.does_item_exist("global_win_bg_color"):
        dpg.set_value("global_win_bg_color", rgba)
    save_appearance_settings()


def on_bg_preset_change(sender, preset_name):
    preset = BG_PRESETS.get(preset_name)
    if not preset:
        return
    vp_col = list(preset["vp"])
    win_col = list(preset["win"])
    state["appearance"]["preset"] = preset_name
    state["appearance"]["vp_color"] = vp_col
    state["appearance"]["win_color"] = win_col
    dpg.set_viewport_clear_color(vp_col)
    if dpg.does_item_exist("global_win_bg_color"):
        dpg.set_value("global_win_bg_color", win_col)
    if dpg.does_item_exist("picker_vp_bg"):
        dpg.set_value("picker_vp_bg", vp_col)
    if dpg.does_item_exist("picker_win_bg"):
        dpg.set_value("picker_win_bg", win_col)
    save_appearance_settings()


def set_bg_img_status(msg, is_error=False):
    if dpg.does_item_exist("bg_img_status"):
        dpg.set_value("bg_img_status", msg)
        dpg.configure_item("bg_img_status", color=(255, 100, 100) if is_error else (100, 230, 120))


def redraw_viewport_background_image():
    if not dpg.does_item_exist("vp_bg_drawlist"):
        return
    dpg.delete_item("vp_bg_drawlist", children_only=True)
    tex_tag = state["bg_image"]["texture_tag"]
    if not tex_tag or not dpg.does_item_exist(tex_tag):
        return
    vw = dpg.get_viewport_client_width() or dpg.get_viewport_width() or 1440
    vh = dpg.get_viewport_client_height() or dpg.get_viewport_height() or 840
    alpha = int(round(max(0.0, min(1.0, state["bg_image"]["opacity"])) * 255))
    dpg.draw_image(
        tex_tag,
        pmin=(0, 0),
        pmax=(vw, vh),
        uv_min=(0, 0),
        uv_max=(1, 1),
        color=(255, 255, 255, alpha),
        parent="vp_bg_drawlist",
    )


def apply_background_image(filepath=None, save_config=True):
    if filepath is None and dpg.does_item_exist("bg_img_path_input"):
        filepath = dpg.get_value("bg_img_path_input").strip().strip('"')
    if not filepath:
        set_bg_img_status("Enter an image path or click Browse.", is_error=True)
        return
    if not os.path.exists(filepath):
        set_bg_img_status(f"File not found: {filepath}", is_error=True)
        return

    try:
        loaded = dpg.load_image(filepath)
        if not loaded:
            set_bg_img_status("Failed to decode image (use PNG, JPG, BMP, HDR).", is_error=True)
            return
        width, height, _, data = loaded
    except Exception as e:
        set_bg_img_status(f"Image load error: {e}", is_error=True)
        return

    old_tex = state["bg_image"]["texture_tag"]
    if old_tex and dpg.does_item_exist(old_tex):
        dpg.delete_item(old_tex)

    new_tex = f"bg_tex_{uuid.uuid4().hex[:6]}"
    with dpg.texture_registry():
        dpg.add_static_texture(width=width, height=height, default_value=data, tag=new_tex)

    state["bg_image"]["texture_tag"] = new_tex
    state["bg_image"]["path"] = filepath
    if dpg.does_item_exist("bg_img_path_input"):
        dpg.set_value("bg_img_path_input", filepath)

    redraw_viewport_background_image()
    set_bg_img_status(f"Loaded background ({width}x{height}): {os.path.basename(filepath)}")
    if save_config:
        save_appearance_settings()


def clear_background_image():
    old_tex = state["bg_image"]["texture_tag"]
    if old_tex and dpg.does_item_exist(old_tex):
        dpg.delete_item(old_tex)
    state["bg_image"]["texture_tag"] = None
    state["bg_image"]["path"] = ""
    if dpg.does_item_exist("bg_img_path_input"):
        dpg.set_value("bg_img_path_input", "")
    if dpg.does_item_exist("vp_bg_drawlist"):
        dpg.delete_item("vp_bg_drawlist", children_only=True)
    set_bg_img_status("Background image cleared.")
    save_appearance_settings()


def on_bg_image_opacity_change(sender, value):
    state["bg_image"]["opacity"] = float(value)
    redraw_viewport_background_image()
    save_appearance_settings()


def on_bg_file_dialog_select(sender, app_data):
    if not app_data:
        return
    selected_path = app_data.get("file_path_name")
    if selected_path and os.path.isfile(selected_path):
        apply_background_image(selected_path)
    elif app_data.get("selections"):
        first_path = next(iter(app_data["selections"].values()), None)
        if first_path:
            apply_background_image(first_path)


# ==========================================
# 7. PYTHON CODE EXPORT & AST IMPORT
# ==========================================
def _format_widget_code(w):
    t = w["type"]
    spec = WIDGET_SPECS.get(t, WIDGET_SPECS["Button"])
    func_name = spec["dpg_func"]
    kw = _build_widget_dpg_kwargs(w)
    if t == "Spacer" and "height" not in kw:
        kw["height"] = 15

    args = []
    if t == "Text" and "default_value" in kw:
        args.append(repr(kw.pop("default_value")))

    for k, v in kw.items():
        args.append(f"{k}={repr(v)}")

    # Export custom user-defined tag if modified from auto-generated 'el_xxxxxx'
    wid = str(w.get("id", ""))
    if wid and not wid.startswith("el_"):
        args.append(f"tag={repr(wid)}")

    if not w.get("enabled", True) and spec["supports_enabled"]:
        args.append("enabled=False")
    if not w.get("show", True):
        args.append("show=False")

    return f"dpg.{func_name}({', '.join(args)})"


def _append_rows_code(code, rows, indent="    "):
    non_empty = [r for r in rows if r["widgets"]]
    for r in non_empty:
        if len(r["widgets"]) == 1:
            code.append(f"{indent}{_format_widget_code(r['widgets'][0])}")
        else:
            code.append(f"{indent}with dpg.group(horizontal=True):")
            for w in r["widgets"]:
                code.append(f"{indent}    {_format_widget_code(w)}")


def generate_code_string():
    sync_window_rects_from_dpg()
    code = [
        "# Generated by DearPyGui Constructor (Copyright (c) 2026 JustEnotik)",
        "# LICENSE NOTICE: Free use requires this project to be Open-Source AND under $1,000/mo commercial revenue.",
        "# Closed-source/proprietary use or >= $1,000/mo revenue requires a paid Commercial License: justenotik@proton.me",
        "",
        "import dearpygui.dearpygui as dpg",
        "",
        "dpg.create_context()",
        "dpg.create_viewport(title='Generated Application', width=1100, height=700)",
        ""
    ]

    for win in state["windows"]:
        title_repr = repr(win["title"])
        code.append(
            f"with dpg.window(label={title_repr}, pos={win['pos']}, width={win['width']}, height={win['height']}):"
        )
        non_empty_root = [r for r in win["rows"] if r["widgets"]]
        tabs = win.get("tabs", [])

        if not non_empty_root and not tabs:
            code.append("    pass")
        else:
            _append_rows_code(code, non_empty_root, indent="    ")
            if tabs:
                code.append("    with dpg.tab_bar():")
                for tab in tabs:
                    t_lbl = repr(tab["title"])
                    code.append(f"        with dpg.tab(label={t_lbl}):")
                    non_empty_tab = [r for r in tab["rows"] if r["widgets"]]
                    if not non_empty_tab:
                        code.append("            pass")
                    else:
                        _append_rows_code(code, non_empty_tab, indent="            ")
        code.append("")

    code.extend([
        "dpg.setup_dearpygui()",
        "dpg.show_viewport()",
        "dpg.start_dearpygui()",
        "dpg.destroy_context()"
    ])
    return "\n".join(code)


def set_io_status(msg, is_error=False):
    if dpg.does_item_exist("io_status_text"):
        dpg.set_value("io_status_text", msg)
        dpg.configure_item("io_status_text", color=(255, 100, 100) if is_error else (100, 230, 120))


def generate_code():
    code_str = generate_code_string()
    dpg.set_value("code_export_field", code_str)
    set_io_status("Generated Python code from current layout.")


def save_code_to_file():
    code_str = generate_code_string()
    dpg.set_value("code_export_field", code_str)
    filepath = dpg.get_value("io_file_path").strip() or "exported_ui.py"
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code_str)
        set_io_status(f"Saved Python code to '{filepath}'.")
    except OSError as e:
        set_io_status(f"Save error: {e}", is_error=True)


def load_code_from_file():
    filepath = dpg.get_value("io_file_path").strip() or "exported_ui.py"
    if not os.path.exists(filepath):
        set_io_status(f"File not found: '{filepath}'", is_error=True)
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code_str = f.read()
        dpg.set_value("code_export_field", code_str)
        import_code_from_editor()
        set_io_status(f"Loaded and imported '{filepath}'.")
    except OSError as e:
        set_io_status(f"Load error: {e}", is_error=True)


def _ast_literal(node, default=None):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return default


def _get_call_name(call_node):
    if isinstance(call_node.func, ast.Attribute):
        return call_node.func.attr
    if isinstance(call_node.func, ast.Name):
        return call_node.func.id
    return ""


def _get_call_kwargs(call_node):
    kwargs = {}
    for kw in call_node.keywords:
        if kw.arg:
            kwargs[kw.arg] = _ast_literal(kw.value)
    return kwargs


def _parse_widget_call(call_node):
    func_name = _get_call_name(call_node)
    w_type = DPG_FUNC_TO_TYPE.get(func_name)
    if not w_type:
        return None

    w_data = create_widget_data(w_type)
    kwargs = _get_call_kwargs(call_node)
    pos_args = [_ast_literal(a) for a in call_node.args]

    if "tag" in kwargs and kwargs["tag"]:
        w_data["id"] = sanitize_id(kwargs["tag"], fallback_prefix="el")

    if w_type == "Text":
        label = pos_args[0] if pos_args else kwargs.get("default_value", w_data["label"])
        w_data["label"] = str(label) if label is not None else "Text"
        if "wrap" in kwargs and isinstance(kwargs["wrap"], (int, float)):
            w_data["wrap"] = int(kwargs["wrap"])
    elif w_type == "ProgressBar":
        if "overlay" in kwargs and kwargs["overlay"] is not None:
            w_data["label"] = str(kwargs["overlay"])
        if "default_value" in kwargs and kwargs["default_value"] is not None:
            w_data["default_value"] = kwargs["default_value"]
    else:
        if "label" in kwargs and kwargs["label"] is not None:
            w_data["label"] = str(kwargs["label"])
        elif pos_args and isinstance(pos_args[0], str) and w_type not in ("RadioButton", "Listbox", "Combo"):
            w_data["label"] = pos_args[0]

    if "width" in kwargs and isinstance(kwargs["width"], (int, float)):
        w_data["width"] = int(kwargs["width"])
    if "height" in kwargs and isinstance(kwargs["height"], (int, float)):
        w_data["height"] = int(kwargs["height"])
    if "min_value" in kwargs and isinstance(kwargs["min_value"], (int, float)):
        w_data["min_value"] = kwargs["min_value"]
    if "max_value" in kwargs and isinstance(kwargs["max_value"], (int, float)):
        w_data["max_value"] = kwargs["max_value"]

    if "default_value" in kwargs and kwargs["default_value"] is not None and w_type != "Text":
        dv = kwargs["default_value"]
        if w_type in ("ColorEdit", "ColorPicker") and isinstance(dv, (list, tuple)):
            w_data["default_value"] = ", ".join(str(int(x)) for x in dv[:4])
        else:
            w_data["default_value"] = dv

    if "items" in kwargs and isinstance(kwargs["items"], (list, tuple)):
        w_data["items"] = [str(x) for x in kwargs["items"]]
    elif pos_args and isinstance(pos_args[0], (list, tuple)) and w_type in ("Combo", "RadioButton", "Listbox"):
        w_data["items"] = [str(x) for x in pos_args[0]]

    if "enabled" in kwargs and isinstance(kwargs["enabled"], bool):
        w_data["enabled"] = kwargs["enabled"]
    if "show" in kwargs and isinstance(kwargs["show"], bool):
        w_data["show"] = kwargs["show"]

    return w_data


def _parse_rows_from_stmts(body_stmts):
    rows = []
    for stmt in body_stmts:
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            w_data = _parse_widget_call(stmt.value)
            if w_data:
                rows.append({"id": new_uid("row"), "widgets": [w_data]})
        elif isinstance(stmt, ast.With):
            for item in stmt.items:
                if isinstance(item.context_expr, ast.Call):
                    cname = _get_call_name(item.context_expr)
                    if cname == "group":
                        kw = _get_call_kwargs(item.context_expr)
                        is_horiz = kw.get("horizontal", False)
                        row_widgets = []
                        for sub in stmt.body:
                            if isinstance(sub, ast.Expr) and isinstance(sub.value, ast.Call):
                                w_data = _parse_widget_call(sub.value)
                                if w_data:
                                    if is_horiz:
                                        row_widgets.append(w_data)
                                    else:
                                        rows.append({"id": new_uid("row"), "widgets": [w_data]})
                        if row_widgets:
                            rows.append({"id": new_uid("row"), "widgets": row_widgets})
    if not rows:
        rows.append({"id": new_uid("row"), "widgets": []})
    return rows


def _parse_window_body(body_stmts):
    root_stmts = []
    tabs = []
    for stmt in body_stmts:
        if isinstance(stmt, ast.With):
            is_tab_bar = False
            for item in stmt.items:
                if isinstance(item.context_expr, ast.Call) and _get_call_name(item.context_expr) == "tab_bar":
                    is_tab_bar = True
                    for sub in stmt.body:
                        if isinstance(sub, ast.With):
                            for sub_item in sub.items:
                                if isinstance(sub_item.context_expr, ast.Call) and _get_call_name(sub_item.context_expr) == "tab":
                                    tkw = _get_call_kwargs(sub_item.context_expr)
                                    t_idx = len(tabs) + 1
                                    tabs.append({
                                        "id": new_uid("tab"),
                                        "title": str(tkw.get("label", f"Tab {t_idx}")),
                                        "rows": _parse_rows_from_stmts(sub.body),
                                    })
            if not is_tab_bar:
                root_stmts.append(stmt)
        else:
            root_stmts.append(stmt)

    rows = _parse_rows_from_stmts(root_stmts)
    return rows, tabs


def import_code_from_editor():
    code_str = dpg.get_value("code_export_field")
    if not code_str or not code_str.strip():
        set_io_status("Code editor is empty.", is_error=True)
        return

    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        set_io_status(f"Python syntax error on line {e.lineno}: {e.msg}", is_error=True)
        return

    parsed_windows = []
    top_level_widgets = []

    for node in tree.body:
        if isinstance(node, ast.With):
            for item in node.items:
                if isinstance(item.context_expr, ast.Call) and _get_call_name(item.context_expr) == "window":
                    kw = _get_call_kwargs(item.context_expr)
                    idx = len(parsed_windows) + 1
                    pos = kw.get("pos", [455 + (idx - 1) * 30, 20 + (idx - 1) * 30])
                    if not isinstance(pos, (list, tuple)) or len(pos) != 2:
                        pos = [455, 20]
                    rows, tabs = _parse_window_body(node.body)
                    win_data = {
                        "id": new_uid("win"),
                        "title": str(kw.get("label", f"Window {idx}")),
                        "pos": [int(pos[0]), int(pos[1])],
                        "width": int(kw.get("width", 560)),
                        "height": int(kw.get("height", 450)),
                        "rows": rows,
                        "tabs": tabs,
                        "active_tab_id": tabs[0]["id"] if tabs else None,
                    }
                    parsed_windows.append(win_data)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            w_data = _parse_widget_call(node.value)
            if w_data:
                top_level_widgets.append(w_data)

    if not parsed_windows and top_level_widgets:
        parsed_windows.append({
            "id": new_uid("win"),
            "title": "Imported Window",
            "pos": [455, 20],
            "width": 560,
            "height": 450,
            "rows": [{"id": new_uid("row"), "widgets": [w]} for w in top_level_widgets],
            "tabs": [],
            "active_tab_id": None,
        })

    if not parsed_windows:
        set_io_status("No dpg.window(...) or dpg.add_* widgets found in code.", is_error=True)
        return

    for old_tag in list(_rendered_canvas_window_ids):
        if dpg.does_item_exist(old_tag):
            dpg.delete_item(old_tag)
    _rendered_canvas_window_ids.clear()

    state["windows"] = parsed_windows
    first_w = parsed_windows[0]
    if first_w["tabs"]:
        select_tab(first_w["id"], first_w["tabs"][0]["id"])
    else:
        select_window(first_w["id"])

    total_tabs = sum(len(w["tabs"]) for w in parsed_windows)
    total_w = sum(
        len(r["widgets"])
        for w in parsed_windows
        for r in (w["rows"] + [tr for t in w["tabs"] for tr in t["rows"]])
    )
    set_io_status(f"Imported {len(parsed_windows)} window(s), {total_tabs} tab(s), and {total_w} widget(s)!")


# ==========================================
# 8. INITIALIZATION & UI LAYOUT
# ==========================================
def build_palette():
    for w_type, spec in WIDGET_SPECS.items():
        with dpg.group(horizontal=True):
            with dpg.group(tag=f"palette_box_{w_type}"):
                getattr(dpg, spec["palette_func"])(tag=f"palette_src_{w_type}", **spec["palette_kw"])

            dpg.add_button(
                label="+ Row",
                width=88,
                user_data=w_type,
                callback=lambda s, a, u: add_widget_from_palette(u, new_row=True),
            )
            dpg.add_button(
                label="+ Col",
                width=88,
                user_data=w_type,
                callback=lambda s, a, u: add_widget_from_palette(u, new_row=False),
            )


def main():
    dpg.create_context()
    dpg.create_viewport(title="DearPyGui Constructor", width=1440, height=840)

    default_preset = BG_PRESETS["Dark Slate (Default)"]
    dpg.set_viewport_clear_color(default_preset["vp"])

    # Back-layer viewport drawlist for optional user background image
    dpg.add_viewport_drawlist(front=False, tag="vp_bg_drawlist")
    dpg.set_viewport_resize_callback(lambda s, a: redraw_viewport_background_image())

    # File dialog for selecting a background image
    with dpg.file_dialog(
        directory_selector=False,
        show=False,
        callback=on_bg_file_dialog_select,
        tag="bg_file_dialog",
        width=680,
        height=440,
    ):
        dpg.add_file_extension(".*")
        dpg.add_file_extension(".png", color=(100, 255, 100, 255))
        dpg.add_file_extension(".jpg", color=(100, 200, 255, 255))
        dpg.add_file_extension(".jpeg", color=(100, 200, 255, 255))
        dpg.add_file_extension(".bmp", color=(255, 200, 100, 255))

    # Global application theme
    with dpg.theme(tag="app_global_theme"):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, default_preset["win"], tag="global_win_bg_color")
    dpg.bind_theme("app_global_theme")

    # Golden selection highlight theme
    with dpg.theme(tag="selected_widget_theme"):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_Border, [255, 215, 0, 255])
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 2.0)

    # Floating Drag Ghost theme
    with dpg.theme(tag="drag_ghost_theme"):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, [25, 35, 50, 235])
            dpg.add_theme_color(dpg.mvThemeCol_Border, [80, 190, 255, 255])
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 2.0)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6.0)

    # Floating Drag Ghost Window (always brought to front during drag)
    with dpg.window(
        tag="drag_ghost_win",
        show=False,
        no_title_bar=True,
        no_move=True,
        no_resize=True,
        no_scrollbar=True,
        autosize=True,
    ):
        dpg.add_text("", tag="drag_ghost_status", color=(100, 255, 130))
        dpg.add_group(tag="drag_ghost_preview_box")
    dpg.bind_item_theme("drag_ghost_win", "drag_ghost_theme")

    # Right-Click (RMB) Context Menu Window for Placed Elements
    with dpg.window(
        label="Element Parameters (RMB)",
        tag="rmb_context_win",
        show=False,
        no_collapse=True,
        no_saved_settings=True,
        autosize=True,
        on_close=lambda: dpg.hide_item("rmb_context_win"),
    ):
        dpg.add_text("", tag="ctx_wgt_header", color=(100, 230, 120))
        dpg.add_separator()

        dpg.add_text("1. Name / Tag & Text:", color=(100, 185, 255))
        dpg.add_input_text(label="Name (ID)", tag="ctx_wgt_id_input", width=165, user_data="id", callback=on_widget_property_change)
        with dpg.group(tag="ctx_label_group"):
            dpg.add_input_text(label="Label / Title", tag="ctx_wgt_label", width=165, user_data="label", callback=on_widget_property_change)
        with dpg.group(tag="ctx_defval_group"):
            dpg.add_input_text(label="Text / Value", tag="ctx_wgt_defval", width=165, user_data="default_value", callback=on_widget_property_change)
        with dpg.group(tag="ctx_items_group"):
            dpg.add_input_text(label="Items (a,b)", tag="ctx_wgt_items", width=165, user_data="items", callback=on_widget_property_change)

        dpg.add_separator()
        dpg.add_text("2. State:", color=(100, 185, 255))
        with dpg.group(horizontal=True):
            dpg.add_checkbox(label="Enabled", tag="ctx_wgt_enabled", default_value=True, user_data="enabled", callback=on_widget_property_change)
            dpg.add_checkbox(label="Visible", tag="ctx_wgt_show", default_value=True, user_data="show", callback=on_widget_property_change)

        dpg.add_separator()
        dpg.add_text("3. Movement:", color=(100, 185, 255))
        dpg.add_checkbox(label="Lock Drag (Pin Position)", tag="ctx_wgt_locked", default_value=False, user_data="locked", callback=on_widget_property_change)
        with dpg.group(horizontal=True):
            dpg.add_button(label="<< Left", width=62, callback=lambda: move_widget_fine("horizontal", -1))
            dpg.add_button(label="Right >>", width=62, callback=lambda: move_widget_fine("horizontal", 1))
            dpg.add_button(label="^^ Up", width=55, callback=lambda: move_widget_fine("vertical", -1))
            dpg.add_button(label="vv Down", width=62, callback=lambda: move_widget_fine("vertical", 1))

        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Duplicate",
                width=85,
                callback=lambda: (duplicate_selected_widget(), dpg.hide_item("rmb_context_win")),
            )
            dpg.add_button(
                label="Delete",
                width=85,
                callback=lambda: (delete_selected_widget(), dpg.hide_item("rmb_context_win")),
            )
            dpg.add_button(
                label="Close",
                width=75,
                callback=lambda: dpg.hide_item("rmb_context_win"),
            )
    dpg.bind_item_theme("rmb_context_win", "drag_ghost_theme")

    # Global Mouse Handlers for Custom Drag & Drop + RMB Context Menu
    with dpg.handler_registry():
        dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Left, callback=on_global_mouse_down)
        dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Right, callback=on_global_right_click)
        dpg.add_mouse_move_handler(callback=on_global_mouse_move)
        dpg.add_mouse_release_handler(button=dpg.mvMouseButton_Left, callback=on_global_mouse_release)

    # Toolbox Window with all 5 Tabs!
    with dpg.window(label="Toolbox", pos=(10, 15), width=435, height=795, no_close=True):
        with dpg.tab_bar(tag="main_tab_bar"):

            # --- TAB 1: ELEMENTS & PALETTE (+ Quick Outliner) ---
            with dpg.tab(label="Elements"):
                dpg.add_text("Window, Tab & Grid Controls:", color=(100, 185, 255))
                with dpg.group(horizontal=True):
                    dpg.add_button(label="+ Window", width=95, callback=add_user_window)
                    dpg.add_button(label="+ Tab", width=95, callback=lambda: add_tab_to_window())
                    dpg.add_button(label="- Tab", width=95, callback=delete_selected_tab)
                    dpg.add_button(label="Clone Wgt", width=95, callback=duplicate_selected_widget)
                with dpg.group(horizontal=True):
                    dpg.add_button(label="- Row (Sel)", width=194, callback=delete_selected_row)
                    dpg.add_button(label="- Col (Sel)", width=194, callback=delete_selected_widget)

                dpg.add_separator()
                dpg.add_text(f"1. Widget Palette ({len(WIDGET_TYPES)} Elements - Drag onto Canvas):", color=(100, 185, 255))
                with dpg.child_window(height=360, border=True):
                    build_palette()

                dpg.add_text("2. Placed Elements List (Quick Outliner):", color=(100, 185, 255))
                with dpg.child_window(tag="mini_outliner_container", height=-1, border=True):
                    pass

            # --- TAB 2: OUTLINER (FULL HIERARCHY TREE) ---
            with dpg.tab(label="Outliner"):
                dpg.add_text("Full Window, Tab & Widget Hierarchy:", color=(100, 185, 255))
                dpg.add_text("Click to select, RMB for popup, or drag to reorder:", color=(160, 160, 160))
                dpg.add_separator()
                with dpg.child_window(tag="outliner_container", width=-1, height=-1, border=False):
                    pass

            # --- TAB 3: INSPECTOR ---
            with dpg.tab(label="Inspector"):
                dpg.add_text("Select an element, tab, or window to inspect.", tag="inspector_empty_label", color=(150, 150, 150))

                # Widget Inspector
                with dpg.group(tag="inspector_widget_group", show=False):
                    dpg.add_text("", tag="insp_wgt_id", color=(100, 230, 120))
                    dpg.add_separator()

                    dpg.add_text("Name / Tag (ID):")
                    dpg.add_input_text(tag="insp_wgt_tag_input", width=-1, user_data="id", callback=on_widget_property_change)

                    with dpg.group(tag="insp_wgt_label_group"):
                        dpg.add_text("Label / Title:")
                        dpg.add_input_text(tag="insp_wgt_label", width=-1, user_data="label", callback=on_widget_property_change)

                    with dpg.group(tag="insp_wgt_defval_group"):
                        dpg.add_text("Default Value / Text:")
                        dpg.add_input_text(tag="insp_wgt_defval", width=-1, user_data="default_value", callback=on_widget_property_change)

                    with dpg.group(tag="insp_wgt_minmax_group", show=False):
                        dpg.add_text("Min / Max Range:")
                        with dpg.group(horizontal=True):
                            dpg.add_input_float(label="Min", tag="insp_wgt_min", width=155, user_data="min_value", callback=on_widget_property_change)
                            dpg.add_input_float(label="Max", tag="insp_wgt_max", width=155, user_data="max_value", callback=on_widget_property_change)

                    with dpg.group(tag="insp_wgt_items_group"):
                        dpg.add_text("Items (comma-separated):")
                        dpg.add_input_text(tag="insp_wgt_items", width=-1, user_data="items", callback=on_widget_property_change)

                    with dpg.group(tag="insp_wgt_width_group"):
                        dpg.add_text("Width (0 = auto):")
                        dpg.add_input_int(tag="insp_wgt_width", width=-1, min_value=0, user_data="width", callback=on_widget_property_change)

                    with dpg.group(tag="insp_wgt_height_group"):
                        dpg.add_text("Height (0 = auto):")
                        dpg.add_input_int(tag="insp_wgt_height", width=-1, min_value=0, user_data="height", callback=on_widget_property_change)

                    with dpg.group(tag="insp_wgt_wrap_group", show=False):
                        dpg.add_text("Wrap (pixels, 0 = no wrap):")
                        dpg.add_input_int(tag="insp_wgt_wrap", width=-1, min_value=0, user_data="wrap", callback=on_widget_property_change)

                    dpg.add_separator()
                    dpg.add_text("State & Movement Lock:", color=(100, 185, 255))
                    with dpg.group(horizontal=True):
                        dpg.add_checkbox(label="Enabled", tag="insp_wgt_enabled", default_value=True, user_data="enabled", callback=on_widget_property_change)
                        dpg.add_checkbox(label="Visible", tag="insp_wgt_show", default_value=True, user_data="show", callback=on_widget_property_change)
                        dpg.add_checkbox(label="Lock Drag", tag="insp_wgt_locked", default_value=False, user_data="locked", callback=on_widget_property_change)

                    dpg.add_separator()
                    dpg.add_text("Move in Grid:", color=(100, 185, 255))
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="<< Left", width=95, callback=lambda: move_widget_fine("horizontal", -1))
                        dpg.add_button(label="Right >>", width=95, callback=lambda: move_widget_fine("horizontal", 1))
                        dpg.add_button(label="^^ Up", width=95, callback=lambda: move_widget_fine("vertical", -1))
                        dpg.add_button(label="vv Down", width=95, callback=lambda: move_widget_fine("vertical", 1))

                    dpg.add_spacer(height=8)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Duplicate Widget", width=130, callback=duplicate_selected_widget)
                        dpg.add_button(label="- Col (Del Wgt)", width=130, callback=delete_selected_widget)
                        dpg.add_button(label="- Row (Del Row)", width=130, callback=delete_selected_row)

                # Tab Inspector
                with dpg.group(tag="inspector_tab_group", show=False):
                    dpg.add_text("", tag="insp_tab_info", color=(100, 210, 255))
                    dpg.add_separator()
                    dpg.add_text("Tab Title:")
                    dpg.add_input_text(tag="insp_tab_title", width=-1, user_data="title", callback=on_tab_property_change)

                    dpg.add_spacer(height=8)
                    dpg.add_text("Reorder / Manage Tab:", color=(100, 185, 255))
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="<< Move Tab Left", width=196, callback=lambda: move_tab_order(-1))
                        dpg.add_button(label="Move Tab Right >>", width=196, callback=lambda: move_tab_order(1))
                    dpg.add_spacer(height=6)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="+ Add Another Tab", width=196, callback=lambda: add_tab_to_window())
                        dpg.add_button(label="- Delete This Tab", width=196, callback=delete_selected_tab)

                # Window Inspector
                with dpg.group(tag="inspector_window_group", show=False):
                    dpg.add_text("", tag="insp_win_info", color=(100, 185, 255))
                    dpg.add_separator()
                    dpg.add_text("Window Title:")
                    dpg.add_input_text(tag="insp_win_title", width=-1, user_data="title", callback=on_window_property_change)

                    dpg.add_text("Width:")
                    dpg.add_input_int(tag="insp_win_width", width=-1, min_value=100, user_data="width", callback=on_window_property_change)

                    dpg.add_text("Height:")
                    dpg.add_input_int(tag="insp_win_height", width=-1, min_value=80, user_data="height", callback=on_window_property_change)

                    dpg.add_spacer(height=8)
                    dpg.add_button(label="+ Add Tab to Window", width=-1, callback=lambda: add_tab_to_window())
                    dpg.add_spacer(height=6)
                    dpg.add_button(label="Delete Window", width=-1, callback=lambda: delete_user_window())

            # --- TAB 4: EXPORT / IMPORT ---
            with dpg.tab(label="Export"):
                dpg.add_text("Export / Import Python Code (AST Parser):", color=(100, 185, 255))
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Export from Canvas", width=196, callback=generate_code)
                    dpg.add_button(label="Import to Canvas", width=196, callback=import_code_from_editor)

                dpg.add_spacer(height=4)
                with dpg.group(horizontal=True):
                    dpg.add_input_text(tag="io_file_path", default_value="exported_ui.py", width=210)
                    dpg.add_button(label="Save .py", width=90, callback=save_code_to_file)
                    dpg.add_button(label="Load .py", width=90, callback=load_code_from_file)

                dpg.add_text("", tag="io_status_text", color=(100, 230, 120))
                dpg.add_input_text(
                    tag="code_export_field",
                    multiline=True,
                    readonly=False,
                    width=-1,
                    height=600,
                    default_value="# Click 'Export from Canvas' or paste DearPyGui Python code here and click 'Import to Canvas'"
                )

            # --- TAB 5: APPEARANCE (APP-ONLY BACKGROUND) ---
            with dpg.tab(label="Appearance"):
                dpg.add_text("Constructor Background (App-Only):", color=(100, 185, 255))
                dpg.add_text("Changes background only in this constructor\n(saved automatically to appearance_settings.json).", color=(150, 150, 150))
                dpg.add_separator()

                dpg.add_text("1. Background Image (Optional):", color=(100, 185, 255))
                with dpg.group(horizontal=True):
                    dpg.add_input_text(tag="bg_img_path_input", hint="Path to .png / .jpg...", width=215)
                    dpg.add_button(label="Browse...", width=85, callback=lambda: dpg.show_item("bg_file_dialog"))
                    dpg.add_button(label="Apply", width=80, callback=lambda: apply_background_image())
                with dpg.group(horizontal=True):
                    dpg.add_slider_float(
                        label="Image Opacity",
                        tag="slider_bg_opacity",
                        default_value=1.0,
                        min_value=0.05,
                        max_value=1.0,
                        width=215,
                        callback=on_bg_image_opacity_change,
                    )
                    dpg.add_button(label="Clear Image", width=95, callback=clear_background_image)
                dpg.add_text("", tag="bg_img_status", color=(100, 230, 120))

                dpg.add_separator()
                dpg.add_text("2. Quick Color Presets:", color=(100, 185, 255))
                dpg.add_combo(
                    items=list(BG_PRESETS.keys()),
                    tag="combo_bg_preset",
                    default_value="Dark Slate (Default)",
                    width=-1,
                    callback=on_bg_preset_change,
                )
                dpg.add_spacer(height=6)

                dpg.add_text("3. Workspace / Viewport Solid Color:")
                dpg.add_color_edit(
                    tag="picker_vp_bg",
                    default_value=default_preset["vp"],
                    no_alpha=True,
                    width=-1,
                    callback=on_viewport_bg_change,
                )
                dpg.add_spacer(height=6)

                dpg.add_text("4. Windows Background Color:")
                dpg.add_color_edit(
                    tag="picker_win_bg",
                    default_value=default_preset["win"],
                    no_alpha=False,
                    width=-1,
                    callback=on_win_bg_change,
                )

    load_appearance_settings()
    refresh_ui()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
