# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import typing

import structlog
from PIL import Image, ImageQt
from PySide6.QtCore import QMetaObject, QSize, QStringListModel, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.library.alchemy.enums import SortingModeEnum
from tagstudio.qt.controllers.preview_panel_controller import PreviewPanel
from tagstudio.qt.helpers.color_overlay import theme_fg_overlay
from tagstudio.qt.mixed.landing import LandingWidget
from tagstudio.qt.mixed.pagination import Pagination
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.thumb_grid_layout import ThumbGridLayout
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.main_menu_bar import MainMenuBar

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


logger = structlog.get_logger(__name__)


# View Component
class MainWindow(QMainWindow):
    THUMB_SIZES: list[tuple[str, int]] = [
        (Translations["home.thumbnail_size.extra_large"], 256),
        (Translations["home.thumbnail_size.large"], 192),
        (Translations["home.thumbnail_size.medium"], 128),
        (Translations["home.thumbnail_size.small"], 96),
        (Translations["home.thumbnail_size.mini"], 76),
    ]

    def __init__(self, driver: "QtDriver", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.rm = ResourceManager()

        # region Type declarations for variables that will be initialized in methods
        # initialized in setup_search_bar
        self.search_bar_layout: QHBoxLayout
        self.back_button: QPushButton
        self.forward_button: QPushButton
        self.search_field: QLineEdit
        self.search_field_completion_list: QStringListModel
        self.search_field_completer: QCompleter
        self.search_button: QPushButton

        # initialized in setup_extra_input_bar
        self.extra_input_layout: QHBoxLayout
        self.sorting_mode_combobox: QComboBox
        self.sorting_direction_combobox: QComboBox
        self.thumb_size_combobox: QComboBox

        # initialized in setup_content
        self.content_layout: QHBoxLayout
        self.content_splitter: QSplitter

        # initialized in setup_entry_list
        self.entry_list_container: QWidget
        self.entry_list_layout: QVBoxLayout
        self.entry_scroll_area: QScrollArea
        self.thumb_grid: QWidget
        self.thumb_layout: ThumbGridLayout
        self.landing_widget: LandingWidget
        self.pagination: Pagination

        # initialized in setup_preview_panel
        self.preview_panel: PreviewPanel
        # endregion

        if not self.objectName():
            self.setObjectName("MainWindow")
        self.resize(1316, 740)

        self.setup_menu_bar()

        self.setup_central_widget(driver)

        self.setup_status_bar()

        QMetaObject.connectSlotsByName(self)

        # NOTE: These are old attempts to allow for a translucent/acrylic
        # window effect. This may be attempted again in the future.
        # self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        # self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, False)
        # # self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # self.windowFX = WindowEffect()
        # self.windowFX.setAcrylicEffect(self.winId(), isEnableShadow=False)

    # region UI Setup Methods

    # region Menu Bar

    def setup_menu_bar(self):
        self.menu_bar = MainMenuBar(self)

        self.setMenuBar(self.menu_bar)
        self.menu_bar.setNativeMenuBar(True)

    # endregion

    def setup_central_widget(self, driver: "QtDriver"):
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("central_widget")
        self.central_layout = QGridLayout(self.central_widget)
        self.central_layout.setObjectName("central_layout")

        self.setup_search_bar()
        self.setup_extra_input_bar()
        self.setup_content(driver)
        self.setCentralWidget(self.central_widget)

    def setup_search_bar(self):
        """Sets up Nav Buttons, Search Field, Search Button."""
        self.search_bar_layout = QHBoxLayout()
        self.search_bar_layout.setObjectName("search_bar_layout")
        self.search_bar_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self.back_button = QPushButton(self.central_widget)
        back_icon: Image.Image = self.rm.get("bxs-left-arrow")  # pyright: ignore[reportAssignmentType]
        back_icon = theme_fg_overlay(back_icon, use_alpha=False)
        self.back_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(back_icon)))
        self.back_button.setObjectName("back_button")
        self.back_button.setMinimumSize(QSize(32, 32))
        self.back_button.setMaximumSize(QSize(32, 16777215))
        self.search_bar_layout.addWidget(self.back_button)

        self.forward_button = QPushButton(self.central_widget)
        forward_icon: Image.Image = self.rm.get("bxs-right-arrow")  # pyright: ignore[reportAssignmentType]
        forward_icon = theme_fg_overlay(forward_icon, use_alpha=False)
        self.forward_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(forward_icon)))
        self.forward_button.setIconSize(QSize(16, 16))
        self.forward_button.setObjectName("forward_button")
        self.forward_button.setMinimumSize(QSize(32, 32))
        self.forward_button.setMaximumSize(QSize(32, 16777215))
        self.search_bar_layout.addWidget(self.forward_button)

        self.search_field = QLineEdit(self.central_widget)
        self.search_field.setPlaceholderText(Translations["home.search_entries"])
        self.search_field.setObjectName("search_field")
        self.search_field.setMinimumSize(QSize(0, 32))
        self.search_field_completion_list = QStringListModel()
        self.search_field_completer = QCompleter(
            self.search_field_completion_list, self.search_field
        )
        self.search_field_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.search_field.setCompleter(self.search_field_completer)
        self.search_bar_layout.addWidget(self.search_field)

        self.search_button = QPushButton(Translations["home.search"], self.central_widget)
        self.search_button.setObjectName("search_button")
        self.search_button.setMinimumSize(QSize(0, 32))
        self.search_bar_layout.addWidget(self.search_button)

        self.central_layout.addLayout(self.search_bar_layout, 3, 0, 1, 1)

    def setup_extra_input_bar(self):
        """Sets up inputs for sorting settings and thumbnail size."""
        self.extra_input_layout = QHBoxLayout()
        self.extra_input_layout.setObjectName("extra_input_layout")

        ## left side spacer
        self.extra_input_layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        ## Sorting Mode Dropdown
        self.sorting_mode_combobox = QComboBox(self.central_widget)
        self.sorting_mode_combobox.setObjectName("sorting_mode_combobox")
        for sort_mode in SortingModeEnum:
            self.sorting_mode_combobox.addItem(Translations[sort_mode.value], sort_mode)
        self.extra_input_layout.addWidget(self.sorting_mode_combobox)

        ## Sorting Direction Dropdown
        self.sorting_direction_combobox = QComboBox(self.central_widget)
        self.sorting_direction_combobox.setObjectName("sorting_direction_combobox")
        self.sorting_direction_combobox.addItem(
            Translations["sorting.direction.ascending"], userData=True
        )
        self.sorting_direction_combobox.addItem(
            Translations["sorting.direction.descending"], userData=False
        )
        self.sorting_direction_combobox.setCurrentIndex(1)  # Default: Descending
        self.extra_input_layout.addWidget(self.sorting_direction_combobox)

        ## Thumbnail Size placeholder
        self.thumb_size_combobox = QComboBox(self.central_widget)
        self.thumb_size_combobox.setObjectName("thumb_size_combobox")
        self.thumb_size_combobox.setPlaceholderText(Translations["home.thumbnail_size"])
        self.thumb_size_combobox.setCurrentText("")
        size_policy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.thumb_size_combobox.sizePolicy().hasHeightForWidth())
        self.thumb_size_combobox.setSizePolicy(size_policy)
        self.thumb_size_combobox.setMinimumWidth(128)
        self.thumb_size_combobox.setMaximumWidth(352)
        self.extra_input_layout.addWidget(self.thumb_size_combobox)
        for size in MainWindow.THUMB_SIZES:
            self.thumb_size_combobox.addItem(size[0], size[1])
        self.thumb_size_combobox.setCurrentIndex(2)  # Default: Medium

        self.central_layout.addLayout(self.extra_input_layout, 5, 0, 1, 1)

    def setup_content(self, driver: "QtDriver"):
        self.content_layout = QHBoxLayout()
        self.content_layout.setObjectName("content_layout")

        self.content_splitter = QSplitter()
        self.content_splitter.setObjectName("content_splitter")
        self.content_splitter.setHandleWidth(12)

        self.setup_entry_list(driver)
        self.setup_preview_panel(driver)

        self.content_splitter.setStretchFactor(0, 1)
        self.content_layout.addWidget(self.content_splitter)

        self.central_layout.addLayout(self.content_layout, 10, 0, 1, 1)

    def setup_entry_list(self, driver: "QtDriver"):
        self.entry_list_container = QWidget()
        self.entry_list_layout = QVBoxLayout(self.entry_list_container)
        self.entry_list_layout.setSpacing(0)

        self.entry_scroll_area = QScrollArea()
        self.entry_scroll_area.setObjectName("entry_scroll_area")
        self.entry_scroll_area.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.entry_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.entry_scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.entry_scroll_area.setWidgetResizable(True)
        self.entry_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.entry_scroll_area.verticalScrollBar().valueChanged.connect(
            lambda value: self.thumb_layout.update()
        )

        self.thumb_grid = QWidget()
        self.thumb_grid.setObjectName("thumb_grid")
        self.thumb_layout = ThumbGridLayout(driver, self.entry_scroll_area)
        self.thumb_layout.setSpacing(min(self.thumb_size // 10, 12))
        self.thumb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_grid.setLayout(self.thumb_layout)
        self.entry_scroll_area.setWidget(self.thumb_grid)

        self.entry_list_layout.addWidget(self.entry_scroll_area)

        self.landing_widget = LandingWidget(driver, self.devicePixelRatio())
        self.entry_list_layout.addWidget(self.landing_widget)

        self.pagination = Pagination()
        self.entry_list_layout.addWidget(self.pagination)
        self.content_splitter.addWidget(self.entry_list_container)

    def setup_preview_panel(self, driver: "QtDriver"):
        self.preview_panel = PreviewPanel(driver.lib, driver)
        self.content_splitter.addWidget(self.preview_panel)

    def setup_status_bar(self):
        self.status_bar = QStatusBar(self)
        self.status_bar.setObjectName("status_bar")
        status_bar_size_policy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        status_bar_size_policy.setHorizontalStretch(0)
        status_bar_size_policy.setVerticalStretch(0)
        status_bar_size_policy.setHeightForWidth(self.status_bar.sizePolicy().hasHeightForWidth())
        self.status_bar.setSizePolicy(status_bar_size_policy)
        self.status_bar.setSizeGripEnabled(False)
        self.setStatusBar(self.status_bar)

    # endregion

    def toggle_landing_page(self, enabled: bool):
        if enabled:
            self.entry_scroll_area.setHidden(True)
            self.landing_widget.setHidden(False)
            self.landing_widget.animate_logo_in()
        else:
            self.landing_widget.setHidden(True)
            self.landing_widget.set_status_label("")
            self.entry_scroll_area.setHidden(False)

    @property
    def sorting_mode(self) -> SortingModeEnum:
        """What to sort by."""
        return self.sorting_mode_combobox.currentData()

    @property
    def sorting_direction(self) -> bool:
        """Whether to Sort the results in ascending order."""
        return self.sorting_direction_combobox.currentData()

    @property
    def thumb_size(self) -> int:
        return self.thumb_size_combobox.currentData()
