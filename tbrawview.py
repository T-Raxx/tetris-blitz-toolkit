"""Polished raw-JSON viewer: syntax highlighting + find + live validity badge.
Drop-in for the editor's Raw JSON tab (proxies setText/toPlainText)."""
import json, re
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QTextCursor

def _fmt(rgb):
    f = QTextCharFormat(); f.setForeground(QColor(*rgb)); return f

class JsonHighlighter(QSyntaxHighlighter):
    # order matters: later rules overwrite overlapping ranges (key must win over its string span)
    RULES = [
        (re.compile(r'"(\\.|[^"\\])*"'), _fmt((160, 210, 140))),                # string value
        (re.compile(r'-?\b\d+(\.\d+)?([eE][+-]?\d+)?\b'), _fmt((240, 180, 90))),  # number
        (re.compile(r'\b(true|false|null)\b'), _fmt((210, 120, 200))),          # keyword
        (re.compile(r'[{}\[\],:]'), _fmt((150, 150, 150))),                     # punctuation
        (re.compile(r'"(\\.|[^"\\])*"(?=\s*:)'), _fmt((130, 170, 255))),        # object key
    ]

    def highlightBlock(self, text):
        for rx, f in self.RULES:
            for m in rx.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), f)

class RawJsonView(QWidget):
    def __init__(self):
        super().__init__()
        self.editor = QPlainTextEdit(); self.editor.setTabStopDistance(28)
        self.hl = JsonHighlighter(self.editor.document())
        self.search = QLineEdit(); self.search.setPlaceholderText("find… (Enter)")
        self.search.returnPressed.connect(self._find_next)
        self.validity = QLabel("—")
        self.editor.textChanged.connect(self._check_validity)
        bar = QHBoxLayout(); bar.addWidget(self.search); bar.addWidget(self.validity); bar.addStretch(1)
        root = QVBoxLayout(self); root.addLayout(bar); root.addWidget(self.editor, 1)

    # QPlainTextEdit-compatible proxy so the editor can swap it in
    def setPlainText(self, s): self.editor.setPlainText(s)
    def setText(self, s): self.editor.setPlainText(s)
    def toPlainText(self): return self.editor.toPlainText()

    def is_valid(self):
        try:
            json.loads(self.editor.toPlainText()); return True
        except Exception:
            return False

    def _check_validity(self):
        try:
            json.loads(self.editor.toPlainText())
            self.validity.setText("valid ✓"); self.validity.setStyleSheet("color:#8fd18f")
        except json.JSONDecodeError as e:
            self.validity.setText(f"line {e.lineno}: {e.msg}"); self.validity.setStyleSheet("color:#e06767")
        except Exception as e:
            self.validity.setText(str(e)); self.validity.setStyleSheet("color:#e06767")

    def _find_next(self):
        q = self.search.text()
        if q and not self.editor.find(q):
            self.editor.moveCursor(QTextCursor.MoveOperation.Start)   # wrap to top
            self.editor.find(q)
