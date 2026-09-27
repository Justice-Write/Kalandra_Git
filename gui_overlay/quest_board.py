"""Local metadata quests and player-reported tags; no network or game input."""
import os
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QListWidget, QListWidgetItem, QPlainTextEdit)
from core_engine.quest_board import QuestBoard, QUEST_TYPES, STATUSES
from core_engine.community_tags import CommunityTags
from core_engine.providers import get_provider


class QuestBoardTab(QWidget):
    def __init__(self, config=None, board=None, community=None, provider=None, parent=None):
        super().__init__(parent)
        config = config or {}
        folder = config.get('dir_database')
        self.community = community or CommunityTags(
            os.path.join(folder, 'community_tags.json') if folder else None)
        self.board = board or QuestBoard(
            path=os.path.join(folder, 'community_quests.json') if folder else None,
            verify_threshold=config.get('quest_verify_threshold', 2),
            maintainers=config.get('quest_maintainers', []), community=self.community)
        self.provider = provider or get_provider('game_data')
        root = QVBoxLayout(self)
        note = QLabel('Local Quest Board — metadata only. Player reports remain unverified until agreement or trusted sign-off. '
                      'Contributor names are local attribution, not authenticated online identities.')
        note.setWordWrap(True); root.addWidget(note)
        row = QHBoxLayout()
        self.player = QLineEdit(config.get('community_contributor', ''))
        self.player.setPlaceholderText('Your contributor name')
        row.addWidget(self.player)
        self.status_filter = QComboBox(); self.status_filter.addItems(['All statuses', *STATUSES])
        self.type_filter = QComboBox(); self.type_filter.addItems(['All types', *QUEST_TYPES])
        self.search = QLineEdit(); self.search.setPlaceholderText('Filter subject or title')
        for widget in (self.status_filter, self.type_filter, self.search): row.addWidget(widget)
        root.addLayout(row)
        self.quests = QListWidget(); root.addWidget(self.quests, 1)
        self.details = QPlainTextEdit(); self.details.setReadOnly(True); root.addWidget(self.details, 1)
        self.proposal = QLineEdit(); self.proposal.setPlaceholderText('Proposal: comma-separated tags, or applies: target for a relationship')
        self.evidence = QLineEdit(); self.evidence.setPlaceholderText('Evidence: source URL or a concrete observation')
        root.addWidget(self.proposal); root.addWidget(self.evidence)
        actions = QHBoxLayout()
        self.buttons = {}
        for text, callback in [('Refresh gaps', self.refresh_gaps), ('Claim', self.claim),
                ('Submit evidence', self.submit), ('Maintainer sign-off', self.signoff),
                ('Close verified quest', self.close_quest), ('Open source', self.open_source)]:
            button = QPushButton(text); button.clicked.connect(callback)
            self.buttons[text] = button; actions.addWidget(button)
        root.addLayout(actions)
        root.addWidget(QLabel('Suggest a tag — saved separately as player-reported, unverified'))
        tags = QHBoxLayout()
        self.entity = QLineEdit(); self.entity.setPlaceholderText('Entity name')
        self.tag = QLineEdit(); self.tag.setPlaceholderText('Game tag')
        self.tag_note = QLineEdit(); self.tag_note.setPlaceholderText('Source / explanation')
        for widget in (self.entity, self.tag, self.tag_note): tags.addWidget(widget)
        button = QPushButton('Suggest tag'); button.clicked.connect(self.suggest_tag); tags.addWidget(button)
        root.addLayout(tags)
        self.status = QLabel(); self.status.setWordWrap(True); root.addWidget(self.status)
        self.credits = QLabel(); root.addWidget(self.credits)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        self.type_filter.currentIndexChanged.connect(self.refresh)
        self.search.textChanged.connect(self.refresh)
        self.player.textChanged.connect(self.show_quest)
        self.quests.currentItemChanged.connect(self.show_quest)
        self.refresh()

    def selected(self):
        item = self.quests.currentItem()
        return self.board.get(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def refresh(self, *_):
        selected = self.selected()
        self.quests.clear()
        status = self.status_filter.currentText() if self.status_filter.currentIndex() else None
        qtype = self.type_filter.currentText() if self.type_filter.currentIndex() else None
        term = self.search.text().strip().lower()
        for quest in self.board.board(status=status, qtype=qtype):
            if term and term not in (quest['title'] + ' ' + quest['subject']).lower(): continue
            item = QListWidgetItem(f"[{quest['status']}] {quest['title']}")
            item.setData(Qt.ItemDataRole.UserRole, quest['id']); self.quests.addItem(item)
            if selected and quest['id'] == selected['id']: self.quests.setCurrentItem(item)
        if self.quests.currentRow() < 0 and self.quests.count(): self.quests.setCurrentRow(0)
        self.show_quest()

    def show_quest(self, *_):
        quest = self.selected(); player = self.player.text().strip()
        live = bool(quest and quest['status'] in ('open', 'claimed', 'submitted', 'reopened'))
        for name in ('Claim', 'Submit evidence'): self.buttons[name].setEnabled(live and bool(player))
        self.buttons['Maintainer sign-off'].setEnabled(live and player.lower() in {m.lower() for m in self.board.maintainers})
        self.buttons['Close verified quest'].setEnabled(bool(quest and quest['status'] == 'verified'))
        self.buttons['Open source'].setEnabled(bool(quest and QUrl(quest.get('subject_url', '')).scheme() in ('http', 'https')))
        self.credits.setText(f'Your verified contribution credits: {self.board.credits(player) if player else 0}')
        if not quest:
            self.details.clear(); return
        lines = [quest['title'], 'Subject: ' + quest['subject'], 'Criteria: ' + quest['criteria'],
                 'Status: ' + quest['status'], f'Agreement requires {self.board.verify_threshold} distinct contributors.',
                 'Resolution: ' + quest.get('resolution', ''), 'Evidence:']
        for sub in quest.get('submissions', []):
            lines.append(f"- {sub['player']}: {sub['proposal']}\n  {sub['evidence']}")
        for verification in quest.get('verifications', []):
            lines.append('Verification: ' + verification['how'])
        self.details.setPlainText('\n'.join(lines))

    def perform(self, action):
        try:
            message = action()
            self.status.setText(message)
        except Exception as error:
            self.status.setText('Not saved: ' + str(error))
        self.refresh()

    def refresh_gaps(self):
        def action():
            if not self.provider: raise ValueError('Game-data provider unavailable')
            result = self.provider.refresh_quests(self.board)
            return f"Created {len(result['created'])} quests; reopened {len(result['reopened'])}."
        self.perform(action)

    def claim(self):
        quest = self.selected()
        if quest: self.perform(lambda: 'Claim recorded.' if self.board.claim(quest['id'], self.player.text()) else 'Claim not accepted.')

    def submit(self):
        quest = self.selected()
        if not quest: return
        def action():
            if not self.proposal.text().strip() or not self.evidence.text().strip():
                raise ValueError('Add both a proposal and evidence')
            result = self.board.submit(quest['id'], self.player.text(), self.evidence.text(), self.proposal.text())
            return 'Evidence saved — ' + result['status'] if result else 'Submission not accepted.'
        self.perform(action)

    def signoff(self):
        quest = self.selected()
        if quest: self.perform(lambda: 'Trusted sign-off recorded.' if self.board.signoff(quest['id'], self.player.text(), self.proposal.text()) else 'Sign-off not accepted.')

    def close_quest(self):
        quest = self.selected()
        if quest: self.perform(lambda: 'Quest closed.' if self.provider and self.provider.close_quest(self.board, quest['id']) else 'Quest is not verified or its data gap remains.')

    def open_source(self):
        quest = self.selected()
        url = QUrl(quest.get('subject_url', '')) if quest else QUrl()
        if url.scheme() in ('http', 'https'): QDesktopServices.openUrl(url)

    def suggest_tag(self):
        def action():
            entry = self.community.suggest_tag(self.entity.text(), self.tag.text(), self.tag_note.text())
            if not entry: raise ValueError('Enter an entity and game tag')
            return 'Saved — player-reported, unverified.' if not entry['verified'] else 'Existing verified tag received your report.'
        self.perform(action)
