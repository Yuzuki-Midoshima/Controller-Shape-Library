"""Japanese PySide6 UI for Controller-Shape-Library."""
from __future__ import annotations

import os
import json
from pathlib import Path

from maya import OpenMayaUI as omui
from maya import cmds
from PySide6 import QtCore, QtGui, QtWidgets
from shiboken6 import wrapInstance

from .. import api
from ..core.shape_data import SHAPES
from .color_dialog import ColorPreviewDialog


SHAPE_MIME = "application/x-controller-shape-items"


class ShapeSourceList(QtWidgets.QListWidget):
    def startDrag(self, supported_actions):
        item_ids = [item.data(QtCore.Qt.UserRole + 2)
                    for item in self.selectedItems()]
        if not item_ids:
            return
        mime = QtCore.QMimeData()
        mime.setData(SHAPE_MIME, json.dumps(item_ids).encode("utf-8"))
        drag = QtGui.QDrag(self)
        drag.setMimeData(mime)
        drag.exec(QtCore.Qt.CopyAction)


class OrganizerList(QtWidgets.QListWidget):
    itemsDropped = QtCore.Signal(list)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(SHAPE_MIME):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(SHAPE_MIME):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(SHAPE_MIME):
            values = bytes(event.mimeData().data(SHAPE_MIME)).decode("utf-8")
            self.itemsDropped.emit(json.loads(values))
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class ShapePicker(QtWidgets.QDialog):
    itemsChosen = QtCore.Signal(list)

    def __init__(self, entries, categories, parent=None):
        super().__init__(parent)
        self.setWindowTitle("シェイプを追加")
        self.setWindowFlags(self.windowFlags()
                            | QtCore.Qt.WindowMinimizeButtonHint
                            | QtCore.Qt.WindowMaximizeButtonHint)
        self.resize(560, 430)
        layout = QtWidgets.QVBoxLayout(self)
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs, 1)
        records = [(None, "ALL")] + [(item["key"], item["label"])
                                      for item in categories]
        for category, label in records:
            shape_list = ShapeSourceList()
            shape_list.setViewMode(QtWidgets.QListView.IconMode)
            shape_list.setResizeMode(QtWidgets.QListView.Adjust)
            shape_list.setMovement(QtWidgets.QListView.Static)
            shape_list.setWrapping(True)
            shape_list.setIconSize(QtCore.QSize(72, 72))
            shape_list.setGridSize(QtCore.QSize(112, 102))
            shape_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
            shape_list.setDragEnabled(True)
            for item_id, name, icon, item_category in entries:
                if category is not None and item_category != category:
                    continue
                item = QtWidgets.QListWidgetItem(icon, name)
                item.setData(QtCore.Qt.UserRole + 2, item_id)
                shape_list.addItem(item)
            shape_list.itemDoubleClicked.connect(lambda _item, view=shape_list:
                                                  self._choose(view))
            self.tabs.addTab(shape_list, label)
        add_button = QtWidgets.QPushButton("選択したシェイプを追加")
        add_button.clicked.connect(lambda: self._choose(
            self.tabs.currentWidget()))
        layout.addWidget(add_button)

    def _choose(self, shape_list):
        item_ids = [item.data(QtCore.Qt.UserRole + 2)
                    for item in shape_list.selectedItems()]
        if item_ids:
            self.itemsChosen.emit(item_ids)


def maya_main_window():
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget) if pointer else None


def shape_icon(data, apply_orientation=False):
    """Render a warm-yellow preview using a lightweight 3D projection."""
    pixmap = QtGui.QPixmap(72, 72)
    pixmap.fill(QtGui.QColor("#303030"))
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setPen(QtGui.QPen(QtGui.QColor("#f0c84b"), 1.5))

    def oriented(point):
        if apply_orientation:
            # Serialized Maya controller CVs use the opposite horizontal
            # convention from the library preview. Only X is mirrored here;
            # flipping Z as well rotates text by 180 degrees.
            return (-point[0], point[1], point[2])
        return point

    points = [oriented(p) for curve in data["curves"]
              for p in curve["points"]]
    if points:
        projected = [(p[0] + p[1] * .35, p[2] - p[1] * .35) for p in points]
        xs, ys = zip(*projected)
        scale = 56.0 / max(max(xs) - min(xs), max(ys) - min(ys), .000001)
        center_x = (max(xs) + min(xs)) * .5
        center_y = (max(ys) + min(ys)) * .5
        for curve in data["curves"]:
            path = QtGui.QPainterPath()
            for index, raw_point in enumerate(curve["points"]):
                point = oriented(raw_point)
                x = point[0] + point[1] * .35
                y = point[2] - point[1] * .35
                pos = QtCore.QPointF(36 + (x - center_x) * scale,
                                     36 - (y - center_y) * scale)
                path.moveTo(pos) if index == 0 else path.lineTo(pos)
            painter.drawPath(path)
    painter.end()
    return QtGui.QIcon(pixmap)


class MainWindow(QtWidgets.QDialog):
    OBJECT_NAME = "ControllerShapeLibraryWindow"
    DEFAULT_COLOR_INDEX = 17

    def __init__(self, parent=None):
        super().__init__(parent or maya_main_window())
        self.setWindowFlags(
            self.windowFlags()
            | QtCore.Qt.WindowMinimizeButtonHint
            | QtCore.Qt.WindowMaximizeButtonHint
            | QtCore.Qt.WindowSystemMenuHint
        )
        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle("Controller-Shape-Library 1.1")
        self.setMinimumSize(480, 400)
        self.resize(560, 460)
        self.setSizeGripEnabled(True)
        self._shape = "circle"
        self._shape_lists = []
        self._library_path = api.library_path()
        category_records = api.library_categories(self._library_path)
        self._shape_categories = [item["key"] for item in category_records]
        self._category_labels = {item["key"]: item["label"]
                                 for item in category_records}
        self._updating_shapes = False
        self._updating_categories = False
        self._library_undo = []
        self._library_redo = []
        self._library_list = None
        self._organizer_lists = []
        self._last_model_panel = self._model_panel()
        self._color_dialog = None
        self._creation_color = self.DEFAULT_COLOR_INDEX
        self._pending_creation_color = None
        self._color_original = {}
        self._color_targets = []
        self._color_undo_open = False
        self._color_selection_job = None
        self._build_ui()

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 8)
        root.setSpacing(8)
        self.tabs = QtWidgets.QTabWidget()
        root.addWidget(self.tabs)
        self.tabs.addTab(self._create_tab(), "作成")
        self.tabs.addTab(self._setup_tab(), "編集")
        self.tabs.addTab(self._library_tab(), "ライブラリ")
        self.tabs.currentChanged.connect(self._outer_tab_changed)
        self.status = QtWidgets.QLabel("準備完了")
        self.status.setToolTip("読込元: " + os.path.abspath(__file__))
        self.status.setMinimumHeight(24)
        self.status.setStyleSheet("color:#bdbdbd; padding-left:4px;")
        root.addWidget(self.status)

    def _create_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(5)
        settings = QtWidgets.QWidget()
        settings_layout = QtWidgets.QHBoxLayout(settings)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(6)
        self.name_edit = QtWidgets.QLineEdit("controller")
        self.name_edit.setPlaceholderText("例: L_arm_CTRL")
        self.size_spin = QtWidgets.QDoubleSpinBox()
        self.size_spin.setRange(.001, 10000)
        self.size_spin.setDecimals(3)
        self.size_spin.setValue(1.0)
        settings_layout.addWidget(QtWidgets.QLabel("名前"))
        settings_layout.addWidget(self.name_edit, 1)
        settings_layout.addWidget(QtWidgets.QLabel("サイズ"))
        settings_layout.addWidget(self.size_spin)
        layout.addWidget(settings)
        text_row = QtWidgets.QWidget()
        text_layout = QtWidgets.QHBoxLayout(text_row)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(6)
        self.text_edit = QtWidgets.QLineEdit()
        self.text_edit.setPlaceholderText("任意の文字を入力")
        text_button = QtWidgets.QPushButton("文字を作成")
        text_button.clicked.connect(self._create_text)
        self.text_edit.returnPressed.connect(self._create_text)
        text_layout.addWidget(QtWidgets.QLabel("文字"))
        text_layout.addWidget(self.text_edit, 1)
        text_layout.addWidget(text_button)
        layout.addWidget(text_row)
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setPlaceholderText("シェイプ名を検索…")
        self.search_edit.textChanged.connect(self._filter_shapes)
        layout.addWidget(self.search_edit)
        tabs = QtWidgets.QTabWidget()
        tabs.setMinimumHeight(210)
        self.shape_tabs = tabs
        for category in self._shape_categories:
            shape_list = OrganizerList()
            shape_list.setViewMode(QtWidgets.QListView.IconMode)
            shape_list.setResizeMode(QtWidgets.QListView.Adjust)
            shape_list.setMovement(QtWidgets.QListView.Snap)
            shape_list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
            shape_list.setDragEnabled(True)
            shape_list.setAcceptDrops(True)
            shape_list.setDropIndicatorShown(True)
            shape_list.setStyleSheet(
                "QListWidget::item:selected {background:#3f647d;} "
                "QAbstractItemView::drop-indicator {background:#55b7ff; height:4px;}")
            shape_list.setDefaultDropAction(QtCore.Qt.MoveAction)
            shape_list.setWrapping(True)
            shape_list.setWordWrap(False)
            shape_list.setIconSize(QtCore.QSize(72, 72))
            shape_list.setGridSize(QtCore.QSize(112, 102))
            shape_list.setSpacing(0)
            shape_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
            # Mouse interaction only: Q/W/E/R must remain Maya viewport hotkeys.
            shape_list.setFocusPolicy(QtCore.Qt.NoFocus)
            shape_list.itemClicked.connect(self._create_item)
            items = [(key, data) for key, data in SHAPES.items()
                     if data.get("category") == category]
            for key, data in items:
                item = QtWidgets.QListWidgetItem(shape_icon(data), data.get("label", key))
                item.setData(QtCore.Qt.UserRole, key)
                item.setData(QtCore.Qt.UserRole + 1, False)
                item.setData(QtCore.Qt.UserRole + 2, "builtin:" + key)
                item.setToolTip("{} を作成".format(data.get("label", key)))
                shape_list.addItem(item)
            self._shape_lists.append(shape_list)
            shape_list.model().rowsMoved.connect(
                lambda *args, category=category: self._save_tab_order(category))
            tabs.addTab(shape_list, self._category_labels[category])
        layout.addWidget(tabs, 1)
        quick_actions = QtWidgets.QHBoxLayout()
        quick_actions.setSpacing(6)
        combine_button = QtWidgets.QPushButton("シェイプ結合")
        combine_button.setToolTip(
            "2つ以上を選択し、最後に選択したControllerへShapeを統合します")
        combine_button.clicked.connect(self._combine_selected)
        color_button = QtWidgets.QPushButton("カラー…")
        color_button.setToolTip("次に作成するControllerの色を指定します")
        color_button.clicked.connect(self._show_color_picker)
        self.color_button = color_button
        self._update_color_button()
        quick_actions.addWidget(combine_button, 1)
        quick_actions.addWidget(color_button, 1)
        layout.addLayout(quick_actions)
        return widget

    def _setup_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        snap_group = QtWidgets.QGroupBox("位置合わせ")
        snap_layout = QtWidgets.QVBoxLayout(snap_group)
        hint = QtWidgets.QLabel("① コントローラー → ② 合わせ先 の順で選択")
        hint.setStyleSheet("color:#bdbdbd;")
        snap_button = QtWidgets.QPushButton("位置と回転をスナップ")
        snap_button.setMinimumHeight(30)
        snap_button.clicked.connect(self._snap)
        snap_layout.addWidget(hint)
        snap_layout.addWidget(snap_button)
        layout.addWidget(snap_group)

        group_box = QtWidgets.QGroupBox("グループ作成")
        group_layout = QtWidgets.QVBoxLayout(group_box)
        group_layout.addWidget(QtWidgets.QLabel("選択したControllerと同じ位置に作成します"))
        names = QtWidgets.QHBoxLayout()
        self.zero_suffix_edit = QtWidgets.QLineEdit("_ZERO")
        self.offset_suffix_edit = QtWidgets.QLineEdit("_OFFSET")
        self.zero_position_combo = QtWidgets.QComboBox()
        self.offset_position_combo = QtWidgets.QComboBox()
        for combo in (self.zero_position_combo, self.offset_position_combo):
            combo.addItem("後", "suffix")
            combo.addItem("前", "prefix")
        names.addWidget(QtWidgets.QLabel("ZERO名"))
        names.addWidget(self.zero_suffix_edit, 1)
        names.addWidget(self.zero_position_combo)
        names.addWidget(QtWidgets.QLabel("OFFSET名"))
        names.addWidget(self.offset_suffix_edit, 1)
        names.addWidget(self.offset_position_combo)
        group_layout.addLayout(names)
        buttons = QtWidgets.QHBoxLayout()
        zero_button = QtWidgets.QPushButton("ZERO グループ")
        zero_button.setMinimumHeight(30)
        zero_button.clicked.connect(lambda: self._create_groups(
            api.create_zero_group, self.zero_suffix_edit.text(),
            self.zero_position_combo.currentData()))
        offset_button = QtWidgets.QPushButton("OFFSET グループ")
        offset_button.setMinimumHeight(30)
        offset_button.clicked.connect(lambda: self._create_groups(
            api.create_offset_group, self.offset_suffix_edit.text(),
            self.offset_position_combo.currentData()))
        buttons.addWidget(zero_button, 1)
        buttons.addWidget(offset_button, 1)
        group_layout.addLayout(buttons)
        layout.addWidget(group_box)
        layout.addStretch()
        return widget

    def _library_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(5)
        library_tabs = QtWidgets.QTabWidget()
        layout.addWidget(library_tabs)

        register = QtWidgets.QWidget()
        register_layout = QtWidgets.QVBoxLayout(register)
        register_layout.setContentsMargins(4, 4, 4, 4)
        self.library_file_label = QtWidgets.QLabel()
        self.library_file_label.setStyleSheet("color:#bdbdbd;")
        register_layout.addWidget(self.library_file_label)
        self._library_list = QtWidgets.QListWidget()
        self._library_list.setViewMode(QtWidgets.QListView.IconMode)
        self._library_list.setResizeMode(QtWidgets.QListView.Adjust)
        self._library_list.setMovement(QtWidgets.QListView.Static)
        self._library_list.setIconSize(QtCore.QSize(72, 72))
        self._library_list.setGridSize(QtCore.QSize(112, 102))
        self._library_list.setFocusPolicy(QtCore.Qt.NoFocus)
        self._library_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._library_list.currentItemChanged.connect(self._library_item_changed)
        register_layout.addWidget(self._library_list, 1)
        save_layout = QtWidgets.QHBoxLayout()
        self.library_name_edit = QtWidgets.QLineEdit()
        self.library_name_edit.setPlaceholderText("プリセット名")
        self.library_category_combo = QtWidgets.QComboBox()
        for key in self._shape_categories:
            self.library_category_combo.addItem(self._category_labels[key], key)
        save_button = QtWidgets.QPushButton("保存／上書き")
        save_button.clicked.connect(self._save_library_shape)
        save_layout.addWidget(self.library_name_edit, 1)
        save_layout.addWidget(QtWidgets.QLabel("登録先タブ"))
        save_layout.addWidget(self.library_category_combo)
        save_layout.addWidget(save_button)
        register_layout.addLayout(save_layout)
        buttons = QtWidgets.QHBoxLayout()
        refresh_button = QtWidgets.QPushButton("更新")
        refresh_button.clicked.connect(self._refresh_library)
        remove_button = QtWidgets.QPushButton("削除")
        remove_button.clicked.connect(self._remove_library_shape)
        buttons.addWidget(refresh_button)
        buttons.addWidget(remove_button)
        register_layout.addLayout(buttons)
        library_tabs.addTab(register, "登録")

        organize = QtWidgets.QWidget()
        organize_layout = QtWidgets.QVBoxLayout(organize)
        organize_layout.setContentsMargins(4, 4, 4, 4)
        self.organizer_tabs = QtWidgets.QTabWidget()
        for category in self._shape_categories:
            shape_list = OrganizerList()
            shape_list.setViewMode(QtWidgets.QListView.IconMode)
            shape_list.setResizeMode(QtWidgets.QListView.Adjust)
            shape_list.setMovement(QtWidgets.QListView.Snap)
            shape_list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
            shape_list.setDragEnabled(True)
            shape_list.setAcceptDrops(True)
            shape_list.setDropIndicatorShown(True)
            shape_list.setDefaultDropAction(QtCore.Qt.MoveAction)
            shape_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
            shape_list.setStyleSheet(
                "QListWidget::item:selected {background:#3f647d;} "
                "QAbstractItemView::drop-indicator {background:#55b7ff; height:4px;}")
            shape_list.setIconSize(QtCore.QSize(72, 72))
            shape_list.setGridSize(QtCore.QSize(112, 102))
            shape_list.model().rowsMoved.connect(
                lambda *args, category=category: self._save_organizer_order(category))
            shape_list.itemsDropped.connect(
                lambda item_ids, category=category: self._assign_items_to_category(
                    item_ids, category))
            self._organizer_lists.append(shape_list)
            self.organizer_tabs.addTab(shape_list, self._category_labels[category])
        organize_layout.addWidget(self.organizer_tabs, 1)
        organize_buttons = QtWidgets.QHBoxLayout()
        assign_button = QtWidgets.QPushButton("現在のタブへ追加")
        assign_button.clicked.connect(self._open_shape_picker)
        left_button = QtWidgets.QPushButton("← 左へ")
        left_button.clicked.connect(lambda: self._move_organizer_item(-1))
        right_button = QtWidgets.QPushButton("右へ →")
        right_button.clicked.connect(lambda: self._move_organizer_item(1))
        up_button = QtWidgets.QPushButton("↑ 上へ")
        up_button.clicked.connect(lambda: self._move_organizer_vertical(-1))
        down_button = QtWidgets.QPushButton("↓ 下へ")
        down_button.clicked.connect(lambda: self._move_organizer_vertical(1))
        remove_button = QtWidgets.QPushButton("削除")
        remove_button.clicked.connect(self._delete_organizer_item)
        organize_buttons.addWidget(assign_button, 1)
        organize_buttons.addWidget(left_button)
        organize_buttons.addWidget(right_button)
        organize_buttons.addWidget(up_button)
        organize_buttons.addWidget(down_button)
        organize_buttons.addWidget(remove_button, 1)
        organize_layout.addLayout(organize_buttons)
        library_tabs.addTab(organize, "整理")

        manage = QtWidgets.QWidget()
        manage_layout = QtWidgets.QVBoxLayout(manage)
        self.category_list = QtWidgets.QListWidget()
        self.category_list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.category_list.setDropIndicatorShown(True)
        self.category_list.model().rowsMoved.connect(self._category_rows_moved)
        manage_layout.addWidget(self.category_list, 1)
        category_buttons = QtWidgets.QHBoxLayout()
        for text, callback in (
                ("タブ追加", self._add_category_tab),
                ("名前変更", self._rename_category_tab),
                ("↑", lambda: self._move_category_tab(-1)),
                ("↓", lambda: self._move_category_tab(1)),
                ("削除", self._delete_category_tab)):
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(callback)
            category_buttons.addWidget(button)
        manage_layout.addLayout(category_buttons)
        history_buttons = QtWidgets.QHBoxLayout()
        undo_button = QtWidgets.QPushButton("元に戻す")
        undo_button.clicked.connect(self._undo_library_change)
        redo_button = QtWidgets.QPushButton("やり直す")
        redo_button.clicked.connect(self._redo_library_change)
        history_buttons.addWidget(undo_button)
        history_buttons.addWidget(redo_button)
        manage_layout.addLayout(history_buttons)
        library_tabs.addTab(manage, "タブ管理")
        self._refresh_category_list()
        self._refresh_library()
        return widget

    @staticmethod
    def _selection():
        return cmds.ls(selection=True, long=True, type="transform") or []

    def _run(self, callback):
        try:
            result = callback()
            self.status.setText("完了: {}".format(result or ""))
            return result
        except Exception as error:
            self.status.setText("エラー: " + str(error))
            cmds.warning(str(error))
            return None

    def _each(self, function):
        selected = self._selection()
        if not selected:
            return self._run(lambda: (_ for _ in ()).throw(ValueError("対象を選択してください")))
        def apply_all():
            results = [function(node) for node in selected]
            return "{}件処理しました".format(len(results))
        return self._run(apply_all)

    def _create_groups(self, function, name_part, position):
        name_part = name_part.strip()
        if not name_part:
            return self._run(lambda: (_ for _ in ()).throw(
                ValueError("グループ名を入力してください")))
        return self._each(lambda node: function(node, name_part, position))

    def _create_shape(self, shape):
        self._shape = shape
        self._create()

    def _create_item(self, item):
        if item.data(QtCore.Qt.UserRole + 1):
            self._create_library_shape(item.data(QtCore.Qt.UserRole))
        else:
            self._create_shape(item.data(QtCore.Qt.UserRole))
        QtCore.QTimer.singleShot(0, self._restore_viewport_focus)

    def _filter_shapes(self, text):
        query = text.strip().lower()
        for shape_list in self._shape_lists:
            for row in range(shape_list.count()):
                item = shape_list.item(row)
                key = str(item.data(QtCore.Qt.UserRole)).lower()
                item.setHidden(query not in item.text().lower() and query not in key)

    def _create(self):
        def create():
            controller = api.create_controller(
                self._shape, self.name_edit.text().strip() or "controller",
                self.size_spin.value(), self._creation_color)
            cmds.select(controller, replace=True)
            return "{} を作成しました".format(controller)
        self._run(create)

    def _create_text(self):
        text = self.text_edit.text()
        def create():
            controller = api.create_text_controller(
                text=text,
                name=self.name_edit.text().strip() or "controller",
                size=self.size_spin.value(),
                color=self._creation_color,
            )
            cmds.select(controller, replace=True)
            return "{} を作成しました".format(controller)
        self._run(create)
        QtCore.QTimer.singleShot(0, self._restore_viewport_focus)

    def _combine_selected(self):
        selected = self._selection()
        if len(selected) < 2:
            self._run(lambda: (_ for _ in ()).throw(ValueError(
                "統合するControllerを2つ以上選択してください")))
            return
        target = selected[-1]
        result = self._run(lambda: api.combine_controllers(
            selected, target=target, delete_sources=True))
        if result:
            cmds.select(result, replace=True)
        QtCore.QTimer.singleShot(0, self._restore_viewport_focus)

    @staticmethod
    def _model_panel():
        focused = cmds.getPanel(withFocus=True)
        if focused and cmds.getPanel(typeOf=focused) == "modelPanel":
            return focused
        for panel in cmds.getPanel(visiblePanels=True) or []:
            if cmds.getPanel(typeOf=panel) == "modelPanel":
                return panel
        panels = cmds.getPanel(type="modelPanel") or []
        return panels[0] if panels else None

    def _restore_viewport_focus(self):
        focused_widget = QtWidgets.QApplication.focusWidget()
        if focused_widget and self.isAncestorOf(focused_widget):
            focused_widget.clearFocus()
        panel = self._last_model_panel or self._model_panel()
        if panel:
            cmds.setFocus(panel)

    def _show_color_picker(self):
        if self._color_dialog and self._color_dialog.isVisible():
            self._color_dialog.raise_()
            self._color_dialog.activateWindow()
            return
        initial = self._creation_qcolor()
        self._pending_creation_color = None
        dialog = ColorPreviewDialog(initial, self)
        self._color_dialog = dialog
        dialog.colorPreviewed.connect(self._preview_creation_color)
        dialog.finished.connect(self._finish_creation_color_picker)
        dialog.place_next_to(self)
        dialog.show()

    def _creation_qcolor(self):
        if isinstance(self._creation_color, int):
            value = cmds.colorIndex(self._creation_color, query=True)[:3]
        else:
            value = self._creation_color
        return QtGui.QColor.fromRgbF(*value)

    def _preview_creation_color(self, color):
        self._pending_creation_color = (color.redF(), color.greenF(), color.blueF())
        self._update_color_button(color)

    def _finish_creation_color_picker(self, result):
        if result == QtWidgets.QDialog.Accepted and self._pending_creation_color is not None:
            self._creation_color = self._pending_creation_color
            self.status.setText("作成色を設定しました")
        self._pending_creation_color = None
        self._color_dialog = None
        self._update_color_button()
        QtCore.QTimer.singleShot(0, self._restore_viewport_focus)

    def _update_color_button(self, color=None):
        if not hasattr(self, "color_button"):
            return
        color = color or self._creation_qcolor()
        self.color_button.setStyleSheet(
            "QPushButton { border-left: 8px solid %s; }" % color.name())

    @staticmethod
    def _curve_shapes(node):
        shapes = cmds.listRelatives(
            node, shapes=True, noIntermediate=True, fullPath=True) or []
        return [shape for shape in shapes if cmds.nodeType(shape) == "nurbsCurve"]

    @staticmethod
    def _capture_color(shape):
        rgb = cmds.getAttr(shape + ".overrideColorRGB")
        rgb = rgb[0] if isinstance(rgb, list) else rgb
        return (cmds.getAttr(shape + ".overrideEnabled"),
                cmds.getAttr(shape + ".overrideRGBColors"),
                cmds.getAttr(shape + ".overrideColor"), tuple(rgb))

    def _preview_color(self, color):
        rgb = (color.redF(), color.greenF(), color.blueF())
        for shape in self._color_targets:
            if not cmds.objExists(shape):
                continue
            cmds.setAttr(shape + ".overrideEnabled", True)
            cmds.setAttr(shape + ".overrideRGBColors", True)
            cmds.setAttr(shape + ".overrideColorRGB", *rgb)

    def _retarget_color_preview(self):
        if not self._color_dialog or not self._color_dialog.isVisible():
            return
        nodes = self._selection()
        shapes = [shape for node in nodes for shape in self._curve_shapes(node)
                  if not cmds.referenceQuery(shape, isNodeReferenced=True)]
        if not shapes or shapes == self._color_targets:
            return
        self._restore_original_colors()
        self._color_original = {shape: self._capture_color(shape) for shape in shapes}
        self._color_targets = shapes
        self._preview_color(self._color_dialog.picker.currentColor())

    def _restore_original_colors(self):
        for shape, state in self._color_original.items():
            if not cmds.objExists(shape):
                continue
            enabled, use_rgb, index, rgb = state
            cmds.setAttr(shape + ".overrideEnabled", enabled)
            cmds.setAttr(shape + ".overrideRGBColors", use_rgb)
            cmds.setAttr(shape + ".overrideColor", index)
            cmds.setAttr(shape + ".overrideColorRGB", *rgb)

    def _finish_color_picker(self, result):
        if result != QtWidgets.QDialog.Accepted:
            self._restore_original_colors()
        if self._color_selection_job and cmds.scriptJob(exists=self._color_selection_job):
            cmds.scriptJob(kill=self._color_selection_job, force=True)
        self._color_selection_job = None
        self._close_color_undo()
        self._color_original = {}
        self._color_targets = []
        self._color_dialog = None
        QtCore.QTimer.singleShot(0, self._restore_viewport_focus)

    def _close_color_undo(self):
        if self._color_undo_open:
            cmds.undoInfo(closeChunk=True)
            self._color_undo_open = False

    @staticmethod
    def _display_color(node):
        curves = MainWindow._curve_shapes(node)
        if not curves:
            return QtGui.QColor("white")
        shape = curves[0]
        if cmds.getAttr(shape + ".overrideEnabled"):
            if cmds.getAttr(shape + ".overrideRGBColors"):
                value = cmds.getAttr(shape + ".overrideColorRGB")[0]
            else:
                value = cmds.colorIndex(
                    cmds.getAttr(shape + ".overrideColor"), query=True)[:3]
            return QtGui.QColor.fromRgbF(*[max(0.0, min(1.0, axis)) for axis in value])
        return QtGui.QColor("white")

    def _snap(self):
        selected = self._selection()
        self._run(lambda: api.snap_to(selected[0], selected[-1]) if len(selected) >= 2 else
                  (_ for _ in ()).throw(ValueError("コントローラー、スナップ先の順に選択してください")))

    def _refresh_library(self):
        if self._library_list is None:
            return
        current_item = self._library_list.currentItem()
        current = current_item.data(QtCore.Qt.UserRole) if current_item else ""
        self._library_list.clear()
        from ..core.library import load
        shapes = load(self._library_path)
        self._updating_shapes = True
        for name in api.library_shapes(self._library_path):
            item = QtWidgets.QListWidgetItem(
                shape_icon(shapes[name], apply_orientation=True), name)
            item.setData(QtCore.Qt.UserRole, name)
            item.setToolTip("{} を作成".format(name))
            self._library_list.addItem(item)
            if name == current:
                self._library_list.setCurrentItem(item)
        for shape_list in self._shape_lists:
            shape_list.clear()
        for category, shape_list in zip(self._shape_categories, self._shape_lists):
            hidden = set(api.library_hidden_items(category, self._library_path))
            entries = [("builtin:" + key, key, data, False)
                       for key, data in SHAPES.items()
                       if api.library_item_category(
                           "builtin:" + key, data.get("category"),
                           self._library_path) == category]
            entries.extend(("custom:" + name, name, shapes[name], True)
                           for name in api.library_shapes(self._library_path)
                           if api.library_item_category(
                               "custom:" + name,
                               shapes[name].get("category", "Panel"),
                               self._library_path) == category)
            for item_id, key, data, custom in entries:
                if item_id in hidden:
                    continue
                preset = QtWidgets.QListWidgetItem(
                    shape_icon(data, apply_orientation=custom),
                    data.get("label", key))
                preset.setData(QtCore.Qt.UserRole, key)
                preset.setData(QtCore.Qt.UserRole + 1, custom)
                preset.setData(QtCore.Qt.UserRole + 2, item_id)
                shape_list.addItem(preset)
        for category, shape_list in zip(self._shape_categories, self._shape_lists):
            self._apply_tab_order(category, shape_list)
        self._refresh_organizer()
        self._updating_shapes = False
        filename = os.path.basename(self._library_path)
        self.library_file_label.setText("使用中: {}（選択のみ）".format(filename))
        self.library_file_label.setToolTip(self._library_path)

    def _apply_tab_order(self, category, shape_list):
        saved = api.library_tab_order(category, self._library_path)
        if not saved:
            return
        items = [shape_list.takeItem(0) for _ in range(shape_list.count())]
        by_id = {item.data(QtCore.Qt.UserRole + 2): item for item in items}
        ordered = [by_id.pop(item_id) for item_id in saved if item_id in by_id]
        ordered.extend(item for item in items if item in by_id.values())
        for item in ordered:
            shape_list.addItem(item)

    def _save_tab_order(self, category):
        if self._updating_shapes:
            return
        shape_list = self._shape_lists[self._shape_categories.index(category)]
        item_ids = [shape_list.item(row).data(QtCore.Qt.UserRole + 2)
                    for row in range(shape_list.count())]
        self._run(lambda: api.set_library_tab_order(
            category, item_ids, self._library_path))

    def _refresh_organizer(self):
        if not self._organizer_lists:
            return
        for source, target in zip(self._shape_lists, self._organizer_lists):
            target.clear()
            for row in range(source.count()):
                original = source.item(row)
                item = QtWidgets.QListWidgetItem(original.icon(), original.text())
                for role in (QtCore.Qt.UserRole, QtCore.Qt.UserRole + 1,
                             QtCore.Qt.UserRole + 2):
                    item.setData(role, original.data(role))
                target.addItem(item)
        self._refresh_organizer_add_combo()

    def _refresh_organizer_add_combo(self):
        if not hasattr(self, "organizer_add_combo"):
            return
        category, shape_list = self._active_organizer()
        present = {shape_list.item(row).data(QtCore.Qt.UserRole + 2)
                   for row in range(shape_list.count())}
        self.organizer_add_combo.clear()
        from ..core.library import load
        shapes = load(self._library_path)
        for name in api.library_shapes(self._library_path):
            item_id = "custom:" + name
            if item_id not in present:
                self.organizer_add_combo.addItem(name, item_id)
        for item_id in api.library_hidden_items(category, self._library_path):
            if item_id.startswith("builtin:"):
                key = item_id.split(":", 1)[1]
                if key in SHAPES:
                    self.organizer_add_combo.addItem(
                        SHAPES[key].get("label", key), item_id)

    def _save_organizer_order(self, category):
        if self._updating_shapes:
            return
        index = self._shape_categories.index(category)
        shape_list = self._organizer_lists[index]
        item_ids = [shape_list.item(row).data(QtCore.Qt.UserRole + 2)
                    for row in range(shape_list.count())]
        self._record_library_state()
        if self._run(lambda: api.set_library_tab_order(
                category, item_ids, self._library_path)):
            self._updating_shapes = True
            self._apply_tab_order(category, self._shape_lists[index])
            self._updating_shapes = False

    def _active_organizer(self):
        index = self.organizer_tabs.currentIndex()
        return self._shape_categories[index], self._organizer_lists[index]

    def _open_shape_picker(self):
        from ..core.library import load
        shapes = load(self._library_path)
        entries = []
        for key, data in SHAPES.items():
            item_id = "builtin:" + key
            category = api.library_item_category(
                item_id, data.get("category"), self._library_path)
            entries.append((item_id, data.get("label", key),
                            shape_icon(data), category))
        for name in api.library_shapes(self._library_path):
            data = shapes[name]
            item_id = "custom:" + name
            category = api.library_item_category(
                item_id, data.get("category", "Panel"), self._library_path)
            entries.append((item_id, name,
                            shape_icon(data, apply_orientation=True), category))
        picker = ShapePicker(
            entries, api.library_categories(self._library_path), self)
        picker.itemsChosen.connect(self._picker_items_chosen)
        picker.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self._shape_picker = picker
        picker.show()

    def _picker_items_chosen(self, item_ids):
        category, _shape_list = self._active_organizer()
        self._assign_items_to_category(item_ids, category)

    def _assign_items_to_category(self, item_ids, category):
        def assign_all():
            for item_id in item_ids:
                api.assign_library_item(item_id, category, self._library_path)
                api.set_library_item_hidden(
                    category, item_id, False, self._library_path)
            return "{}件追加しました".format(len(item_ids))
        self._record_library_state()
        if self._run(assign_all):
            self._refresh_library()

    def _assign_library_item_to_tab(self):
        selected_names = [item.data(QtCore.Qt.UserRole)
                          for item in self._library_list.selectedItems()]
        combo_id = self.organizer_add_combo.currentData()
        item_ids = (["custom:" + name for name in selected_names]
                    if len(selected_names) > 1 else
                    ([combo_id] if combo_id else
                     (["custom:" + selected_names[0]] if selected_names else [])))
        if not item_ids:
            return self._run(lambda: (_ for _ in ()).throw(
                ValueError("追加できるシェイプがありません")))
        category, _shape_list = self._active_organizer()
        def assign_all():
            for item_id in item_ids:
                if item_id.startswith("custom:"):
                    self._assign_custom_to_category(
                        item_id.split(":", 1)[1], category)
                else:
                    api.set_library_item_hidden(
                        category, item_id, False, self._library_path)
            return "{}件追加しました".format(len(item_ids))
        if self._run(assign_all):
            self._refresh_library()

    def _assign_custom_to_category(self, name, category):
        api.set_library_category(name, category, self._library_path)
        return api.set_library_item_hidden(
            category, "custom:" + name, False, self._library_path)

    def _move_organizer_item(self, offset):
        category, shape_list = self._active_organizer()
        row = shape_list.currentRow()
        target = max(0, min(shape_list.count() - 1, row + int(offset)))
        if row < 0 or row == target:
            return
        self._updating_shapes = True
        item = shape_list.takeItem(row)
        shape_list.insertItem(target, item)
        shape_list.setCurrentItem(item)
        self._updating_shapes = False
        self._save_organizer_order(category)

    def _move_organizer_vertical(self, direction):
        _category, shape_list = self._active_organizer()
        columns = max(1, shape_list.viewport().width() //
                      max(1, shape_list.gridSize().width()))
        self._move_organizer_item(int(direction) * columns)

    def _delete_organizer_item(self):
        return self._hide_organizer_item()

    def _hide_organizer_item(self):
        category, shape_list = self._active_organizer()
        items = shape_list.selectedItems()
        if not items:
            return self._run(lambda: (_ for _ in ()).throw(
                ValueError("タブから外すシェイプを選択してください")))
        item_ids = [item.data(QtCore.Qt.UserRole + 2) for item in items]
        def remove_all():
            for item_id in item_ids:
                api.set_library_item_hidden(
                    category, item_id, True, self._library_path)
            return "{}件タブから削除しました".format(len(item_ids))
        self._record_library_state()
        if self._run(remove_all):
            self._refresh_library()

    def _restore_organizer_item(self):
        category, _shape_list = self._active_organizer()
        hidden = api.library_hidden_items(category, self._library_path)
        if not hidden:
            return self._run(lambda: (_ for _ in ()).throw(
                ValueError("追加できる非表示シェイプがありません")))
        labels = [item_id.split(":", 1)[-1] for item_id in hidden]
        label, accepted = QtWidgets.QInputDialog.getItem(
            self, "シェイプを追加", "追加するシェイプ", labels, 0, False)
        if accepted:
            item_id = hidden[labels.index(label)]
            if self._run(lambda: api.set_library_item_hidden(
                    category, item_id, False, self._library_path)):
                self._refresh_library()

    def _outer_tab_changed(self, index):
        if index != 2:
            return
        selected = self._selection()
        if selected:
            name = selected[0].rsplit("|", 1)[-1].rsplit(":", 1)[-1]
            self.library_name_edit.setText(name)

    def _add_category_tab(self):
        label, accepted = QtWidgets.QInputDialog.getText(
            self, "タブ追加", "新しいタブ名")
        if not accepted or not label.strip():
            return
        self._record_library_state()
        key = self._run(lambda: api.add_library_category(
            label.strip(), self._library_path))
        if not key:
            return
        self._shape_categories.append(key)
        self._category_labels[key] = label.strip()
        self.library_category_combo.addItem(label.strip(), key)
        self._append_category_widgets(key, label.strip())
        self._refresh_category_list(key)
        self._refresh_library()

    def _append_category_widgets(self, category, label):
        create_list = QtWidgets.QListWidget()
        create_list.setViewMode(QtWidgets.QListView.IconMode)
        create_list.setResizeMode(QtWidgets.QListView.Adjust)
        create_list.setMovement(QtWidgets.QListView.Snap)
        create_list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        create_list.setDragEnabled(True)
        create_list.setAcceptDrops(True)
        create_list.setDropIndicatorShown(True)
        create_list.setIconSize(QtCore.QSize(72, 72))
        create_list.setGridSize(QtCore.QSize(112, 102))
        create_list.setFocusPolicy(QtCore.Qt.NoFocus)
        create_list.itemClicked.connect(self._create_item)
        create_list.model().rowsMoved.connect(
            lambda *args, category=category: self._save_tab_order(category))
        self._shape_lists.append(create_list)
        self.shape_tabs.addTab(create_list, label)

        organize_list = OrganizerList()
        organize_list.setViewMode(QtWidgets.QListView.IconMode)
        organize_list.setResizeMode(QtWidgets.QListView.Adjust)
        organize_list.setMovement(QtWidgets.QListView.Snap)
        organize_list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        organize_list.setDragEnabled(True)
        organize_list.setAcceptDrops(True)
        organize_list.setDropIndicatorShown(True)
        organize_list.setStyleSheet(
            "QListWidget::item:selected {background:#3f647d;} "
            "QAbstractItemView::drop-indicator {background:#55b7ff; height:4px;}")
        organize_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        organize_list.setIconSize(QtCore.QSize(72, 72))
        organize_list.setGridSize(QtCore.QSize(112, 102))
        organize_list.model().rowsMoved.connect(
            lambda *args, category=category: self._save_organizer_order(category))
        organize_list.itemsDropped.connect(
            lambda item_ids, category=category: self._assign_items_to_category(
                item_ids, category))
        self._organizer_lists.append(organize_list)
        self.organizer_tabs.addTab(organize_list, label)

    def _rename_category_tab(self):
        item = self.category_list.currentItem()
        key = item.data(QtCore.Qt.UserRole) if item else None
        if not key:
            return
        old_label = self._category_labels[key]
        label, accepted = QtWidgets.QInputDialog.getText(
            self, "タブ名変更", "新しいタブ名", text=old_label)
        if not accepted or not label.strip():
            return
        self._record_library_state()
        if self._run(lambda: api.rename_library_category(
                key, label.strip(), self._library_path)):
            self._category_labels[key] = label.strip()
            index = self._shape_categories.index(key)
            self.shape_tabs.setTabText(index, label.strip())
            self.organizer_tabs.setTabText(index, label.strip())
            combo_index = self.library_category_combo.findData(key)
            self.library_category_combo.setItemText(combo_index, label.strip())
            self._refresh_category_list(key)

    def _record_library_state(self):
        path = Path(self._library_path)
        self._library_undo.append(path.read_text(encoding="utf-8")
                                  if path.exists() else "")
        self._library_redo.clear()

    def _restore_library_state(self, content):
        path = Path(self._library_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self._sync_category_widgets()
        self._refresh_library()

    def _undo_library_change(self):
        if not self._library_undo:
            return
        path = Path(self._library_path)
        self._library_redo.append(path.read_text(encoding="utf-8"))
        self._restore_library_state(self._library_undo.pop())

    def _redo_library_change(self):
        if not self._library_redo:
            return
        path = Path(self._library_path)
        self._library_undo.append(path.read_text(encoding="utf-8"))
        self._restore_library_state(self._library_redo.pop())

    def _refresh_category_list(self, selected_key=None):
        if not hasattr(self, "category_list"):
            return
        self._updating_categories = True
        self.category_list.clear()
        for record in api.library_categories(self._library_path):
            item = QtWidgets.QListWidgetItem(record["label"])
            item.setData(QtCore.Qt.UserRole, record["key"])
            self.category_list.addItem(item)
            if record["key"] == selected_key:
                self.category_list.setCurrentItem(item)
        self._updating_categories = False

    def _category_rows_moved(self, *args):
        if self._updating_categories:
            return
        records = api.library_categories(self._library_path)
        desired = [self.category_list.item(row).data(QtCore.Qt.UserRole)
                   for row in range(self.category_list.count())]
        self._record_library_state()
        current = [item["key"] for item in records]
        for target, key in enumerate(desired):
            old = current.index(key)
            if old != target:
                api.move_library_category(key, target - old, self._library_path)
                current.insert(target, current.pop(old))
        self._sync_category_widgets()

    def _move_category_tab(self, offset):
        item = self.category_list.currentItem()
        if not item:
            return
        key = item.data(QtCore.Qt.UserRole)
        self._record_library_state()
        api.move_library_category(key, offset, self._library_path)
        self._sync_category_widgets(key)

    def _delete_category_tab(self):
        item = self.category_list.currentItem()
        if not item:
            return
        key = item.data(QtCore.Qt.UserRole)
        answer = QtWidgets.QMessageBox.question(
            self, "タブ削除", "{} タブを削除しますか？".format(item.text()))
        if answer == QtWidgets.QMessageBox.Yes:
            self._record_library_state()
            if self._run(lambda: api.remove_library_category(
                    key, self._library_path)):
                self._sync_category_widgets()
                self._refresh_library()

    def _sync_category_widgets(self, selected_key=None):
        records = api.library_categories(self._library_path)
        new_keys = [item["key"] for item in records]
        old_create = dict(zip(self._shape_categories, self._shape_lists))
        old_organize = dict(zip(self._shape_categories, self._organizer_lists))
        for record in records:
            if record["key"] not in old_create:
                self._shape_categories.append(record["key"])
                self._category_labels[record["key"]] = record["label"]
                self._append_category_widgets(record["key"], record["label"])
                old_create[record["key"]] = self._shape_lists[-1]
                old_organize[record["key"]] = self._organizer_lists[-1]
        while self.shape_tabs.count():
            self.shape_tabs.removeTab(0)
        while self.organizer_tabs.count():
            self.organizer_tabs.removeTab(0)
        self._shape_categories = new_keys
        self._category_labels = {item["key"]: item["label"] for item in records}
        self._shape_lists = [old_create[key] for key in new_keys]
        self._organizer_lists = [old_organize[key] for key in new_keys]
        for key, create_list, organize_list in zip(
                new_keys, self._shape_lists, self._organizer_lists):
            label = self._category_labels[key]
            self.shape_tabs.addTab(create_list, label)
            self.organizer_tabs.addTab(organize_list, label)
        current_combo = self.library_category_combo.currentData()
        self.library_category_combo.clear()
        for key in new_keys:
            self.library_category_combo.addItem(self._category_labels[key], key)
        index = self.library_category_combo.findData(current_combo)
        if index >= 0:
            self.library_category_combo.setCurrentIndex(index)
        self._refresh_category_list(selected_key)

    def _library_item_changed(self, current, previous):
        if not current:
            return
        from ..core.library import load
        name = current.data(QtCore.Qt.UserRole)
        data = load(self._library_path).get(name, {})
        index = self.library_category_combo.findData(data.get("category", "Panel"))
        if index >= 0:
            self.library_category_combo.setCurrentIndex(index)
        self.library_name_edit.setText(name)

    def _change_library_category(self):
        item = self._library_list.currentItem()
        if not item:
            return self._run(lambda: (_ for _ in ()).throw(
                ValueError("変更するプリセットを選択してください")))
        name = item.data(QtCore.Qt.UserRole)
        category = self.library_category_combo.currentData()
        if self._run(lambda: api.set_library_category(
                name, category, self._library_path)):
            self._refresh_library()
            self._select_library_name(name)

    def _save_library_shape(self):
        selected = self._selection()
        if not selected:
            self._run(lambda: (_ for _ in ()).throw(ValueError("登録するControllerを選択してください")))
            return
        name = self.library_name_edit.text().strip()
        if not name:
            name = selected[0].rsplit("|", 1)[-1].rsplit(":", 1)[-1]
            self.library_name_edit.setText(name)
        self._record_library_state()
        if self._run(lambda: api.save_to_library(
                selected[0], name, self._library_path,
                self.library_category_combo.currentData())):
            self._refresh_library()
            self._select_library_name(name)

    def _create_library_item(self, item):
        self._create_library_shape(item.data(QtCore.Qt.UserRole))

    def _create_library_shape(self, name=None):
        item = self._library_list.currentItem()
        name = name or (item.data(QtCore.Qt.UserRole) if item else "")
        if not name:
            self._run(lambda: (_ for _ in ()).throw(ValueError("保存済みシェイプがありません")))
            return
        controller = self._run(lambda: api.create_from_library(
            name, self.name_edit.text().strip() or "controller",
            self.size_spin.value(), self._creation_color,
            self._library_path))
        if controller:
            cmds.select(controller, replace=True)
            QtCore.QTimer.singleShot(0, self._restore_viewport_focus)

    def _select_library_name(self, name):
        for row in range(self._library_list.count()):
            item = self._library_list.item(row)
            if item.data(QtCore.Qt.UserRole) == name:
                self._library_list.setCurrentItem(item)
                return

    def _move_library_shape(self, offset):
        item = self._library_list.currentItem()
        if not item:
            return
        name = item.data(QtCore.Qt.UserRole)
        from ..core.library import load
        category = load(self._library_path)[name].get("category", "Panel")
        shape_list = self._shape_lists[self._shape_categories.index(category)]
        source_row = next((row for row in range(shape_list.count())
                           if shape_list.item(row).data(QtCore.Qt.UserRole + 2)
                           == "custom:" + name), -1)
        target_row = max(0, min(shape_list.count() - 1, source_row + int(offset)))
        if source_row >= 0 and source_row != target_row:
            self._updating_shapes = True
            moved = shape_list.takeItem(source_row)
            shape_list.insertItem(target_row, moved)
            shape_list.setCurrentItem(moved)
            self._updating_shapes = False
            self._save_tab_order(category)
            api.move_library_shape(name, offset, self._library_path)
            self._refresh_library()
        self._select_library_name(name)

    def _remove_library_shape(self):
        names = [item.data(QtCore.Qt.UserRole)
                 for item in self._library_list.selectedItems()]
        if not names:
            return
        answer = QtWidgets.QMessageBox.question(
            self, "ライブラリから削除",
            "{}件のプリセットを削除しますか？".format(len(names)))
        if answer == QtWidgets.QMessageBox.Yes:
            self._record_library_state()
            def remove_all():
                for name in names:
                    api.remove_from_library(name, self._library_path)
                return "{}件削除しました".format(len(names))
            self._run(remove_all)
            self._refresh_library()


def show():
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if widget.objectName() == MainWindow.OBJECT_NAME:
            widget.close()
            widget.deleteLater()
    window = MainWindow()
    window.show()
    return window
