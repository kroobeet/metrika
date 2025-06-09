"""Вкладка конфигурации API для настройки OAuth Яндекс.Метрики"""

from dataclasses import dataclass
from typing import Optional
import webbrowser

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QMessageBox)
from PySide6.QtCore import Signal
import requests

from core.models import ApiConfig
from core.exceptions import ConfigError


@dataclass
class ApiTabConfig:
    """Настройка элементов пользовательского интерфейса на вкладке API."""
    client_id_label: str = "Client ID:"
    client_secret_label: str = "Client Secret:"
    auth_code_label: str = "Authorization Code:"
    auth_code_placeholder: str = "Вставьте код из браузера здесь"
    token_label: str = "API Токен:"
    get_code_btn_text: str = "Получить код"
    load_token_btn_text: str = "Загрузить API токен"
    save_config_btn_text: str = "Сохранить настройки"


class ApiTab(QWidget):
    """Виджет для управления API и настройкой OAuth Яндекс.Метрики"""

    token_updated = Signal(str)  # Сигнал отправляемый при обновлении токена

    OAUTH_URL = "https://oauth.yandex.ru/authorize"
    TOKEN_URL = "https://oauth.yandex.ru/token"

    def __init__(self, config_manager, config: Optional[ApiConfig] = None):
        super().__init__()
        self.config_manager = config_manager
        self.ui_config = config or ApiTabConfig()
        self._init_ui()
        self._load_config()

    def _init_ui(self) -> None:
        """Инициализация компонентов пользовательского интерфейса"""
        layout = QVBoxLayout()

        # Поле Client ID
        self.client_id_input = self._create_input_field(
            self.ui_config.client_id_label, layout
        )

        # Поле Client Secret
        self.client_secret_input = self._create_input_field(
            self.ui_config.client_secret_label, layout
        )

        # Поле Authorization Code
        self.auth_code_input = QLineEdit()
        self.auth_code_input.setPlaceholderText(self.ui_config.auth_code_placeholder)
        self.auth_code_input.textChanged.connect(self._toggle_load_token_btn)
        self._add_labeled_field(
            self.ui_config.auth_code_label,
            self.auth_code_input,
            layout
        )

        # Кнопка "Загрузить токен"
        self.load_token_btn = QPushButton(self.ui_config.load_token_btn_text)
        self.load_token_btn.clicked.connect(self._load_api_token)
        self.load_token_btn.setVisible(False)
        layout.addWidget(self.load_token_btn)

        # Отображение токена
        self.token_input = QLineEdit()
        self.token_input.setReadOnly(True)
        self._add_labeled_field(
            self.ui_config.token_label,
            self.token_input,
            layout
        )

        # Кнопки действий
        button_layout = QHBoxLayout()

        self.get_token_btn = QPushButton(self.ui_config.get_code_btn_text)
        self.get_token_btn.clicked.connect(self._get_auth_code)
        button_layout.addWidget(self.get_token_btn)

        self.save_api_btn = QPushButton(self.ui_config.save_config_btn_text)
        self.save_api_btn.clicked.connect(self._save_config)
        button_layout.addWidget(self.save_api_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _create_input_field(self, label_text: str, parent_layout: QVBoxLayout) -> QLineEdit:
        """Создание меток для полей ввода"""
        input_field = QLineEdit()
        self._add_labeled_field(label_text, input_field, parent_layout)
        return input_field

    @staticmethod
    def _add_labeled_field(label_text: str, labeled_field: QLineEdit, layout: QVBoxLayout) -> None:
        """Добавление меток полей в макет"""
        field_layout = QHBoxLayout()
        field_layout.addWidget(QLabel(label_text))
        field_layout.addWidget(labeled_field)
        layout.addLayout(field_layout)

    def _toggle_load_token_btn(self, text: str) -> None:
        """Переключение видимости кнопки загрузки токена в зависимости от введённых данных"""
        self.load_token_btn.setVisible(bool(text.strip()))

    def _load_config(self) -> None:
        """Загрузка конфигурации API из менеджера конфигурации"""
        try:
            config = self.config_manager.load_api_config()
            self.client_id_input.setText(config.client_id)
            self.client_secret_input.setText(config.client_secret)
            self.token_input.setText(config.api_token)
        except ConfigError as e:
            QMessageBox.warning(
                self,
                "Ошибка конфигурации",
                f"Ошибка загрузки конфига: {str(e)}"
            )

    def _get_auth_code(self) -> None:
        """Открытие браузера, чтобы получить код авторизации"""
        client_id = self.client_id_input.text().strip()
        if not client_id:
            QMessageBox.warning(self, "Ошибка", "Поле Client ID является обязательным!")
            return

        try:
            auth_url = f"{self.OAUTH_URL}?response_type=code&client_id={client_id}"
            webbrowser.open(auth_url)
            QMessageBox.information(
                self,
                "Авторизация",
                "Браузер открыт для авторизации. Пожалуйста, скопируйте код после входа."
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Ошибка браузера",
                f"Не получилось открыть браузер: {str(e)}"
            )

    def _load_api_token(self) -> None:
        """Обмен кода авторизации на API токен"""
        required_fields = {
            "Authorization Code": self.auth_code_input.text().strip(),
            "Client ID": self.client_id_input.text().strip(),
            "Client Secret": self.client_secret_input.text().strip(),
        }

        for field_name, value in required_fields.items():
            if not value:
                QMessageBox.warning(self, "Ошибка ввода", f"Поле '{field_name}' является обязательным!")
                return

        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": required_fields["Authorization Code"],
                    "client_id": required_fields["Client ID"],
                    "client_secret": required_fields["Client Secret"]
                },
                timeout=10
            )
            response.raise_for_status()

            token_data = response.json()
            self.token_input.setText(token_data["access_token", ""])
            self.token_updated.emit(token_data["access_token", ""])

            config = ApiConfig(
                client_id=required_fields["Client ID"],
                client_secret=required_fields["Client Secret"],
                api_token=token_data.get("access_token", ""),
                refresh_token=token_data.get("refresh_token", "")
            )
            self.config_manager.save_api_config(config)

            QMessageBox.information(
                self,
                "Успех",
                "API токен успешно получен и сохранён!"
            )
        except requests.RequestException as e:
            QMessageBox.critical(
                self,
                "Ошибка API",
                f"Не удалось получить токен: {str(e)}"
            )

    def _save_config(self) -> None:
        """Сохранение текущей конфигурации"""
        try:
            config = ApiConfig(
                client_id=self.client_id_input.text().strip(),
                client_secret=self.client_secret_input.text().strip(),
                api_token=self.token_input.text().strip(),
                refresh_token=""  # Preserve existing refresh token
            )
            self.config_manager.save_api_config(config)
            QMessageBox.information(
                self,
                "Успех",
                "Конфигурация успешно сохранена!"
            )
        except ConfigError as e:
            QMessageBox.warning(
                self,
                "Ошибка сохранения",
                f"Не удалось сохранить конфиг: {str(e)}"
            )

    def get_auth_code(self) -> str:
        """Получение текущего OAuth токена"""
        return self.token_input.text().strip()
