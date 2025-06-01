from typing import List
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QRadioButton, QButtonGroup, QDateEdit, QLabel,
                               QComboBox, QCheckBox, QLineEdit, QMessageBox)
from PySide6.QtCore import QDate
from core.models import ReportParams, Location


class ParamsTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        """Инициализация пользовательского интерфейса"""
        layout = QVBoxLayout()

        # Группа для быстрого выбора периода
        period_group = QGroupBox("Быстрый выбор периода")
        period_layout = QHBoxLayout()

        self.period_btns = QButtonGroup()
        periods = [
            ("Сегодня", 0),
            ("Вчера", 1),
            ("Неделя", 7),
            ("Месяц", 30),
            ("Прошлый месяц", 2),
            ("Квартал", 90),
            ("Год", 365)
        ]

        for text, days in periods:
            btn = QRadioButton(text)
            if text == "Месяц":
                btn.setChecked(True)
            self.period_btns.addButton(btn, days)
            period_layout.addWidget(btn)

        period_group.setLayout(period_layout)
        layout.addWidget(period_group)

        # Ручной ввод периода
        date_group = QGroupBox("Ручной выбор периода")
        date_layout = QHBoxLayout()

        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_to = QDateEdit(QDate.currentDate())

        date_layout.addWidget(QLabel("С:"))
        date_layout.addWidget(self.date_from)
        date_layout.addWidget(QLabel("По:"))
        date_layout.addWidget(self.date_to)
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)

        # Обработчик изменения периода
        self.period_btns.buttonClicked.connect(self._update_dates)

        # ID счётчика
        counter_layout = QHBoxLayout()
        counter_layout.addWidget(QLabel("ID счётчика:"))
        self.counter_input = QLineEdit()
        counter_layout.addWidget(self.counter_input)
        layout.addLayout(counter_layout)

        # Группировка
        group_layout = QHBoxLayout()
        group_layout.addWidget(QLabel("Группировка:"))
        self.group_combo = QComboBox()
        self.group_combo.addItems(["По дням", "По неделям", "По месяцам"])
        group_layout.addWidget(self.group_combo)
        layout.addLayout(group_layout)

        # Источники трафика
        traffic_group = QGroupBox("Источники трафика")
        traffic_layout = QHBoxLayout()

        self.traffic_sources = {
            "search": QCheckBox("Поисковые системы"),
            "direct": QCheckBox("Прямые заходы"),
            "ad": QCheckBox("Реклама"),
            "internal": QCheckBox("Внутренние переходы"),
            "referral": QCheckBox("Ссылки на сайтах"),
            "recommendation": QCheckBox("Рекомендательные системы"),
            "social": QCheckBox("Социальные сети"),
        }

        for cb in self.traffic_sources.values():
            cb.setChecked(True)
            traffic_layout.addWidget(cb)

        traffic_group.setLayout(traffic_layout)
        layout.addWidget(traffic_group)

        # Тип трафика
        behavior_group = QGroupBox("Тип трафика")
        behavior_layout = QHBoxLayout()

        self.behavior_group = QButtonGroup()
        self.behavior_all = QRadioButton("Все посетители")
        self.behavior_human = QRadioButton("Только люди")
        self.behavior_robot = QRadioButton("Только роботы")

        self.behavior_all.setChecked(True)
        self.behavior_group.addButton(self.behavior_all, 0)
        self.behavior_group.addButton(self.behavior_human, 1)
        self.behavior_group.addButton(self.behavior_robot, 2)

        behavior_layout.addWidget(self.behavior_all)
        behavior_layout.addWidget(self.behavior_human)
        behavior_layout.addWidget(self.behavior_robot)
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)

        self.setLayout(layout)

    def _update_dates(self, btn):
        """Обновление дат при выборе быстрого периода"""
        days = self.period_btns.id(btn)
        today = QDate.currentDate()

        if days == 0:  # Сегодня
            self.date_from.setDate(today)
            self.date_to.setDate(today)
        elif days == 1:  # Вчера
            self.date_from.setDate(today.addDays(-1))
            self.date_to.setDate(today.addDays(-1))
        elif days == 2:  # Прошлый месяц
            current_date = QDate.currentDate()
            # Получаем текущий месяц и год
            current_month = current_date.month()
            current_year = current_date.year()

            # Вычисляем предыдущий месяц и год
            if current_month == 1:
                prev_month = 12
                prev_year = current_year - 1
            else:
                prev_month = current_month - 1
                prev_year = current_year

            # Первый день предыдущего месяца
            first_day_prev = QDate(prev_year, prev_month, 1)

            # Последний день предыдущего месяца
            last_day_prev = QDate(prev_year, prev_month, first_day_prev.daysInMonth())

            self.date_from.setDate(first_day_prev)
            self.date_to.setDate(last_day_prev)
        else:
            self.date_from.setDate(today.addDays(-days))
            self.date_to.setDate(today)

    def validate_input(self) -> bool:
        """Проверка валидности введенных данных"""
        # Проверка ID счетчика
        if not self.counter_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите ID счетчика")
            return False

        # Проверка дат
        date_from = self.date_from.date().toPython()
        date_to = self.date_to.date().toPython()
        if date_from > date_to:
            QMessageBox.warning(self, "Ошибка", "Дата 'C' не может быть позже даты 'По'!")
            return False

        # Проверка выбора источников трафика
        if not any(cb.isChecked() for cb in self.traffic_sources.values()):
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы один источник трафика")
            return False

        return True

    def get_report_params(self, locations: List[Location]) -> ReportParams:
        """Получение параметров отчета с проверкой валидности"""
        if not self.validate_input():
            raise ValueError("Invalid input parameters")

        behavior_map = {
            0: "all",
            1: "human",
            2: "robot"
        }

        return ReportParams(
            date_from=self.date_from.date().toPython(),
            date_to=self.date_to.date().toPython(),
            counter_id=self.counter_input.text().strip(),
            grouping=self.group_combo.currentText(),
            traffic_sources={k: cb.isChecked() for k, cb in self.traffic_sources.items()},
            behavior=behavior_map.get(self.behavior_group.checkedId(), "all"),
            locations=locations
        )
