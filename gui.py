import os
import sys
from typing import Iterable

from PyQt5 import QtCore, QtGui, QtWidgets

import cli


class RequeryWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal(set)
    error = QtCore.pyqtSignal(str)

    def __init__(self, pages: int | None):
        super().__init__()
        self.pages = pages

    @QtCore.pyqtSlot()
    def run(self):
        try:
            songs = set()
            for page in cli.inf_gen(self.pages):
                html = cli.fetch_song_list_html(page)
                if not html:
                    break

                page_songs = cli.get_song_set(html)
                if not page_songs:
                    break

                songs.update(page_songs)

            if songs:
                cli.save_song_set(songs)
            self.finished.emit(songs)
        except Exception as exc:  # pragma: no cover
            self.error.emit(str(exc))


class GuitarFlashSearchWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Guitar Flash Search")
        self.resize(900, 600)

        self.song_set: set[tuple[str, str]] = set()
        self.worker_thread: QtCore.QThread | None = None

        self._build_ui()
        self._load_song_set()
        self._fill_table(self.song_set)

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        root_layout = QtWidgets.QVBoxLayout(central)

        search_row = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Digite o nome da música")
        self.search_input.returnPressed.connect(self.on_search_clicked)

        self.search_button = QtWidgets.QPushButton("Buscar")
        self.search_button.clicked.connect(self.on_search_clicked)

        self.clear_button = QtWidgets.QPushButton("Limpar")
        self.clear_button.clicked.connect(self.on_clear_clicked)

        search_row.addWidget(self.search_input)
        search_row.addWidget(self.search_button)
        search_row.addWidget(self.clear_button)

        refresh_row = QtWidgets.QHBoxLayout()
        self.pages_spin = QtWidgets.QSpinBox()
        self.pages_spin.setMinimum(1)
        self.pages_spin.setMaximum(999)
        self.pages_spin.setValue(10)
        self.pages_spin.setPrefix("Páginas: ")

        self.requery_button = QtWidgets.QPushButton("Atualizar lista online")
        self.requery_button.clicked.connect(self.on_requery_clicked)

        refresh_row.addWidget(self.pages_spin)
        refresh_row.addWidget(self.requery_button)
        refresh_row.addStretch(1)

        self.status_label = QtWidgets.QLabel("Pronto")

        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Música", "Link"])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.Stretch
        )
        # não permitir alterar altura das linhas
        self.table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget::item:selected {"
            "background-color: transparent;"
            "color: palette(text);"
            "}"
        )
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)

        root_layout.addLayout(search_row)
        root_layout.addLayout(refresh_row)
        root_layout.addWidget(self.status_label)
        root_layout.addWidget(self.table)

    def _load_song_set(self):
        if os.path.exists(cli.CSV_PATH):
            self.song_set = cli.load_song_set()
            if self.song_set:
                self.status_label.setText(f"{len(self.song_set)} músicas carregadas")
            else:
                self.status_label.setText("Arquivo encontrado, mas sem músicas válidas")
        else:
            self.status_label.setText(
                "CSV não encontrado. Use 'Atualizar lista online'."
            )

    def _fill_table(self, songs: Iterable[tuple[str, str]]):
        sorted_songs = sorted(songs, key=lambda x: x[0].lower())
        self.table.setRowCount(len(sorted_songs))

        for row, (name, link) in enumerate(sorted_songs):
            name_item = QtWidgets.QTableWidgetItem(name)
            link_item = QtWidgets.QTableWidgetItem(link)
            link_item.setForeground(QtGui.QColor("#1a73e8"))
            font = link_item.font()
            font.setUnderline(True)
            link_item.setFont(font)

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, link_item)

    def on_search_clicked(self):
        term = self.search_input.text().strip()

        if not self.song_set:
            self.status_label.setText("Sem dados carregados para busca")
            self.table.setRowCount(0)
            return

        if not term:
            self._fill_table(self.song_set)
            self.status_label.setText(
                f"Mostrando todas as {len(self.song_set)} músicas"
            )
            return

        results = cli.search_song(term, self.song_set)
        self._fill_table(results)

        if results:
            self.status_label.setText(f"{len(results)} resultado(s) para '{term}'")
        else:
            self.status_label.setText("Nenhuma música encontrada")

    def on_clear_clicked(self):
        self.search_input.clear()
        if self.song_set:
            self._fill_table(self.song_set)
            self.status_label.setText(
                f"Mostrando todas as {len(self.song_set)} músicas"
            )
        else:
            self.table.setRowCount(0)
            self.status_label.setText("Sem dados carregados")

    def on_requery_clicked(self):
        # deve confirmar se o usuário quer atualizar, pois isso pode levar um tempo considerável
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Confirmar atualização",
            "Atualizar a lista online pode levar um tempo considerável. Deseja continuar?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if confirm != QtWidgets.QMessageBox.Yes:
            return
        pages = self.pages_spin.value()
        self.requery_button.setEnabled(False)
        self.search_button.setEnabled(False)
        self.status_label.setText("Atualizando lista online...")

        self.worker_thread = QtCore.QThread(self)
        self.worker = RequeryWorker(pages)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_requery_finished)
        self.worker.error.connect(self._on_requery_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    def _on_requery_finished(self, songs: set[tuple[str, str]]):
        self.requery_button.setEnabled(True)
        self.search_button.setEnabled(True)

        if songs:
            self.song_set = songs
            self._fill_table(self.song_set)
            self.status_label.setText(
                f"Lista atualizada com {len(self.song_set)} músicas"
            )
        else:
            self.status_label.setText("Nenhum dado novo encontrado")

    def _on_requery_error(self, message: str):
        self.requery_button.setEnabled(True)
        self.search_button.setEnabled(True)
        self.status_label.setText(f"Erro ao atualizar: {message}")

    def on_cell_double_clicked(self, row: int, column: int):
        _ = column
        link_item = self.table.item(row, 1)
        if not link_item:
            return

        link = link_item.text().strip()
        if link:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(link))


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = GuitarFlashSearchWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
