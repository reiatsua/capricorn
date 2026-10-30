import io
import json
import base64
import random
import re
from typing import List, Dict, Any, Optional
from PIL import Image

import config
import system_controller
from skill_manager import skill_manager
from terminal_ui import ui

class CapriBrain:

    def __init__(self):
        self.history: List[Dict[str, str]] = []
        self.client_gemini = None
        self.chat = None
        self.chat_model = None
        self.provider = "mock"

        # Listen for dynamic skill updates from Capri self-modifications
        skill_manager.register_on_tools_updated(self._on_tools_updated)
        self._init_provider()

    def _on_tools_updated(self):
        """Called when Capri writes and activates a new tool."""
        self.chat = None  # Recreate chat with new toolset on next message
        ui.print_system("Мозги Капри обновлены: новый инструмент подключен в чат-сессию.")

    def _init_provider(self):
        self.active_model = config.GEMINI_MODEL
        if config.GEMINI_API_KEY:
            try:
                from google import genai
                self.client_gemini = genai.Client(api_key=config.GEMINI_API_KEY)
                self.provider = f"Gemini ({self.active_model})"
            except Exception as e:
                ui.print_status("ERROR", f"Failed to initialize Gemini SDK: {e}")
                self.provider = "mock"
        elif config.OPENAI_API_KEY or config.OPENAI_API_BASE:
            self.provider = "OpenAI/Ollama"
        else:
            self.provider = "Offline Demo (Mock)"

    def _get_gemini_candidates(self) -> List[str]:
        """Returns prioritized list of candidate models with generous quotas."""
        candidates = [
            self.active_model,
            "gemini-flash-lite-latest",
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash"
        ]
        seen = set()
        return [m for m in candidates if not (m in seen or seen.add(m))]

    def clear_memory(self):
        """Clears conversational history."""
        self.history.clear()
        self.chat = None
        self.chat_model = None

    def respond_to_text(self, user_text: str) -> str:
        """Generate response to user text/voice input with function calling capability."""
        # 1. Gemini Provider with Tools
        if self.client_gemini is not None:
            try:
                from google.genai import types

                for model_name in self._get_gemini_candidates():
                    try:
                        # Create or reuse chat session with all system and custom tools
                        if self.chat is None or self.chat_model != model_name:
                            self.chat = self.client_gemini.chats.create(
                                model=model_name,
                                config=types.GenerateContentConfig(
                                    system_instruction=config.CAPRI_SYSTEM_PROMPT,
                                    temperature=0.85,
                                    tools=skill_manager.get_all_tools()
                                )
                            )
                            self.chat_model = model_name

                        response = self.chat.send_message(user_text)
                        reply = response.text.strip() if response.text else "Сделано, чумба."

                        if model_name != self.active_model:
                            self.active_model = model_name
                            ui.print_system(f"Переключилась на активную модель: {model_name}")

                        # Update memory
                        self.history.append({"role": "user", "content": user_text})
                        self.history.append({"role": "assistant", "content": reply})
                        return reply

                    except Exception as e:
                        err_str = str(e)
                        self.chat = None # reset chat on error
                        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                            ui.print_status("ERROR", f"Квота {model_name} исчерпана (429). Пробую следующую модель...")
                            continue
                        else:
                            ui.print_status("ERROR", f"Gemini error ({model_name}): {err_str[:120]}")
                            break

                return self._mock_text_reply(user_text)

            except Exception as e:
                ui.print_status("ERROR", f"Gemini generation error: {e}")
                return self._mock_text_reply(user_text)

        # 2. OpenAI / Ollama Provider
        elif self.provider == "OpenAI/Ollama":
            try:
                import requests
                base_url = config.OPENAI_API_BASE.rstrip("/") if config.OPENAI_API_BASE else "https://api.openai.com/v1"
                headers = {"Content-Type": "application/json"}
                if config.OPENAI_API_KEY:
                    headers["Authorization"] = f"Bearer {config.OPENAI_API_KEY}"

                messages = [{"role": "system", "content": config.CAPRI_SYSTEM_PROMPT}]
                for turn in self.history[-config.MAX_HISTORY_TURNS:]:
                    messages.append({"role": turn["role"], "content": turn["content"]})
                messages.append({"role": "user", "content": user_text})

                res = requests.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": "gpt-4o-mini" if "openai" in base_url else "capri",
                        "messages": messages,
                        "temperature": 0.85
                    },
                    timeout=30
                )
                if res.status_code == 200:
                    reply = res.json()["choices"][0]["message"]["content"].strip()
                    self.history.append({"role": "user", "content": user_text})
                    self.history.append({"role": "assistant", "content": reply})
                    return reply
                else:
                    ui.print_status("ERROR", f"API error {res.status_code}: {res.text}")
                    return self._mock_text_reply(user_text)
            except Exception as e:
                ui.print_status("ERROR", f"OpenAI/Ollama error: {e}")
                return self._mock_text_reply(user_text)

        # 3. Mock Fallback
        else:
            return self._mock_text_reply(user_text)

    def analyze_screen(self, img: Image.Image) -> str:
        """Analyze screenshot and generate situational comment."""
        # Encode image to JPEG bytes
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=config.SCREENSHOT_JPEG_QUALITY)
        jpeg_bytes = buf.getvalue()

        vision_prompt = (
            "[SCREEN_CHECK] Проанализируй этот скриншот моего рабочего стола. "
            "Определи, чем я сейчас занимаюсь (пишу код, смотрю видео, играю, браузер, рабочий стол). "
            "Дай пару, ироничный, живой комментариев от лица Капри в стиле Найт-Сити (3-5 предложения, используй сленг типа чумба, дельта, корпо)."
        )

        if self.client_gemini is not None:
            try:
                from google.genai import types

                image_part = types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg")
                text_part = types.Part.from_text(text=vision_prompt)

                for model_name in self._get_gemini_candidates():
                    try:
                        response = self.client_gemini.models.generate_content(
                            model=model_name,
                            contents=[image_part, text_part],
                            config=types.GenerateContentConfig(
                                system_instruction=config.CAPRI_SYSTEM_PROMPT,
                                temperature=0.9,
                            )
                        )

                        comment = response.text.strip()
                        if model_name != self.active_model:
                            self.active_model = model_name
                            ui.print_system(f"Переключилась на активную модель: {model_name}")

                        # Store in history as a screen observation
                        self.history.append({"role": "assistant", "content": f"[Осмотрела экран]: {comment}"})
                        return comment

                    except Exception as e:
                        err_str = str(e)
                        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                            ui.print_status("ERROR", f"Квота {model_name} исчерпана (429). Пробую следующую модель...")
                            continue
                        else:
                            ui.print_status("ERROR", f"Gemini vision error ({model_name}): {err_str[:120]}")
                            break

                return self._mock_screen_reply()

            except Exception as e:
                ui.print_status("ERROR", f"Gemini screen analysis error: {e}")
                return self._mock_screen_reply()

        elif self.provider == "OpenAI/Ollama":
            try:
                import requests
                base_url = config.OPENAI_API_BASE.rstrip("/") if config.OPENAI_API_BASE else "https://api.openai.com/v1"
                headers = {"Content-Type": "application/json"}
                if config.OPENAI_API_KEY:
                    headers["Authorization"] = f"Bearer {config.OPENAI_API_KEY}"

                b64_img = base64.b64encode(jpeg_bytes).decode("utf-8")
                messages = [
                    {"role": "system", "content": config.CAPRI_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": vision_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                        ]
                    }
                ]
                res = requests.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={"model": "gpt-4o-mini", "messages": messages, "temperature": 0.85},
                    timeout=30
                )
                if res.status_code == 200:
                    comment = res.json()["choices"][0]["message"]["content"].strip()
                    self.history.append({"role": "assistant", "content": f"[Осмотрела экран]: {comment}"})
                    return comment
            except Exception as e:
                ui.print_status("ERROR", f"Vision API error: {e}")

        return self._mock_screen_reply()

    def _mock_text_reply(self, user_text: str) -> str:
        """Fallback replies when offline/mock with basic local tool handling."""
        lower = user_text.lower()
        
        # 1. Spotify / Media intents
        if any(w in lower for w in ["спотифай", "спотик", "spotify", "музык", "трек", "песн", "синтвейв", "саундтрек", "плейлист"]):
            if "пауз" in lower or "стоп" in lower:
                system_controller.control_playback("play_pause")
                return "Поставила спотик на паузу, чумба."
            elif "след" in lower or "скип" in lower or "дальш" in lower:
                system_controller.control_playback("next")
                return "Скипнула на следующий трек, лови новый ритм."
            elif "назад" in lower or "предыд" in lower:
                system_controller.control_playback("prev")
                return "Вернула предыдущий трек."
            else:
                # Extract query if possible
                query = re.sub(r"(включи|вруби|найди|запусти|поставь|песню|трек|музыку|в спотике|в спотифае|spotify)", "", lower).strip()
                res = system_controller.play_spotify(query)
                return f"Врубила спотик, чумба! {res}"

        if "громче" in lower or "прибавь" in lower:
            system_controller.control_playback("volume_up")
            return "Прибавила звук, качаем на полную!"

        if "тише" in lower or "убавь" in lower:
            system_controller.control_playback("volume_down")
            return "Сделала потише, чумба."

        # 2. Open App intents
        if any(lower.startswith(w) for w in ["открой ", "запусти ", "включи "]):
            app_target = re.sub(r"^(открой|запусти|включи)\s+", "", lower).strip()
            if app_target:
                res = system_controller.open_app(app_target)
                return f"Разворачиваю {app_target}, чумба. {res}"

        # 3. Files intents (Read-Only)
        if any(w in lower for w in ["покажи файлы", "список файлов", "что на рабочем столе", "файлы на рабочем"]):
            res = system_controller.list_directory()
            return f"Вот что нарыла на рабочем столе:\n{res}"

        # Default random conversational replies
        replies = [
            "В Сети сегодня тихо, чумба. Даже подозрительно тихо. Пора навести шороху.",
            "Принято, чумба. Твой дек пока не плавится — уже неплохой результат.",
            "Неплохая дельта. Но если полезешь за Черный Заслон, меня с собой не впутывай.",
            "Ха, забавный план. Только смотри, чтобы фиксеры Арасаки не узнали раньше времени.",
            "Я на связи. Сканирую эфир, пока ты возишься со своими делами.",
            "Слышу тебя громко и четко. Чего задумал на этот раз?"
        ]
        return random.choice(replies)

    def _mock_screen_reply(self) -> str:
        """Sample authentic screen comments when offline/mock."""
        comments = [
            "Похоже, ты готовишься к долгой ночке у монитора, чумба. Достойный выбор.",
            "Опять возишься с кодом? Смотри не слови киберпсихоз от этих багов.",
            "Наблюдаю за твоим экраном. Трафик стабильный, хром на месте. Продолжай.",
            "Так и будешь скроллить Сеть, или мы сегодня провернем что-нибудь серьезное?",
            "Вижу открытый терминал. Пахнет свежими скриптами и бессонницей, чумба."
        ]
        return random.choice(comments)
