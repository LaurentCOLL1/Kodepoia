from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from ..core.paths import AppPaths
from ..runtime import KodeRuntime


def _build_window(runtime: KodeRuntime):
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QPushButton, QStackedWidget, QTextEdit, QVBoxLayout, QWidget

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Kodepoia — KodeStudio")
            self.resize(1100, 720)
            root = QWidget()
            outer = QVBoxLayout(root)
            body = QHBoxLayout()
            self.nav = QListWidget()
            self.nav.setFixedWidth(190)
            self.stack = QStackedWidget()
            pages = [
                ("Projects", "Aucun projet ouvert. Le Project Wizard arrivera en R2."),
                ("Chat", "KodeBrain sera branché en R3. Le Protected Core est déjà actif."),
                ("Security", "KodeGuardian, KodePermissions, KodeAudit, KodeSandbox et KodeSecrets sont actifs."),
                ("Audit", "Les décisions de sécurité sont écrites dans le journal local append-only."),
                ("Settings", "Paramètres locaux Kodepoia. Aucun secret n'est affiché ici."),
            ]
            for title, text in pages:
                self.nav.addItem(QListWidgetItem(title))
                page = QWidget()
                layout = QVBoxLayout(page)
                heading = QLabel(title)
                font = heading.font()
                font.setPointSize(18)
                font.setBold(True)
                heading.setFont(font)
                description = QLabel(text)
                description.setWordWrap(True)
                layout.addWidget(heading)
                layout.addWidget(description)
                if title == "Security":
                    stop = QPushButton("Activer l'arrêt d'urgence")
                    stop.clicked.connect(self._kill_switch)
                    reset = QPushButton("Réarmer KodeGuardian")
                    reset.clicked.connect(self._reset_guardian)
                    self.security_state = QLabel()
                    layout.addWidget(stop)
                    layout.addWidget(reset)
                    layout.addWidget(self.security_state)
                if title == "Audit":
                    self.audit_view = QTextEdit()
                    self.audit_view.setReadOnly(True)
                    layout.addWidget(self.audit_view)
                    refresh = QPushButton("Rafraîchir")
                    refresh.clicked.connect(self._refresh_audit)
                    layout.addWidget(refresh)
                layout.addStretch(1)
                self.stack.addWidget(page)
            self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
            self.nav.setCurrentRow(0)
            body.addWidget(self.nav)
            body.addWidget(self.stack, 1)
            outer.addLayout(body, 1)
            status = QFrame()
            status_layout = QHBoxLayout(status)
            self.guardian_badge = QLabel()
            status_layout.addWidget(self.guardian_badge)
            status_layout.addWidget(QLabel("Sandbox ●"))
            status_layout.addWidget(QLabel("Ollama ○ (R3)"))
            status_layout.addWidget(QLabel("Git ●"))
            status_layout.addStretch(1)
            outer.addWidget(status)
            self.setCentralWidget(root)
            self._refresh_security()
            self._refresh_audit()

        def _refresh_security(self) -> None:
            stopped = runtime.guardian.stopped
            value = "ARRÊTÉ" if stopped else "ACTIF"
            self.guardian_badge.setText(f"Guardian {'■' if stopped else '●'} {value}")
            if hasattr(self, "security_state"):
                self.security_state.setText(f"État KodeGuardian : {value}")

        def _kill_switch(self) -> None:
            runtime.guardian.kill_switch("kodestudio.user")
            runtime.sandbox.kill_all()
            self._refresh_security()
            self._refresh_audit()

        def _reset_guardian(self) -> None:
            runtime.guardian.reset_kill_switch("kodestudio.user")
            self._refresh_security()
            self._refresh_audit()

        def _refresh_audit(self) -> None:
            if hasattr(self, "audit_view"):
                events = runtime.audit.tail(100)
                self.audit_view.setPlainText("\n".join(str(item) for item in events))

    return MainWindow()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kodestudio")
    parser.add_argument("--smoke-test", action="store_true", help="start offscreen and exit automatically")
    args = parser.parse_args(argv)
    if args.smoke_test:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("KodeStudio requires the optional UI dependency. Install with: pip install -e '.[ui]'", file=sys.stderr)
        return 2
    if args.smoke_test:
        temp = tempfile.TemporaryDirectory(prefix="kodepoia-ui-smoke-")
        base = Path(temp.name)
        paths = AppPaths(base / "data", base / "config", base / "cache")
    else:
        temp = None
        paths = AppPaths.default()
    application = QApplication.instance() or QApplication(sys.argv[:1])
    runtime = KodeRuntime.build(paths)
    window = _build_window(runtime)
    window.show()
    if args.smoke_test:
        QTimer.singleShot(150, application.quit)
    code = application.exec()
    if temp is not None:
        temp.cleanup()
    return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
