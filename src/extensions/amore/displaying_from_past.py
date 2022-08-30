from qtpy.QtCore import QCoreApplication, QDate, QMetaObject, Signal
from qtpy.QtWidgets import (
    QDateTimeEdit, QFrame, QGridLayout, QLabel, QPushButton, QWidget)

MAXVAL = 2.5


class IntervalSettings(QWidget):
    selected_tool = Signal(object)

    def __init__(self):
        super().__init__()

        self.ui_min_time = 0
        self.ui_max_time = 0
        self.setup_ui(self)

    def setup_ui(self, RangeSlider):
        RangeSlider.setObjectName("RangeSlider")
        self.RangeBarVLayout = QGridLayout(RangeSlider)

        self.dates_layout = QGridLayout()
        self.dates_layout.setContentsMargins(5, 2, 5, 2)
        self.dates_layout.setObjectName("dates_layout")

        # start_time Calendar Widget
        start_time_label = QLabel('Start Date', self)
        self.ui_start_time = QDateTimeEdit()
        self.ui_start_time.setDate(QDate.currentDate().addDays(-MAXVAL*2))
        self.ui_start_time.setCalendarPopup(True)
        self.ui_start_time.setDisplayFormat("dd.MM.yyyy")
        self.ui_start_time.setObjectName("start_time")

        # end_time Calendar Widget
        end_time_label = QLabel('End Date', self)
        self.ui_end_time = QDateTimeEdit()
        self.ui_end_time.setDate(QDate.currentDate().addDays(1))
        self.ui_end_time.setCalendarPopup(True)
        self.ui_end_time.setDisplayFormat("dd.MM.yyyy")
        self.ui_end_time.setObjectName("end_time")

        # Add connections to calendar
        start_time_label.setBuddy(self.ui_start_time)
        self.dates_layout.addWidget(start_time_label, 0, 0)
        self.dates_layout.addWidget(self.ui_start_time, 0, 1)
        self.dates_layout.addWidget(end_time_label, 0, 2)
        self.dates_layout.addWidget(self.ui_end_time, 0, 3)
        self.ui_start_time.dateChanged.connect(self.get_start_date)
        self.ui_end_time.dateChanged.connect(self.get_end_date)

        # general information
        self.ui_buttons_frame = QFrame(RangeSlider)
        self.ui_buttons_layout = QGridLayout(self.ui_buttons_frame)
        self.ui_warning = QLabel(
            "Click the arrow icon to save the selected ROI, "
            "recent saved ROIs are marked in a different color.")
        self.ui_warning.setStyleSheet(
            "color: red; font-weight: bold; font-size: 30")

        self.ui_get_coordinates = QPushButton(
            "Display ROIS from interval")
        self.ui_get_last_coordinates = QPushButton(
            "Display last ROI sent to device")

        self.ui_buttons_layout.addWidget(self.ui_get_coordinates, 2, 4, 1, 2)
        self.ui_buttons_layout.addWidget(
            self.ui_get_last_coordinates, 2, 6, 1, 2)
        self.ui_buttons_layout.addWidget(start_time_label, 2, 0, 1, 1)
        self.ui_buttons_layout.addWidget(self.ui_start_time, 2, 1, 1, 1)
        self.ui_buttons_layout.addWidget(end_time_label, 2, 2, 1, 1)
        self.ui_buttons_layout.addWidget(self.ui_end_time, 2, 3, 1, 1)
        self.RangeBarVLayout.addWidget(self.ui_buttons_frame, 0, 0, 1, 2)
        self.retranslate_ui(RangeSlider)
        QMetaObject.connectSlotsByName(RangeSlider)

        self.show()

    def get_start_date(self):
        self.ui_min_time = self.ui_start_time.dateTime().toTime_t()

    def get_end_date(self):
        self.ui_max_time = self.ui_end_time.dateTime().toTime_t()

    def retranslate_ui(self, RangeSlider):
        _translate = QCoreApplication.translate
        RangeSlider.setWindowTitle(_translate("RangeSlider", "Time interval"))
