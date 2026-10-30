"""Verify safe launch never schedules startup networking/game/log watchers."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import configure_startup

class SafeStartup(unittest.TestCase):
    def overlay(self):
        return SimpleNamespace(game_watch_timer=Mock(), death_watch_timer=Mock(),
            _on_clipboard_item=Mock(), initial_sync=Mock(), startup_freshness_check=Mock(),
            startup_game_data_check=Mock(), windowTitle=lambda: 'Kalandra', setWindowTitle=Mock())

    def test_safe_startup_stops_watchers_without_scheduling_network_or_game_work(self):
        overlay, schedule, clipboard = self.overlay(), Mock(), Mock()
        configure_startup(overlay, safe=True, schedule=schedule, clipboard=clipboard)
        schedule.assert_not_called()
        overlay.game_watch_timer.stop.assert_called_once()
        overlay.death_watch_timer.stop.assert_called_once()
        clipboard.dataChanged.disconnect.assert_called_once_with(overlay._on_clipboard_item)
        overlay.setWindowTitle.assert_called_once_with('Kalandra (safe startup)')

    def test_normal_startup_keeps_existing_user_selected_flow(self):
        overlay, schedule = self.overlay(), Mock()
        configure_startup(overlay, schedule=schedule)
        self.assertEqual([call.args[0] for call in schedule.call_args_list], [800, 1200, 1600])
        overlay.game_watch_timer.stop.assert_not_called()
        overlay.death_watch_timer.stop.assert_not_called()

if __name__ == '__main__':
    unittest.main()
