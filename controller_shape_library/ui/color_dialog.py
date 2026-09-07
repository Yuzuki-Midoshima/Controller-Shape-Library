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
        self._editing_custom_index = None
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
        self.picker.currentColorChanged.connect(self._on_picker_color_changed)
        self.finished.connect(self._restore_palette)
        self.picker.show()
        self._configure_custom_colors()

    def _configure_custom_colors(self):
        self._color_wells = [
            widget for widget in self.picker.findChildren(QtWidgets.QWidget)
            if widget.metaObject().className().endswith("QWellArray")
        ]
        self._custom_well = (
            max(self._color_wells, key=lambda widget: widget.mapToGlobal(
                widget.rect().topLeft()).y()) if self._color_wells else None
        )
        for well in self._color_wells:
            well.installEventFilter(self)
        for button in self.picker.findChildren(QtWidgets.QPushButton):
            if "Add to Custom" in button.text() or "カスタム" in button.text():
                button.clicked.connect(self._finish_custom_edit)

    def _custom_index_at(self, position):
        if not self._custom_well or not self._custom_well.rect().contains(position):
            return None
        count = QtWidgets.QColorDialog.customCount()
        columns = 8
        rows = max(1, (count + columns - 1) // columns)
        column = min(columns - 1, max(
            0, position.x() * columns // max(1, self._custom_well.width())))
        row = min(rows - 1, max(
            0, position.y() * rows // max(1, self._custom_well.height())))
        index = column * rows + row
        return index if index < count else None

    def _show_custom_menu(self, index, global_position):
        menu = QtWidgets.QMenu(self)
        edit = menu.addAction("編集")
        remove = menu.addAction("削除")
        edit.triggered.connect(lambda: self._edit_custom_color(index))
        remove.triggered.connect(lambda: self._remove_custom_color(index))
        menu.popup(global_position)

    def _edit_custom_color(self, index):
        color = QtWidgets.QColorDialog.customColor(index)
        if color.isValid():
            self._editing_custom_index = index
            self.picker.setCurrentColor(color)

    def _remove_custom_color(self, index):
        QtWidgets.QColorDialog.setCustomColor(index, QtGui.QColor("white"))
        if self._editing_custom_index == index:
            self._editing_custom_index = None
        if self._custom_well:
            self._custom_well.update()

    def _finish_custom_edit(self):
        if self._editing_custom_index is None:
            return
        QtWidgets.QColorDialog.setCustomColor(
            self._editing_custom_index, self.picker.currentColor())
        self._editing_custom_index = None
        if self._custom_well:
            self._custom_well.update()

    def _on_picker_color_changed(self, color):
        if self._editing_custom_index is not None:
            QtWidgets.QColorDialog.setCustomColor(
                self._editing_custom_index, color)
            if self._custom_well:
                self._custom_well.update()
        self.colorPreviewed.emit(color)

    def eventFilter(self, watched, event):
        if watched is self._custom_well:
            if (event.type() == QtCore.QEvent.MouseButtonPress
                    and event.button() == QtCore.Qt.RightButton):
                index = self._custom_index_at(event.position().toPoint())
                if index is not None:
                    self._show_custom_menu(index, event.globalPosition().toPoint())
                    return True
            if event.type() == QtCore.QEvent.ContextMenu:
                index = self._custom_index_at(event.pos())
                if index is not None:
                    self._show_custom_menu(index, event.globalPos())
                    return True
        return super().eventFilter(watched, event)

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
