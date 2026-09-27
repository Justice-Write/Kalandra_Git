"""Real Qt quest workflow against isolated local fixture stores."""
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtWidgets import QApplication
from core_engine.community_tags import CommunityTags
from core_engine.quest_board import QuestBoard
from core_engine.database_handler import KalandraDBHandler
from core_engine.providers import ScrapedGameData
from gui_overlay.quest_board import QuestBoardTab

APP = QApplication.instance() or QApplication([])


class QuestUiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='quest-ui-')
        self.tags = CommunityTags(os.path.join(self.temp.name, 'tags.json'))
        self.board = QuestBoard(os.path.join(self.temp.name, 'board.json'), community=self.tags)
        self.db = KalandraDBHandler(self.temp.name)
        db = self.db
        class Provider:
            def refresh_quests(self, board): return board.generate_from_db(db)
            def close_quest(self, board, qid): return board.close(qid, db)
        self.ui = QuestBoardTab(board=self.board, community=self.tags, provider=Provider())

    def tearDown(self):
        self.ui.close(); self.db.close(); self.temp.cleanup()

    def test_claim_submit_verify_close_and_credits(self):
        q = self.board.post('tag', 'Fixture Wand'); self.ui.refresh()
        self.ui.player.setText('alice'); self.ui.claim()
        self.assertEqual(self.board.get(q['id'])['status'], 'claimed')
        self.ui.proposal.setText('Spell'); self.ui.evidence.setText('Fixture evidence A')
        self.ui.submit(); self.ui.submit()
        self.assertEqual(self.board.get(q['id'])['status'], 'submitted')
        self.assertFalse(self.ui.buttons['Close verified quest'].isEnabled())
        self.ui.signoff()  # typed names never grant maintainer privileges
        self.assertEqual(self.board.get(q['id'])['status'], 'submitted')
        self.ui.player.setText('bob'); self.ui.evidence.setText('Fixture evidence B'); self.ui.submit()
        self.assertEqual(self.board.get(q['id'])['status'], 'verified')
        self.assertTrue(self.tags.tags_for('Fixture Wand')[0]['verified'])
        self.ui.close_quest(); self.assertEqual(self.board.get(q['id'])['status'], 'closed')
        self.assertIn('1', self.ui.credits.text())
        self.assertEqual(QuestBoard(self.board.path).get(q['id'])['status'], 'closed')

    def test_filters_sources_and_unverified_suggestion(self):
        self.board.post('tag', 'Wand', subject_url='file:///private.txt')
        self.board.post('investigate', 'Boots'); self.ui.refresh()
        self.ui.search.setText('Wand'); self.assertEqual(self.ui.quests.count(), 1)
        with patch('gui_overlay.quest_board.QDesktopServices.openUrl') as opened:
            self.ui.open_source(); opened.assert_not_called()
        self.ui.entity.setText('Wand'); self.ui.tag.setText('Spell'); self.ui.suggest_tag()
        self.assertIn('unverified', self.ui.status.text())
        self.assertFalse(CommunityTags(self.tags.path).tags_for('Wand')[0]['verified'])

    def test_refresh_uses_provider_and_gap_cannot_close_before_verification(self):
        self.db.cursor.execute("INSERT INTO knowledge_ledger(topic_tag,content_payload,source_url,scraped_at,tags) VALUES('Fixture','','https://example.com','now','')")
        self.db.conn.commit(); self.ui.refresh_gaps()
        self.assertEqual(self.ui.quests.count(), 1)
        q = self.ui.selected(); self.ui.close_quest()
        self.assertEqual(self.board.get(q['id'])['status'], 'open')
        self.ui.player.setText('alice'); self.ui.submit()
        self.assertIn('both a proposal and evidence', self.ui.status.text())

    def test_write_failure_is_visible_and_does_not_leave_phantom_entry(self):
        self.ui.entity.setText('Fixture'); self.ui.tag.setText('Spell')
        with patch('core_engine.community_tags.os.replace', side_effect=OSError('fixture disk full')):
            self.ui.suggest_tag()
        self.assertIn('Not saved', self.ui.status.text())
        self.assertEqual(self.tags.all(), [])

    def test_corrupt_store_is_not_overwritten(self):
        for cls in (QuestBoard, CommunityTags):
            path = os.path.join(self.temp.name, cls.__name__ + '.json')
            with open(path, 'w') as file: file.write('broken')
            with self.assertRaises(ValueError): cls(path)
            with open(path) as file: self.assertEqual(file.read(), 'broken')

    def test_provider_closes_connection_on_success_and_failure(self):
        db = Mock(); board = Mock(); provider = ScrapedGameData()
        with patch('core_engine.database_handler.KalandraDBHandler', return_value=db):
            provider.refresh_quests(board)
            board.generate_from_db.assert_called_once_with(db)
            db.close.assert_called_once()
            db.reset_mock(); board.close.side_effect = OSError('fixture failure')
            with self.assertRaises(OSError): provider.close_quest(board, 'fixture')
            db.close.assert_called_once()

    def test_native_layout_capture(self):
        self.board.post('tag', 'Fixture Wand', subject_url='https://example.com')
        self.ui.player.setText('Fixture contributor'); self.ui.refresh()
        self.ui.resize(1050, 700); self.ui.show(); APP.processEvents()
        self.assertTrue(self.ui.grab().save(os.path.join(tempfile.gettempdir(), 'kalandra-quest-runtime.png')))


if __name__ == '__main__': unittest.main()
