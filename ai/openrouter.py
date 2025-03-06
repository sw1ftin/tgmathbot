from openai import OpenAI
import os
import logging

class AIAssistant:
    def __init__(self,
                 api_key,
                 base_url="https://openrouter.ai/api/v1",
                 model="qwen/qwq-32b:free",
                 image_model="meta-llama/llama-3.2-11b-vision-instruct:free",
                 default_prompt=""):
        """
        :param api_key: API ключ для доступа к сервису
        :param base_url: URL API сервиса
        :param model: Модель для использования
        """
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.model = model
        self.image_model = image_model
        if not default_prompt:
            try:
                with open("ai/default_prompt.txt", "r", encoding="utf-8") as file:
                    self.default_prompt = file.read()
            except Exception as e:
                self.default_prompt = ""
        else:
            self.default_prompt = default_prompt

    def get_response(self, prompt: str) -> str | None:
        """
        Получение ответа от ИИ

        :param prompt: Запрос пользователя
        :return: Ответ от ИИ
        """
        print('Getting response')
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": self.default_prompt
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                choice = completion.choices[0]
                if hasattr(choice, "message"):
                    return choice.message.content
                else:
                    return choice.text
            except Exception as e:
                err_str = str(e)
                logging.error(err_str)
                if "Connection error" in err_str and attempt < max_attempts - 1:
                    import time
                    time.sleep(1)
                    continue
                return "Извините, произошла ошибка при получении ответа"
            
    def get_image_response(self, url: str) -> str | None:
        """
        Распознавание текста с картинки с помощью ИИ

        :param prompt: URL картинки
        :return: Ответ от ИИ
        """
        print('Getting response')
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                completion = self.client.chat.completions.create(
                    model=self.image_model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Распознай текст с картинки. Выведи только результат распознавания."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": url
                                    }
                                }
                            ]
                        }
                    ]
                )
                choice = completion.choices[0]
                if hasattr(choice, "message"):
                    return choice.message.content
                else:
                    return choice.text
            except Exception as e:
                err_str = str(e)
                logging.error(err_str)
                if "Connection error" in err_str and attempt < max_attempts - 1:
                    import time
                    time.sleep(1)
                    continue
                return "Извините, произошла ошибка при получении ответа"
        
            

def main():
    import dotenv
    dotenv.load_dotenv()
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    assistant = AIAssistant(api_key=OPENROUTER_API_KEY)
    from latexocr import FormulaRecognizer
    ocr = FormulaRecognizer()
    print('ok')
    print(ocr.recognize_from_image(r'test\\only_formula.png'))
    integral = ocr.recognize_from_image(r'test\\only_formula.png')
    print(assistant.get_response("Что это за интеграл? " + integral))

if __name__ == "__main__":
    main()
