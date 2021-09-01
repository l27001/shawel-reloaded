class CommandNotFound(Exception):
    """Вызывается, когда команда не может быть найдена"""
    def __init__(self, message="Команда не найдена"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"Вызвано исключение CommandNotFound с сообщением: {self.message}"
