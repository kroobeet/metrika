from typing import List
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget,
                               QTreeWidgetItem, QLabel, QAbstractItemView)
from PySide6.QtCore import Qt
from core.models import Location


class LocationsTab(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.locations_data = {}
        self._init_ui()
        self._load_locations()

    def _init_ui(self):
        """Инициализация пользовательского интерфейса"""
        layout = QVBoxLayout()

        # Дерево регионов и городов
        self.locations_tree = QTreeWidget()
        self.locations_tree.setHeaderLabels(["Локация", "Тип"])
        self.locations_tree.setSelectionMode(QTreeWidget.MultiSelection)
        self.locations_tree.itemChanged.connect(self._on_item_changed)

        layout.addWidget(QLabel("Выберите регионы или города"))
        layout.addWidget(self.locations_tree)

        self.setLayout(layout)

    def _load_locations(self):
        """Загрузка локаций из файла"""
        try:
            self.locations_data = self.config_manager.load_locations()
            self._update_locations_tree()
        except Exception as e:
            print(f"Ошибка загрузки локаций: {str(e)}")

    def _update_locations_tree(self):
        """Обновление дерева локаций"""
        self.locations_tree.clear()
        self.locations_tree.itemChanged.disconnect(self._on_item_changed)

        if not self.locations_data.get("Россия"):
            return

        for region, region_data in self.locations_data["Россия"].items():
            region_item = QTreeWidgetItem(self.locations_tree)
            region_item.setText(0, region)
            region_item.setText(1, "Регион")
            region_item.setCheckState(0, Qt.CheckState.Checked if region_data.get("full", False) else Qt.CheckState.Unchecked)

            for city, selected in region_data.get("cities", {}).items():
                city_item = QTreeWidgetItem(region_item)
                city_item.setText(0, city)
                city_item.setText(1, "Город")
                city_item.setCheckState(0, Qt.CheckState.Checked if selected else Qt.CheckState.Unchecked)

        self.locations_tree.expandAll()
        self.locations_tree.itemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, item, column):
        """Обработка изменения состояния элемента"""
        if column != 0:
            return

        is_checked = item.checkState(0) == Qt.CheckState.Checked
        item_type = item.text(1)
        item_name = item.text(0)

        # Обновляем данные в памяти
        if item_type == "Регион":
            self._update_region_state(item_name, is_checked)
        elif item_type == "Город":
            parent = item.parent()
            if parent:
                region_name = parent.text(0)
                self._update_city_state(region_name, item_name, is_checked)

        # Сохраняем изменения в файл
        try:
            self.config_manager.save_locations(self.locations_data)
        except Exception as e:
            print(f"Ошибка сохранения локаций: {str(e)}")

    def _update_region_state(self, region_name, is_selected):
        """Обновление состояния региона и его городов"""
        if "Россия" not in self.locations_data or region_name not in self.locations_data["Россия"]:
            return

        # Обновляем состояние региона
        self.locations_data["Россия"][region_name]["full"] = is_selected

        # Обновляем все города в регионе
        if "cities" in self.locations_data["Россия"][region_name]:
            for city in self.locations_data["Россия"][region_name]["cities"]:
                self.locations_data["Россия"][region_name]["cities"][city] = is_selected

        # Обновляем дерево, чтобы отразить изменения
        self._update_locations_tree()

    def _update_city_state(self, region_name, city_name, is_selected):
        """Обновление состояния города"""
        if ("Россия" not in self.locations_data or
                region_name not in self.locations_data["Россия"] or
                "cities" not in self.locations_data["Россия"][region_name] or
                city_name not in self.locations_data["Россия"][region_name]["cities"]):
            return

        # Обновляем состояние города
        self.locations_data["Россия"][region_name]["cities"][city_name] = is_selected

        # Проверяем, нужно ли обновить состояние региона
        all_cities_selected = all(
            self.locations_data["Россия"][region_name]["cities"].values()
        )
        self.locations_data["Россия"][region_name]["full"] = all_cities_selected

    def get_selected_locations(self) -> List[Location]:
        """Получение списка выбранных локаций"""
        selected_items = []

        # Рекурсивно обходим все элементы дерева
        def walk_tree(item):
            if item.checkState(0) == Qt.CheckState.Checked:
                selected_items.append(item)
            for i in range(item.childCount()):
                walk_tree(item.child(i))

        for i in range(self.locations_tree.topLevelItemCount()):
            walk_tree(self.locations_tree.topLevelItem(i))

        locations = []
        for item in selected_items:
            if item.text(1) == "Регион":
                region = item.text(0)
                if region in self.locations_data["Россия"]:
                    for city in self.locations_data["Россия"][region]["cities"]:
                        locations.append(Location(
                            name=city,
                            region=region,
                            selected=True
                        ))
            else:
                city = item.text(0)
                region = item.parent().text(0)
                locations.append(Location(
                    name=city,
                    region=region,
                    selected=True
                ))

        return locations