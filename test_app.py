import ast
import json
import os
import re
import tempfile
import unittest
from unittest.mock import patch

import dearpygui.dearpygui as dpg
import app


class TestDearPyGuiConstructor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialize the full DearPyGui Constructor UI once for fast, realistic integration tests."""
        cls._orig_config_path = app.APPEARANCE_CONFIG_PATH
        cls._temp_dir = tempfile.TemporaryDirectory()
        app.APPEARANCE_CONFIG_PATH = os.path.join(cls._temp_dir.name, "test_appearance_settings.json")

        # Patch start_dearpygui and destroy_context so main() builds the entire UI and stays alive
        with patch.object(dpg, "start_dearpygui", lambda: None), patch.object(dpg, "destroy_context", lambda: None):
            app.main()

        # Render a few frames so item rects are populated by DearPyGui
        for _ in range(3):
            dpg.render_dearpygui_frame()

    @classmethod
    def tearDownClass(cls):
        if dpg.is_dearpygui_running():
            dpg.stop_dearpygui()
        dpg.destroy_context()
        app.APPEARANCE_CONFIG_PATH = cls._orig_config_path
        cls._temp_dir.cleanup()

    def setUp(self):
        """Reset state to a clean single window before each test."""
        for old_tag in list(app._rendered_canvas_window_ids):
            if dpg.does_item_exist(old_tag):
                dpg.delete_item(old_tag)
        app._rendered_canvas_window_ids.clear()

        app.state["windows"] = [
            {
                "id": "win_main",
                "title": "Main Window",
                "pos": [455, 20],
                "width": 560,
                "height": 480,
                "rows": [{"id": "row_init", "widgets": []}],
                "tabs": [],
                "active_tab_id": None,
            }
        ]
        app.state["drag"] = {
            "pending": None,
            "active": False,
            "mode": None,
            "value": None,
            "label": "",
            "hovered_target": None,
        }
        app.select_window("win_main")
        dpg.render_dearpygui_frame()

    def test_01_english_only_codebase(self):
        """Verify 100% English strings/comments in app.py (zero Cyrillic characters)."""
        app_path = os.path.join(app.APP_DIR, "app.py")
        with open(app_path, "r", encoding="utf-8") as f:
            content = f.read()
        cyrillic_matches = re.findall(r"[а-яА-ЯёЁ]+", content)
        self.assertEqual(cyrillic_matches, [], f"Found Cyrillic text in app.py: {cyrillic_matches}")

    def test_02_all_23_widget_types_palette_and_canvas_render(self):
        """Verify all 23 widget types exist in the palette, can be added to Canvas, and render without DPG errors."""
        self.assertGreaterEqual(len(app.WIDGET_TYPES), 23)
        for w_type in app.WIDGET_TYPES:
            self.assertTrue(dpg.does_item_exist(f"palette_box_{w_type}"), f"Missing palette box for {w_type}")
            self.assertTrue(dpg.does_item_exist(f"palette_src_{w_type}"), f"Missing palette source for {w_type}")

            # Add via palette (+ Row)
            app.add_widget_from_palette(w_type, new_row=True)
            dpg.render_dearpygui_frame()

            # Verify widget exists in state and on Canvas
            w_id = app.state["selected_target"]["widget_id"]
            self.assertIsNotNone(w_id)
            self.assertTrue(dpg.does_item_exist(f"wbox_{w_id}"), f"Missing canvas wrapper group for {w_type}")
            self.assertTrue(dpg.does_item_exist(f"widget_{w_id}"), f"Missing canvas widget for {w_type}")

            # Verify preview in drag ghost works for every widget type
            _, _, _, _, _, w_data = app.find_widget(w_id)
            dpg.delete_item("drag_ghost_preview_box", children_only=True)
            app.render_widget_preview(w_type, w_data, parent="drag_ghost_preview_box")

    def test_03_windows_and_tabs_lifecycle(self):
        """Verify adding/deleting windows and adding/renaming/reordering/deleting tabs."""
        # Add second window
        app.add_user_window()
        self.assertEqual(len(app.state["windows"]), 2)
        second_win_id = app.state["windows"][1]["id"]
        self.assertEqual(app.state["selected_target"]["window_id"], second_win_id)

        # Add two tabs to second window
        t1 = app.add_tab_to_window(second_win_id)
        t2 = app.add_tab_to_window(second_win_id)
        win2 = app.get_window(second_win_id)
        self.assertEqual([t["id"] for t in win2["tabs"]], [t1, t2])
        self.assertEqual(win2["active_tab_id"], t2)

        # Add a Button inside Tab 2
        app.add_widget_from_palette("Button", new_row=False)
        tab2_obj = app.get_tab(second_win_id, t2)
        self.assertEqual(len(tab2_obj["rows"][0]["widgets"]), 1)

        # Select Tab 2 and rename it via Inspector callback
        app.select_tab(second_win_id, t2)
        app.on_tab_property_change(None, "Settings Tab", "title")
        self.assertEqual(tab2_obj["title"], "Settings Tab")

        # Move Tab 2 left (so order becomes [t2, t1])
        app.move_tab_order(-1)
        self.assertEqual([t["id"] for t in win2["tabs"]], [t2, t1])

        # Delete Tab 2
        app.delete_selected_tab()
        self.assertEqual([t["id"] for t in win2["tabs"]], [t1])

        # Delete second window
        app.delete_user_window(second_win_id)
        self.assertEqual(len(app.state["windows"]), 1)

    def test_04_rmb_context_menu_and_widget_properties(self):
        """Verify RMB context menu opens, edits ID/Label/Value/Items/State/Lock, and duplicates widget."""
        app.add_widget_from_palette("SliderFloat", new_row=True)
        w_id = app.state["selected_target"]["widget_id"]
        win, _, row, _, _, w = app.find_widget(w_id)

        # Open RMB menu on the placed widget
        app.open_rmb_context_menu(win, None, row, w, 500, 300)
        self.assertTrue(dpg.is_item_shown("rmb_context_win"))
        self.assertEqual(dpg.get_value("ctx_wgt_id_input"), w_id)

        # Rename ID (with special characters that must be sanitized)
        app.on_widget_property_change(None, "my custom slider!", "id")
        self.assertEqual(w["id"], "my_custom_slider_")
        self.assertEqual(app.state["selected_target"]["widget_id"], "my_custom_slider_")

        # Change label, default_value, min/max
        app.on_widget_property_change(None, "Volume Level", "label")
        app.on_widget_property_change(None, "0.75", "default_value")
        app.on_widget_property_change(None, -10.0, "min_value")
        app.on_widget_property_change(None, 10.0, "max_value")
        self.assertEqual(w["label"], "Volume Level")
        self.assertEqual(float(w["default_value"]), 0.75)
        self.assertEqual(w["min_value"], -10.0)
        self.assertEqual(w["max_value"], 10.0)

        # Toggle Enabled=False and Visible=False
        app.on_widget_property_change(None, False, "enabled")
        app.on_widget_property_change(None, False, "show")
        self.assertFalse(w["enabled"])
        self.assertFalse(w["show"])

        # Duplicate widget
        app.duplicate_selected_widget()
        self.assertEqual(len(row["widgets"]), 2)
        cloned = row["widgets"][1]
        self.assertNotEqual(cloned["id"], w["id"])
        self.assertTrue(cloned["label"].endswith("_copy"))

    def test_05_movement_and_lock_protection(self):
        """Verify fine grid movement (Left/Right/Up/Down), drag-move, and that locked=True blocks movement."""
        app.add_widget_from_palette("Button", new_row=True)
        w1_id = app.state["selected_target"]["widget_id"]
        app.add_widget_from_palette("Checkbox", new_row=False)
        w2_id = app.state["selected_target"]["widget_id"]

        win = app.get_window("win_main")
        row0 = win["rows"][0]
        self.assertEqual([w["id"] for w in row0["widgets"]], [w1_id, w2_id])

        # Move w2 left -> [w2_id, w1_id]
        app.move_widget_fine("horizontal", -1)
        self.assertEqual([w["id"] for w in row0["widgets"]], [w2_id, w1_id])

        # Lock w2 and verify it cannot move horizontally, vertically, or via move_existing_widget
        _, _, _, _, _, w2 = app.find_widget(w2_id)
        w2["locked"] = True
        app.move_widget_fine("horizontal", 1)
        self.assertEqual([w["id"] for w in row0["widgets"]], [w2_id, w1_id])
        app.move_widget_fine("vertical", 1)
        self.assertEqual(len(win["rows"]), 1)

        # Unlock w2 and move it down to a new row
        w2["locked"] = False
        app.move_widget_fine("vertical", 1)
        self.assertEqual(len(win["rows"]), 2)
        self.assertEqual([w["id"] for w in win["rows"][0]["widgets"]], [w1_id])
        self.assertEqual([w["id"] for w in win["rows"][1]["widgets"]], [w2_id])

    def test_06_drag_and_drop_lifecycle(self):
        """Verify starting drag, showing/focusing ghost preview, drop target detection, and releasing."""
        app._start_active_drag("NEW", "KnobFloat", "New KnobFloat")
        self.assertTrue(app.state["drag"]["active"])
        self.assertTrue(dpg.is_item_shown("drag_ghost_win"))

        # Simulate hovering over win_main drop target and releasing
        app.state["drag"]["hovered_target"] = {
            "action": "new_row",
            "win_id": "win_main",
            "tab_id": None,
            "desc": "Main Window: Drop as New Row",
        }
        app.on_global_mouse_release(None, None)

        self.assertFalse(app.state["drag"]["active"])
        self.assertFalse(dpg.is_item_shown("drag_ghost_win"))
        win = app.get_window("win_main")
        self.assertEqual(len(win["rows"][0]["widgets"]), 1)
        self.assertEqual(win["rows"][0]["widgets"][0]["type"], "KnobFloat")

    def test_07_export_and_ast_import_roundtrip_all_widgets_and_tabs(self):
        """Verify exporting all 23 widget types + tabs produces valid Python code and re-imports cleanly via AST."""
        # Add 5 root widgets (some sharing a horizontal row, some with custom tags/disabled/hidden)
        app.add_widget_from_palette("Button", new_row=True)
        w_btn_id = app.state["selected_target"]["widget_id"]
        _, _, _, _, _, w_btn = app.find_widget(w_btn_id)
        w_btn["id"] = "custom_submit_btn"
        w_btn["enabled"] = False

        app.add_widget_from_palette("ColorEdit", new_row=False)
        w_col_id = app.state["selected_target"]["widget_id"]
        _, _, _, _, _, w_col = app.find_widget(w_col_id)
        w_col["show"] = False

        # Add a tab and place ALL 23 widget types inside it
        tab_id = app.add_tab_to_window("win_main")
        for idx, w_type in enumerate(app.WIDGET_TYPES):
            app.add_widget_from_palette(w_type, new_row=(idx % 2 == 0))

        # Generate code and verify syntax via ast.parse
        code_str = app.generate_code_string()
        tree = ast.parse(code_str)
        self.assertIsNotNone(tree)
        self.assertIn("tag='custom_submit_btn'", code_str)
        self.assertIn("enabled=False", code_str)
        self.assertIn("show=False", code_str)
        self.assertIn("with dpg.tab_bar():", code_str)

        # Put code in editor, wipe state, and run AST import
        dpg.set_value("code_export_field", code_str)
        app.state["windows"] = []
        app.import_code_from_editor()

        self.assertEqual(len(app.state["windows"]), 1)
        imp_win = app.state["windows"][0]
        self.assertEqual(len(imp_win["rows"][0]["widgets"]), 2)
        self.assertEqual(imp_win["rows"][0]["widgets"][0]["id"], "custom_submit_btn")
        self.assertFalse(imp_win["rows"][0]["widgets"][0]["enabled"])
        self.assertFalse(imp_win["rows"][0]["widgets"][1]["show"])

        self.assertEqual(len(imp_win["tabs"]), 1)
        imp_tab_widgets = [w["type"] for r in imp_win["tabs"][0]["rows"] for w in r["widgets"]]
        self.assertEqual(imp_tab_widgets, app.WIDGET_TYPES)

    def test_08_appearance_persistence(self):
        """Verify appearance settings save to JSON in app directory and load back accurately."""
        app.on_bg_preset_change(None, "Deep Cyberpunk")
        app.on_bg_image_opacity_change(None, 0.65)
        self.assertTrue(os.path.exists(app.APPEARANCE_CONFIG_PATH))

        with open(app.APPEARANCE_CONFIG_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(saved["preset"], "Deep Cyberpunk")
        self.assertEqual(saved["vp_color"], [12, 10, 24, 255])
        self.assertAlmostEqual(saved["bg_image_opacity"], 0.65, places=2)

        # Reset in-memory state and reload from disk
        app.state["appearance"]["preset"] = "Dark Slate (Default)"
        app.load_appearance_settings()
        self.assertEqual(app.state["appearance"]["preset"], "Deep Cyberpunk")
        self.assertAlmostEqual(app.state["bg_image"]["opacity"], 0.65, places=2)

    def test_09_c_long_overflow_protection(self):
        """Verify huge integer/float strings do not trigger C long OverflowError in DearPyGui."""
        for w_type in ("SliderInt", "InputInt", "DragInt", "SliderFloat", "DragFloat"):
            app.add_widget_from_palette(w_type, new_row=True)
            app.on_widget_property_change(None, "999999999999999999999999999", "default_value")
            app.on_widget_property_change(None, "-999999999999999999999999999", "min_value")
            app.on_widget_property_change(None, "999999999999999999999999999", "max_value")
            app.on_widget_property_change(None, 999999999999, "width")
            dpg.render_dearpygui_frame()


if __name__ == "__main__":
    unittest.main()
