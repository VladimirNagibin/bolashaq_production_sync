import json

from openai import OpenAI

from core.settings import settings
from schemas.open_ai_schemas import (
    KitItem,
    ProductCharacteristic,
    ProductSection,
)


class OpenAIService:
    def __init__(
        self, api_key: str | None = None, base_url: str | None = None
    ) -> None:
        self.api_key = api_key or settings.OPEN_AI_API_KEY
        self.base_url = base_url or settings.OPEN_AI_BASE_URL
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def parse_product_with_deepseek(
        self,
        text: str,
        name: str,
        article: str | None = None,
        brend: str | None = None,
    ) -> ProductSection:
        """
        Парсит описание товара с помощью DeepSeek API
        """

        # Создаем промпт
        system_prompt = """Ты эксперт по парсингу технических описаний товаров.
        Твоя задача - разбить описание товара на структурированные части:
        1. Анонс/назначение (краткое описание для чего используется товар)
        2. Подробное описание (технические детали и особенности)
        3. Характеристики товара (технические параметры)
        4. Комплектация (что входит в набор, дополнительные элементы)

        Характеристики заполни отдельными строками.
        """
        # Выдели числовые значения и единицы измерений.
        # Для комплектации извлеки артикулы (например S245-01).

        user_prompt = f"""
        Разбери следующее описание товара на структурированные части:

        {text}

        Верни ответ в формате JSON со следующей структурой:
        {{
            "announcement": "краткое назначение товара",
            "description": "подробное описание",
            "characteristics": [
                {{
                    "name": "Название характеристики",
                    "value": "значение",
                    "unit": "единица измерения"
                }}
            ],
            "kit": [
                {{
                    "code": "артикул",
                    "name": "название",
                    "description": "описание",
                    "specifications": {{}}
                }}
            ]
        }}

        Проверь правильность заполнения по наименованию: {name}
        """
        if brend:
            user_prompt = f"{user_prompt}, производителю: {brend}"
        if article:
            user_prompt = f"{user_prompt}, артикулу: {article}"

        try:
            # Вызов API DeepSeek
            response = self.client.chat.completions.create(
                model="deepseek-chat",  # или "deepseek-coder" для кода
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # низкая температура для консистентности
                max_tokens=2000,
                response_format={"type": "json_object"},  # просим JSON ответ
            )

            # Получаем и парсим ответ
            result_json = json.loads(response.choices[0].message.content)
            characteristics = result_json.get("characteristics", [])
            kits = result_json.get("kit", [])
            # Преобразуем в dataclass
            return ProductSection(
                announcement=result_json.get("announcement", ""),
                description=result_json.get("description", ""),
                characteristics=[
                    ProductCharacteristic(**charact)
                    for charact in characteristics
                ],
                kit=[KitItem(**kit) for kit in kits],
            )

        except Exception as e:
            print(f"Ошибка API DeepSeek: {e}")
            raise
