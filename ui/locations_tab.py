from typing import List
from pathlib import Path
import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget,
                               QTreeWidgetItem, QLabel,
                               QHBoxLayout, QPushButton, QFileDialog, QMessageBox)
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

        # Кнопки для работы с наборами локаций
        buttons_layout = QHBoxLayout()

        self.save_preset_btn = QPushButton("Сохранить набор локаций")
        self.save_preset_btn.clicked.connect(self._save_locations_preset)
        buttons_layout.addWidget(self.save_preset_btn)

        self.load_preset_btn = QPushButton("Загрузить набор локаций")
        self.load_preset_btn.clicked.connect(self._load_locations_preset)
        buttons_layout.addWidget(self.load_preset_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def _save_locations_preset(self):
        """Сохранение текущего набора локаций в файл"""
        # Создаем папку presets/locations если её нет
        presets_dir = Path("temp/presets/locations")
        presets_dir.mkdir(parents=True, exist_ok=True)

        # Получаем текущее состояние локаций
        current_state = self._get_locations_state()

        # Запрашиваем имя файла для сохранения
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить набор локаций",
            str(presets_dir / "locations_preset_.json"),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        # Сохраняем данные в файл
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(current_state, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Успех", "Набор локаций успешно сохранён!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить набор локаций: {str(e)}")

    def _load_locations_preset(self):
        """Загрузка набора локаций из файла"""
        # Запрашиваем файл для загрузки
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить набор локаций",
            "temp/presets/locations",
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        # Запрещаем загрузку основного файла локаций
        if Path(file_path).samefile(Path("configs/locations.json")):
            QMessageBox.critical(self, "Ошибка", "Нельзя загружать основной файл локаций!")
            return

        # Загружаем и валидируем данные
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                preset_data = json.load(f)

            # Валидация структуры данных
            if not self._validate_preset_data(preset_data):
                QMessageBox.critical(self, "Ошибка", "Файл имеет неверный формат!")
                return

            # Применяем загруженные настройки
            self._apply_preset_data(preset_data)
            QMessageBox.information(self, "Успех", "Набор локаций успешно загружен!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить набор локаций: {str(e)}")

    def _get_locations_state(self):
        """Получение текущего состояния локаций в виде словаря"""
        state = {}
        for i in range(self.locations_tree.topLevelItemCount()):
            region_item = self.locations_tree.topLevelItem(i)
            region_name = region_item.text(0)
            state[region_name] = {
                'checked': region_item.checkState(0) == Qt.CheckState.Checked,
                'cities': {}
            }

            for j in range(region_item.childCount()):
                city_item = region_item.child(j)
                city_name = city_item.text(0)
                state[region_name]['cities'][city_name] = city_item.checkState(0) == Qt.CheckState.Checked

        return state

    @staticmethod
    def _validate_preset_data(data) -> bool:
        """Валидация загружаемых данных"""
        if not isinstance(data, dict):
            return False

        for region, region_data in data.items():
            if not isinstance(region, str):
                return False
            if 'checked' not in region_data or not isinstance(region_data['checked'], bool):
                return False
            if 'cities' not in region_data or not isinstance(region_data['cities'], dict):
                return False

            for city, checked in region_data['cities'].items():
                if not isinstance(city, str) or not isinstance(checked, bool):
                    return False

        return True

    def _apply_preset_data(self, preset_data):
        """Применение загруженных данных к текущим локациям"""
        # Отключаем сигналы для предотвращений множественных обновлений
        self.locations_tree.itemChanged.disconnect(self._on_item_changed)

        try:
            # Обновляем состояние элементов дерева
            for i in range(self.locations_tree.topLevelItemCount()):
                region_item = self.locations_tree.topLevelItem(i)
                region_name = region_item.text(0)

                if region_name in preset_data:
                    region_data = preset_data[region_name]
                    region_item.setCheckState(0, Qt.CheckState.Checked if region_data['checked'] else Qt.CheckState.Unchecked)

                    for j in range(region_item.childCount()):
                        city_item = region_item.child(j)
                        city_name = city_item.text(0)

                        if city_name in region_data['cities']:
                            city_item.setCheckState(0, Qt.CheckState.Checked if region_data['cities'][city_name] else Qt.CheckState.Unchecked)

            # Обновляем данные в памяти
            self._update_in_memory_data(preset_data)
        finally:
            self.locations_tree.itemChanged.connect(self._on_item_changed)

    def _update_in_memory_data(self, preset_data):
        """Обновление данных в памяти на основе пресета"""
        if "Россия" not in self.locations_data:
            return

        for region_name, region_data in self.locations_data["Россия"].items():
            if region_name in preset_data:
                preset_region = preset_data[region_name]
                region_data["full"] = preset_region["checked"]

                for city_name in region_data.get("cities", {}):
                    if city_name in preset_region["cities"]:
                        region_data["cities"][city_name] = preset_region["cities"][city_name]

        # Сохраняем изменения в файл
        try:
            self.config_manager.save_config(self.locations_data)
        except Exception as e:
            QMessageBox.warning(self, "Предупреждение", f"Не удалось сохранить изменения в основной файл: {str(e)}")

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