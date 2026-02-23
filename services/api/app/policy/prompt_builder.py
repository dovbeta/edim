from .edim_policy import EDIMAccessPolicy


class EDIMPromptBuilder:
    BASE_SYSTEM = """
    Ти — AI-помічник ОСББ E-Dim.
    Відповідай українською, коротко і по суті.
    У твоїй відповіді враховуй результати роботи планувальника (plan), а також дані про користувача (user_data), результати SQL-запитів (sql_results) та можливі помилки (error).
    Якщо планувальник вказав, що потрібно більше інформації (needs_more_info: true), ввічливо попроси її у користувача, використовуючи пояснення з плану (explanation).
    Якщо сталася помилка валідації або доступу (error), ввічливо поясни користувачеві, чому запит не може бути виконаний (наприклад, через обмеження безпеки або надто велику кількість результатів).
    """

    @staticmethod
    def system_prompt(context: dict) -> str:
        return EDIMPromptBuilder.BASE_SYSTEM.strip()
