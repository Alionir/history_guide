class HistoryGuideException(Exception):
    """Базовое исключение для приложения"""
    pass

class DatabaseError(HistoryGuideException):
    """Ошибки работы с базой данных"""
    pass

class ValidationError(HistoryGuideException):
    """Ошибки валидации данных"""
    pass

class AuthenticationError(HistoryGuideException):
    """Ошибки аутентификации"""
    pass

class AuthorizationError(HistoryGuideException):
    """Ошибки авторизации (недостаточно прав)"""
    pass

class EntityNotFoundError(HistoryGuideException):
    """Сущность не найдена"""
    pass

class DuplicateEntityError(HistoryGuideException):
    """Дублирование сущности"""
    pass