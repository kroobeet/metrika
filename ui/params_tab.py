"""Вкладка для настройки параметров отчёта."""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Tuple

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QRadioButton, QButtonGroup, QDateEdit, QLabel,
                               QComboBox, QCheckBox, QLineEdit, QMessageBox)
from PySide6.QtCore import QDate
from core.models import ReportParams, Location


@dataclass
class ParamsTabConfig:
    """Конфигурация для вкладки параметров."""
    period_group_title: str = "Быстрый выбор периода"
    date_group_title: str = "Ручная настройка периода"
    counter_label: str = "ID Счётчика:"
    grouping_label: str = "Группировка:"
    traffic_group_title: str = "Источники трафика"
    behavior_group_title: str = "Тип трафика"
    date_from_label: str = "От:"
    date_to_label: str = "По:"
    quick_periods: List[Tuple[str, int]] = field(
        default_factory=lambda: [
            ("Сегодня", 0),
            ("Вчера", 1),
            ("Неделя", 7),
            ("Месяц", 30),
            ("Предыдущий месяц", 2),
            ("Квартал", 90),
            ("Год", 365)
        ]
    )
    default_period: str = "Месяц"
    grouping_options: List[str] = field(default_factory=lambda: ["По дням"])
    traffic_sources: Dict[str, str] = field(
        default_factory=lambda: {
            "search": "Поисковые системы",
            "direct": "Прямые заходы",
            "ad": "Реклама",
            "internal": "Внутренние переходы",
            "referral": "Переходы по ссылкам",
            "recommendation": "Рекомендации",
            "social": "Социальные сети"
        }
    )
    behavior_options: Dict[int, Tuple[str, str]] = field(
        default_factory=lambda: {
            0: ("Все посетители", "all"),
            1: ("Только люди", "human"),
            2: ("Только роботы", "robot")
        }
    )


class ParamsTab(QWidget):
    """Виджет для настройки параметров отчёта."""

    def __init__(self, config: Optional[ParamsTabConfig] = None):
        super().__init__()
        self.ui_config = config or ParamsTabConfig()
        self._init_ui()

    def _init_ui(self) -> None:
        """Инициализация компонентов пользовательского интерфейса"""
        layout = QVBoxLayout()

        # Быстрый выбор периода
        period_group = QGroupBox(self.ui_config.period_group_title)
        period_layout = QHBoxLayout()

        self.period_btns = QButtonGroup()
        for text, days in self.ui_config.quick_periods:
            btn = QRadioButton(text)
            if text == self.ui_config.default_period:
                btn.setChecked(True)
            self.period_btns.addButton(btn, days)
            period_layout.addWidget(btn)

        period_group.setLayout(period_layout)
        layout.addWidget(period_group)

        # Ручная настройка периода
        date_group = QGroupBox(self.ui_config.date_group_title)
        date_layout = QHBoxLayout()

        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_to = QDateEdit(QDate.currentDate())

        date_layout.addWidget(QLabel(self.ui_config.date_from_label))
        date_layout.addWidget(self.date_from)
        date_layout.addWidget(QLabel(self.ui_config.date_to_label))
        date_layout.addWidget(self.date_to)

        date_group.setLayout(date_layout)
        layout.addWidget(date_group)

        self.period_btns.buttonClicked.connect(self._update_dates)

        # ID счётчика
        counter_layout = QHBoxLayout()
        counter_layout.addWidget(QLabel(self.ui_config.counter_label))
        self.counter_input = QLineEdit()
        counter_layout.addWidget(self.counter_input)
        layout.addLayout(counter_layout)

        # Группировка
        group_layout = QHBoxLayout()
        group_layout.addWidget(QLabel(self.ui_config.grouping_label))
        self.group_combo = QComboBox()
        self.group_combo.addItems(self.ui_config.grouping_options)
        group_layout.addWidget(self.group_combo)
        layout.addLayout(group_layout)

        # Источника трафика
        traffic_group = QGroupBox(self.ui_config.traffic_group_title)
        traffic_layout = QHBoxLayout()

        self.traffic_checkboxes = {
            key: QCheckBox(label)
            for key, label in self.ui_config.traffic_sources.items()
        }

        for cb in self.traffic_checkboxes.values():
            cb.setChecked(True)
            traffic_layout.addWidget(cb)

        traffic_group.setLayout(traffic_layout)
        layout.addWidget(traffic_group)

        # Тип поведения трафика
        behavior_group = QGroupBox(self.ui_config.behavior_group_title)
        behavior_layout = QHBoxLayout()

        self.behavior_group = QButtonGroup()
        for btn_id, (text, _) in self.ui_config.behavior_options.items():
            btn = QRadioButton(text)
            if btn_id == 0:  # "Все посетители" по умолчанию
                btn.setChecked(True)
            self.behavior_group.addButton(btn, btn_id)
            behavior_layout.addWidget(btn)

        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)

        self.setLayout(layout)

    def _update_dates(self, btn: QRadioButton) -> None:
        """Обновляет диапазон дат на основе выбранного быстрого периода"""
        days = self.period_btns.id(btn)
        today = QDate.currentDate()

        if days == 0:  # Сегодня
            self.date_from.setDate(today)
            self.date_to.setDate(today)
        elif days == 1:  # Вчера
            self.date_from.setDate(today.addDays(-1))
            self.date_to.setDate(today.addDays(-1))
        elif days == 2:  # Предыдущий месяц
            current_date = QDate.currentDate()
            prev_month = 12 if current_date.month() == 1 else current_date.month() - 1
            prev_year = current_date.year() - 1 if current_date.month() == 1 else current_date.year()

            first_day = QDate(prev_year, prev_month, 1)
            last_day = QDate(prev_year, prev_month, first_day.daysInMonth())

            self.date_from.setDate(first_day)
            self.date_to.setDate(last_day)
        else:
            self.date_from.setDate(today.addDays(-days))
            self.date_to.setDate(today)

    def validate_input(self) -> bool:
        """Валидация пользовательского ввода."""
        errors = []

        if not self.counter_input.text().strip():
            errors.append("ID Счётчика является обязательным")

        if self.date_from.date() > self.date_to.date():
            errors.append("Начальная дата не может быть позднее конечной!")

        if not any(cb.isChecked() for cb in self.traffic_checkboxes.values()):
            errors.append("Хотя бы один источник трафика должен быть выбран!")

        if errors:
            QMessageBox.warning(self, "Ошибка валидации", "\n".join(errors))
            return False

        return True

    def get_report_params(self, locations: List[Location]) -> ReportParams:
        """Получает параметры отчёта из пользовательского интерфейса."""
        if not self.validate_input():
            raise ValueError("Некорректные параметры отчёта")

        behavior_id = self.behavior_group.checkedId()
        behavior = self.ui_config.behavior_options.get(behavior_id, ("all",))[1]

        # Явное преобразование в date
        date_from = self.date_from.date().toPython()
        date_to = self.date_to.date().toPython()

        if not isinstance(date_from, date) or not isinstance(date_to, date):
            raise TypeError("Ожидается объект даты")

        return ReportParams(
            date_from=date_from,
            date_to=date_to,
            counter_id=self.counter_input.text().strip(),
            grouping=self.group_combo.currentText(),
            traffic_sources={
                key: cb.isChecked()
                for key, cb in self.traffic_checkboxes.items()
            },
            behavior=behavior,
            locations=locations
        )
