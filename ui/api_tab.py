from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QMessageBox)
from core.models import ApiConfig
import requests


class ApiTab(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self._init_ui()
        self._load_config()

    def _init_ui(self):
        """Инициализация пользовательского интерфейса"""
        layout = QVBoxLayout()

        # Поля для ввода данных API
        client_id_layout = QHBoxLayout()
        client_id_layout.addWidget(QLabel("Client ID:"))
        self.client_id_input = QLineEdit()
        client_id_layout.addWidget(self.client_id_input)
        layout.addLayout(client_id_layout)

        client_secret_layout = QHBoxLayout()
        client_secret_layout.addWidget(QLabel("Client Secret:"))
        self.client_secret_input = QLineEdit()
        client_secret_layout.addWidget(self.client_secret_input)
        layout.addLayout(client_secret_layout)

        # Поле для авторизационного кода
        auth_code_layout = QHBoxLayout()
        auth_code_layout.addWidget(QLabel("Авторизационный код:"))
        self.auth_code_input = QLineEdit()
        self.auth_code_input.setPlaceholderText("Вставьте сюда код из браузера")
        self.auth_code_input.textChanged.connect(self._toggle_load_token_btn)
        auth_code_layout.addWidget(self.auth_code_input)
        layout.addLayout(auth_code_layout)

        # Кнопка для загрузки токена
        self.load_token_btn = QPushButton("Загрузить API токен")
        self.load_token_btn.clicked.connect(self._load_api_token)
        self.load_token_btn.setVisible(False)
        layout.addWidget(self.load_token_btn)

        # Поле для API токена
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("API Token:"))
        self.token_input = QLineEdit()
        self.token_input.setReadOnly(True)
        token_layout.addWidget(self.token_input)
        layout.addLayout(token_layout)

        # Кнопки для работы с API
        api_buttons_layout = QHBoxLayout()

        self.get_token_btn = QPushButton("Получить код")
        self.get_token_btn.clicked.connect(self._get_auth_code)
        api_buttons_layout.addWidget(self.get_token_btn)

        self.save_api_btn = QPushButton("Сохранить настройки")
        self.save_api_btn.clicked.connect(self._save_config)
        api_buttons_layout.addWidget(self.save_api_btn)

        layout.addLayout(api_buttons_layout)
        self.setLayout(layout)

    def _toggle_load_token_btn(self, text):
        """Показывает/скрывает кнопку загрузки токена"""
        self.load_token_btn.setVisible(bool(text.strip()))

    def _load_config(self):
        """Загрузка конфигурации API"""
        try:
            config = self.config_manager.load_api_config()
            self.client_id_input.setText(config.client_id)
            self.client_secret_input.setText(config.client_secret)
            self.token_input.setText(config.api_token)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить конфигурацию: {str(e)}")

    def _get_auth_code(self):
        """Получение авторизационного кода"""
        client_id = self.client_id_input.text().strip()
        if not client_id:
            QMessageBox.warning(self, "Ошибка", "Введите Client ID!")
            return

        try:
            import webbrowser
            url = f"https://oauth.yandex.ru/authorize?response_type=code&client_id={client_id}"
            webbrowser.open(url)
            QMessageBox.information(self, "Получение кода",
                                    "Браузер открыт для получения кода. "
                                    "После авторизации скопируйте код в поле 'Авторизационный код'")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть браузер: {str(e)}")

    def _load_api_token(self):
        """Получение API токена по авторизационному коду"""
        auth_code = self.auth_code_input.text().strip()
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()

        if not auth_code:
            QMessageBox.warning(self, "Ошибка", "Введите авторизационный код!")
            return
        if not client_id:
            QMessageBox.warning(self, "Ошибка", "Введите Client ID!")
            return
        if not client_secret:
            QMessageBox.warning(self, "Ошибка", "Введите Client Secret!")
            return

        try:
            response = requests.post(
                "https://oauth.yandex.ru/token",
                data={
                    "grant_type": "authorization_code",
                    "code": auth_code,
                    "client_id": client_id,
                    "client_secret": client_secret
                },
                timeout=10
            )
            response.raise_for_status()

            token_data = response.json()
            self.token_input.setText(token_data.get("access_token", ""))

            # Сохраняем refresh_token в конфиг
            config = ApiConfig(
                client_id=client_id,
                client_secret=client_secret,
                api_token=token_data.get("access_token", ""),
                refresh_token=token_data.get("refresh_token", "")
            )
            self.config_manager.save_api_config(config)

            QMessageBox.information(self, "Успех", "API токен успешно получен и сохранён!")
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить токен: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении токена: {str(e)}")

    def _save_config(self):
        """Сохранение конфигурации API"""
        try:
            config = ApiConfig(
                client_id=self.client_id_input.text().strip(),
                client_secret=self.client_secret_input.text().strip(),
                api_token=self.token_input.text().strip(),
                refresh_token=""  # Сохраняем существующий refresh_token
            )

            if self.config_manager.save_api_config(config):
                QMessageBox.information(self, "Успех", "Конфигурация успешно сохранена!")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить конфигурацию: {str(e)}")

    def get_oauth_token(self) -> str:
        """Получение текущего OAuth токена"""
        return self.token_input.text().strip()