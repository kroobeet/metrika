"""Вкладка для управления и выбора местоположений для отчётов."""

from pathlib import Path
from typing import Dict, List, Optional, TypedDict
import json

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
                               QLabel, QHBoxLayout, QPushButton, QFileDialog,
                               QMessageBox)
from PySide6.QtCore import Qt, Signal
from core.models import Location


class LocationState(TypedDict):
    """Определение типа для состояния локации"""
    checked: bool
    cities: Dict[str, bool]


class LocationsTabConfig:
    """Конфигурация для вкладки локаций"""
    presets_dir: Path = Path("temp/presets/locations")
    default_preset_name: str = "locations_preset_.json"
    header_labels: List[str] = ["Локация", "Тип"]
    region_type: str = "Регион"
    city_type: str = "Город"
    save_btn_text: str = "Сохранить набор локаций"
    load_btn_text: str = "Загрузить набор локаций"
    main_file_warning: str = "Нельзя загружать главный файл с локациями!"


class LocationsTab(QWidget):
    """Виджет управления выбором локаций для отчёта"""

    locations_changed = Signal()  # Генерация сигнала при изменении выбора локации

    def __init__(self, config_manager, config: Optional[LocationsTabConfig] = None):
        super().__init__()
        self.config_manager = config_manager
        self.ui_config = config or LocationsTabConfig()
        self.locations_data: Dict[str, Dict] = {}
        self._init_ui()
        self._load_locations()

    def _init_ui(self) -> None:
        """Инициализация компонентов пользовательского интерфейса"""
        layout = QVBoxLayout()

        # Дерево локаций
        self.locations_tree = QTreeWidget()
        self.locations_tree.setHeaderLabels(self.ui_config.header_labels)
        self.locations_tree.setSelectionMode(QTreeWidget.MultiSelection)
        self.locations_tree.itemChanged.connect(self._on_item_changed)

        layout.addWidget(QLabel("Выберите регионы или города:"))
        layout.addWidget(self.locations_tree)

        # Кнопки действий
        buttons_layout = QHBoxLayout()

        self.save_preset_btn = QPushButton(self.ui_config.save_btn_text)
        self.save_preset_btn.clicked.connect(self._save_locations_preset)
        buttons_layout.addWidget(self.save_preset_btn)

        self.load_preset_btn = QPushButton(self.ui_config.load_btn_text)
        self.load_preset_btn.clicked.connect(self._load_locations_preset)
        buttons_layout.addWidget(self.load_preset_btn)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def _save_locations_preset(self) -> None:
        """Сохранение текущего выбора локаций в качестве пресета"""
        self.ui_config.presets_dir.mkdir(parents=True, exist_ok=True)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить набор локаций",
            str(self.ui_config.presets_dir / self.ui_config.default_preset_name),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self._get_locations_state(), f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Успех", "Набор локаций успешно сохранён!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {str(e)}")

    def _load_locations_preset(self) -> None:
        """Загрузка файла с пресетом для локаций"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить набор локаций",
            str(self.ui_config.presets_dir),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        if Path(file_path).samefile(Path("configs/locations.json")):
            QMessageBox.critical(self, "Ошибка", self.ui_config.main_file_warning)
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                preset_data = json.load(f)

            if not self._validate_preset_data(preset_data):
                QMessageBox.critical(self, "Ошибка", "Некорректный формат файла!")
                return

            self._apply_preset_data(preset_data)
            QMessageBox.information(self, "Успех", "Набор локаций успешно загружен!")
            self.locations_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить: {str(e)}")

    def _get_locations_state(self) -> Dict[str, LocationState]:
        """Получение текущего состояния выбранных локаций"""
        state = {}
        for i in range(self.locations_tree.topLevelItemCount()):
            region_item = self.locations_tree.topLevelItem(i)
            region_name = region_item.text(0)
            state[region_name] = {
                'checked': region_item.checkState(0) == Qt.CheckState.Checked,
                'cities': {
                    region_item.child(j).text(0):
                    region_item.child(j).checkState(0) == Qt.CheckState.Checked
                    for j in range(region_item.childCount())
                }
            }
        return state

    @staticmethod
    def _validate_preset_data(data: Dict) -> bool:
        """Валидация структуры данных пресета"""
        return all(
            isinstance(region, str) and
            isinstance(region_data, dict) and
            isinstance(region_data.get('checked', False), bool) and
            isinstance(region_data.get('cities', {}), dict) and
            all(isinstance(c, str) and isinstance(s, bool)
            for c, s in region_data['cities'].items())
            for region, region_data in data.items()
        )

    def _apply_preset_data(self, preset_data: Dict[str, LocationState]) -> None:
        """Применение пресета к пользовательскому интерфейсу"""
        self.locations_tree.itemChanged.disconnect(self._on_item_changed)

        try:
            # Update UI
            for i in range(self.locations_tree.topLevelItemCount()):
                region_item = self.locations_tree.topLevelItem(i)
                region_name = region_item.text(0)

                if region_name in preset_data:
                    region_data = preset_data[region_name]
                    region_item.setCheckState(0,
                                              Qt.CheckState.Checked
                                              if region_data['checked']
                                              else Qt.CheckState.Unchecked)

                    for j in range(region_item.childCount()):
                        city_item = region_item.child(j)
                        city_name = city_item.text(0)

                        if city_name in region_data['cities']:
                            city_item.setCheckState(0,
                                                    Qt.CheckState.Checked
                                                    if region_data['cities'][city_name]
                                                    else Qt.CheckState.Unchecked)

            # Обновление данных в памяти
            self._update_in_memory_data(preset_data)
        finally:
            self.locations_tree.itemChanged.connect(self._on_item_changed)

    def _update_in_memory_data(self, preset_data: Dict[str, LocationState]) -> None:
        """Обновление данных в памяти из пресета"""
        if "Россия" not in self.locations_data:
            return

        for region_name, region_data in self.locations_data["Россия"].items():
            if region_name in preset_data:
                preset_region = preset_data[region_name]
                region_data["full"] = preset_region["checked"]

                for city_name in region_data.get("cities", {}):
                    if city_name in preset_data["cities"]:
                        region_data["cities"][city_name] = preset_region["cities"][city_name]

        try:
            self.config_manager.save_locations(self.locations_data)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Внимание",
                f"не удалось сохранить главный файл локаций: {str(e)}"
            )

    def _load_locations(self) -> None:
        """Загрузка локаций из менеджера конфигурации"""
        try:
            self.locations_data = self.config_manager.load_locations()
            self._update_locations_tree()
        except Exception as e:
            QMessageBox.warning(
                self,
                "Ошибка загрузки",
                f"Не удалось загрузить локации: {str(e)}"
            )

    def _update_locations_tree(self) -> None:
        """Обновление дерева локаций на основе данных, хранящихся в памяти."""
        self.locations_tree.clear()
        self.locations_tree.itemChanged.disconnect(self._on_item_changed)

        if not self.locations_data.get("Россия"):
            return

        for region, region_data in self.locations_data["Россия"].items():
            region_item = QTreeWidgetItem(self.locations_tree)
            region_item.setText(0, region)
            region_item.setText(1, self.ui_config.region_type)
            region_item.setCheckState(0,
                                      Qt.CheckState.Checked
                                      if region_data.get("full", False)
                                      else Qt.CheckState.Unchecked)

            for city, selected in region_data.get("cities", {}).items():
                city_item = QTreeWidgetItem(region_item)
                city_item.setText(0, city)
                city_item.setText(1, self.ui_config.city_type)
                city_item.setCheckState(0, Qt.CheckState.Checked if selected else Qt.CheckState.Unchecked)

        # self.locations_tree.expandAll() # Раскрыть дерево со списком локаций
        self.locations_tree.itemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Обработка изменения выбора элемента."""
        if column != 0:
            return

        is_checked = item.checkState(0) == Qt.CheckState.Checked
        item_type = item.text(1)
        item_name = item.text(0)

        if item_type == self.ui_config.region_type:
            self._update_region_state(item_name, is_checked)
        elif item_type == self.ui_config.city_type:
            parent = item.parent()
            if parent:
                self._update_city_state(parent.text(0), item_name, is_checked)

        try:
            self.config_manager.save_locations(self.locations_data)
            self.locations_changed.emit()
        except Exception as e:
            QMessageBox.warning(
                self,
                "Ошибка сохранения",
                f"Не удалось сохранить локации: {str(e)}"
            )

    def _update_region_state(self, region_name: str, is_selected: bool) -> None:
        """Обновление состояния выбора региона и его городов"""
        if "Россия" not in self.locations_data or region_name not in self.locations_data["Россия"]:
            return

        self.locations_data["Россия"][region_name]["full"] = is_selected

        if "cities" in self.locations_data["Россия"][region_name]:
            for city in self.locations_data["Россия"][region_name]["cities"]:
                self.locations_data["Россия"][region_name]["cities"][city] = is_selected

        self._update_locations_tree()

    def _update_city_state(self, region_name: str, city_name: str, is_selected: bool) -> None:
        """При необходимости обновляет выбранный город и родительский регион"""
        if ("Россия" not in self.locations_data or
                region_name not in self.locations_data["Россия"] or
                "cities" not in self.locations_data["Россия"][region_name] or
                city_name not in self.locations_data["Россия"][region_name]["cities"]):
            return

        self.locations_data["Россия"][region_name]["cities"][city_name] = is_selected

        all_cities_selected = all(
            self.locations_data["Россия"][region_name]["cities"].values()
        )
        self.locations_data["Россия"][region_name]["full"] = all_cities_selected

    def get_selected_locations(self) -> List[Location]:
        """Получает список выбранных местоположений"""
        selected_items = []

        def walk_tree(item_tree: QTreeWidgetItem) -> None:
            if item_tree.checkState(0) == Qt.CheckState.Checked:
                selected_items.append(item_tree)
            for j in range(item_tree.childCount()):
                walk_tree(item_tree.child(j))

        for i in range(self.locations_tree.topLevelItemCount()):
            walk_tree(self.locations_tree.topLevelItem(i))

        locations = []
        for item in selected_items:
            if item.text(1) == self.ui_config.region_type:
                region = item.text(0)
                if region in self.locations_data["Россия"]:
                    locations.extend(
                        Location(name=city, region=region, selected=True)
                        for city in self.locations_data["Россия"][region]["cities"]
                    )
                else:
                    locations.append(Location(
                        name=item.text(0),
                        region=item.parent().text(0),
                        selected=True
                    ))

        return locations
