"""Real Qt widget/callback regressions. No game, clipboard, API or settings writes.

Run with .venv/Scripts/python tests/desktop_runtime_checks.py.
Offscreen rendering checks widget construction and callback behavior, not
physical-display placement, native picker appearance or live OCR quality.
"""
import os
import sys
import types
import tempfile
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from gui_overlay import mirror_window as m
from core_engine.trade_tools import build_stats_index

APP = QApplication.instance() or QApplication([])


class DesktopRuntimeTests(unittest.TestCase):
    def test_settings_dialog_builds_and_picker_button_is_connected(self):
        with patch.object(m, 'save_config'), patch.object(m.SettingsDialog, '_load_connections'), \
             patch.object(m.QFileDialog, 'getOpenFileName', return_value=('C:/Apps/fixture.exe', '')) as picker:
            dialog = m.SettingsDialog(None, {}, voices=[])
            dialog.show(); APP.processEvents()
            dialog.grab().save(os.path.join(tempfile.gettempdir(), 'kalandra-settings-runtime.png'))
            button = next(b for b in dialog.findChildren(QPushButton) if b.text().startswith('Pick'))
            button.click()
            picker.assert_called_once()
            self.assertEqual(dialog.ct_exe_lbl.text(), 'C:/Apps/fixture.exe')
            dialog.close()

    def test_program_picker_selection_and_cancel(self):
        widget = QWidget()
        widget.ct_exe_lbl = QLabel(widget)
        with patch.object(m.QFileDialog, 'getOpenFileName', return_value=('C:/Apps/test.exe', '')):
            m.SettingsDialog._pick_custom_exe(widget)
        self.assertEqual(widget._picked_exe, 'C:/Apps/test.exe')
        self.assertEqual(widget.ct_exe_lbl.text(), widget._picked_exe)
        with patch.object(m.QFileDialog, 'getOpenFileName', return_value=('', '')):
            m.SettingsDialog._pick_custom_exe(widget)
        self.assertEqual(widget._picked_exe, 'C:/Apps/test.exe')
        widget.close()

    def test_scanner_calls_voice_and_falls_back_on_failure(self):
        voice = Mock()
        voice.ai_read_image.return_value = 'Rarity: Rare'
        owner = types.SimpleNamespace(voice=voice, signals=types.SimpleNamespace(log=Mock()))
        self.assertEqual(m.KalandraOverlayApp.ai_image_reader(owner, 'fixture.png', 'read'), 'Rarity: Rare')
        voice.ai_read_image.assert_called_once_with('fixture.png', 'read')
        voice.ai_read_image.side_effect = RuntimeError('fixture offline')
        self.assertEqual(m.KalandraOverlayApp.ai_image_reader(owner, 'fixture.png', 'read'), '')
        owner.voice = None
        self.assertEqual(m.KalandraOverlayApp.ai_image_reader(owner, 'fixture.png', 'read'), '')

    def test_armed_clipboard_verdict_replaces_price_popup(self):
        owner = types.SimpleNamespace(config={'craft_hunter': {'armed': True,
            'targets': [{'mod': '#% increased Spell Damage', 'min': 95}]}},
            _last_clip='', _clip_ts=0, _dashboard=Mock(), _show_price_popup=Mock())
        owner._craft_hunter_confirm = lambda info, txt: m.KalandraOverlayApp._craft_hunter_confirm(owner, info, txt)
        provider = Mock()
        provider.read.return_value = ({'name': 'Test Wand', 'mods': ['104% increased Spell Damage']}, 'fixture item')
        with patch('core_engine.providers.get_provider', return_value=provider), \
             patch('gui_overlay.craft_hunter.show_hunt_toast') as toast:
            m.KalandraOverlayApp._on_clipboard_item(owner)
            self.assertTrue(toast.call_args.args[0]['hit'])
            owner._dashboard.notify_craft_confirm.assert_called_once()
            owner._show_price_popup.assert_not_called()
            m.KalandraOverlayApp._on_clipboard_item(owner)
            self.assertEqual(toast.call_count, 1)  # duplicate notification
            owner.config['craft_hunter']['armed'] = False
            owner._last_clip = ''; owner._clip_ts = 0
            m.KalandraOverlayApp._on_clipboard_item(owner)
            owner._show_price_popup.assert_called_once()

    def test_trade_button_uses_prefilled_query_and_fallback(self):
        idx = build_stats_index({'result': [{'entries': [
            {'id': 'explicit.life', 'text': '+# to maximum Life', 'type': 'explicit'}]}]})
        info = {'base': 'Wand', 'mods': ['+45 to maximum Life']}
        for stats, expected in [(idx, '?q='), ([], '/search/')]:
            with patch('gui_overlay.dashboard._trade_stats_index', return_value=stats), \
                 patch.object(m.QDesktopServices, 'openUrl', return_value=True) as opened:
                popup = m.PricePopup(info, 'fixture', 'Standard')
                popup.show(); APP.processEvents()
                button = next(b for b in popup.findChildren(QPushButton) if b.text().startswith('Trade'))
                button.click()
                self.assertIn(expected, opened.call_args.args[0].toString())
                popup.close()


if __name__ == '__main__':
    unittest.main()
