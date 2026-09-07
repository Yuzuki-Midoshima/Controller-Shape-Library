"""Non-modal controller color picker using the shared rig-tool palette."""

from PySide6 import QtCore, QtGui, QtWidgets


STANDARD_COLOR_COLUMNS = (
    ("#1A1A1A", "#424242", "#757575", "#9E9E9E", "#D0D0D0", "#F5F5F5"),
    ("#4A0D0D", "#8A1919", "#E53935", "#EF5350", "#F58A87", "#FFCDD2"),
    ("#4A2508", "#8A440F", "#FB8C00", "#FFA726", "#FFBE72", "#FFE0B2"),
    ("#4A4308", "#8A7D0F", "#FDD835", "#FFEE58", "#FFF59D", "#FFF9C4"),
    ("#084A22", "#0F8A3E", "#43A047", "#66BB6A", "#A5D6A7", "#C8E6C9"),
    ("#084A47", "#0F8A85", "#00ACC1", "#26C6DA", "#80DEEA", "#B2EBF2"),
    ("#08284A", "#0F4C8A", "#1E88E5", "#42A5F5", "#90CAF9", "#BBDEFB"),
    ("#42084A", "#7A0F8A", "#8E24AA", "#AB47BC", "#CE93D8", "#F8BBD0"),
)
STANDARD_COLORS = tuple(color for column in STANDARD_COLOR_COLUMNS for color in column)


class ColorPreviewDialog(QtWidgets.QDialog):
    colorPreviewed = QtCore.Signal(QtGui.QColor)

    def __init__(self, initial, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setModal(False)
        self.setWindowModality(QtCore.Qt.NonModal)
        self.setWindowFlags(
            self.windowFlags()
            | QtCore.Qt.WindowMinimizeButtonHint
            | QtCore.Qt.WindowMaximizeButtonHint
            | QtCore.Qt.WindowSystemMenuHint
        )
        self.setWindowTitle("Controller Shape Color")
        self.resize(550, 450)
        self.setMinimumSize(480, 400)
        self.setSizeGripEnabled(True)
        self._original_standard = tuple(
            QtWidgets.QColorDialog.standardColor(index)
            for index in range(len(STANDARD_COLORS)))
        for index, value in enumerate(STANDARD_COLORS):
            QtWidgets.QColorDialog.setStandardColor(index, QtGui.QColor(value))

        self.picker = QtWidgets.QColorDialog(initial, self)
        self.picker.setWindowFlags(QtCore.Qt.Widget)
        self.picker.setOption(QtWidgets.QColorDialog.DontUseNativeDialog, True)
        self.picker.setOption(QtWidgets.QColorDialog.NoButtons, True)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.picker, 1)
        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        apply_button = QtWidgets.QPushButton("OK")
        cancel_button = QtWidgets.QPushButton("キャンセル")
        buttons.addWidget(apply_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        apply_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        self.picker.currentColorChanged.connect(self.colorPreviewed)
        self.finished.connect(self._restore_palette)

    def place_next_to(self, window):
        screen = window.screen() or QtWidgets.QApplication.primaryScreen()
        position = window.frameGeometry().topRight() + QtCore.QPoint(8, 0)
        if screen:
            area = screen.availableGeometry()
            position.setX(min(position.x(), area.right() - self.width()))
            position.setY(max(area.top(), min(position.y(), area.bottom() - self.height())))
        self.move(position)

    def _restore_palette(self):
        for index, color in enumerate(self._original_standard):
            QtWidgets.QColorDialog.setStandardColor(index, color)
