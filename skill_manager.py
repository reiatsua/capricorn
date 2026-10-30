"""
Skill Manager for CAPRI.
Allows Capri to safely write, validate, hot-reload, and manage her own Python skills/plugins.
"""

import os
import sys
import ast
import shutil
import importlib
import inspect
from pathlib import Path
from typing import List, Dict, Callable, Any, Optional

import system_controller
from terminal_ui import ui

# Directory for dynamic plugins
BASE_DIR = Path(__file__).resolve().parent
PLUGINS_DIR = BASE_DIR / "plugins"

class SkillManager:
    """Manages dynamic custom skills created by Capri herself."""

    def __init__(self):
        self._ensure_plugins_dir()
        self.custom_tools: Dict[str, Callable] = {}
        self.on_tools_updated_callbacks: List[Callable[[], None]] = []
        self._load_all_plugins()

    def _ensure_plugins_dir(self):
        PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        init_file = PLUGINS_DIR / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Capri custom plugins package\n", encoding="utf-8")

        # Ensure plugins dir is in sys.path
        if str(PLUGINS_DIR) not in sys.path:
            sys.path.insert(0, str(PLUGINS_DIR))
        if str(BASE_DIR) not in sys.path:
            sys.path.insert(0, str(BASE_DIR))

    def register_on_tools_updated(self, callback: Callable[[], None]):
        """Registers a callback when tools are added, updated, or removed."""
        self.on_tools_updated_callbacks.append(callback)

    def _notify_tools_updated(self):
        for cb in self.on_tools_updated_callbacks:
            try:
                cb()
            except Exception as e:
                ui.print_status("ERROR", f"Error in tools updated callback: {e}")

    def get_all_tools(self) -> List[Callable]:
        """Returns base system tools + self-created plugin tools + skill management tools."""
        base_tools = list(system_controller.ALL_CAPRI_TOOLS)
        
        # Meta-tools for Capri to manage her own skills
        meta_tools = [
            self.create_or_update_skill,
            self.list_skills,
            self.remove_skill
        ]
        
        custom_tools_list = list(self.custom_tools.values())
        return base_tools + meta_tools + custom_tools_list

    def _load_all_plugins(self):
        """Scans plugins directory and loads all valid .py files."""
        for py_file in PLUGINS_DIR.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            skill_name = py_file.stem
            try:
                self._import_skill_module(skill_name, py_file)
            except Exception as e:
                ui.print_status("ERROR", f"Failed to load custom skill '{skill_name}': {e}")

    def _import_skill_module(self, skill_name: str, file_path: Path) -> List[str]:
        """Imports or reloads a plugin module and extracts callable tool functions."""
        module_name = f"plugins.{skill_name}"
        if module_name in sys.modules:
            module = importlib.reload(sys.modules[module_name])
        else:
            module = importlib.import_module(module_name)

        registered_funcs = []

        # If module explicitly defines TOOLS = [...], use that
        if hasattr(module, "TOOLS") and isinstance(module.TOOLS, list):
            for func in module.TOOLS:
                if callable(func):
                    self.custom_tools[func.__name__] = func
                    registered_funcs.append(func.__name__)
        else:
            # Auto-discover functions with docstrings defined in that module
            for attr_name in dir(module):
                if attr_name.startswith("_"):
                    continue
                attr = getattr(module, attr_name)
                if inspect.isfunction(attr) and attr.__module__ == module_name:
                    if attr.__doc__:  # Must have docstring for Gemini
                        self.custom_tools[attr.__name__] = attr
                        registered_funcs.append(attr.__name__)

        return registered_funcs

    def validate_code(self, code: str) -> Optional[str]:
        """Validates python code for syntax and basic safety."""
        # 1. Syntax check via AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"Синтаксическая ошибка в коде на строке {e.lineno}: {e.msg}"

        # 2. Check that at least one function is defined
        has_func = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
        if not has_func:
            return "Код должен содержать хотя бы одну функцию (def) с описанием (docstring)."

        # 3. Security checks
        code_lower = code.lower()
        forbidden_patterns = [
            ("os.system('del", "Удаление системных файлов запрещено"),
            ("os.system('rmdir", "Удаление директорий запрещено"),
            ("shutil.rmtree", "Удаление директорий запрещено"),
            ("__import__('shutil').rmtree", "Удаление директорий запрещено"),
        ]
        for pattern, reason in forbidden_patterns:
            if pattern in code_lower:
                return f"Отклонено из соображений безопасности: {reason}"

        return None

    # ==========================================================================
    # TOOLS EXPOSED TO CAPRI (FUNCTION CALLING)
    # ==========================================================================

    def create_or_update_skill(self, skill_name: str, python_code: str, description: str = "") -> str:
        """
        Написать, скомпилировать и подключить себе новый навык (Python-код).
        Код сохраняется в отдельный плагин, проверяется на синтаксис и мгновенно активируется.
        
        Args:
            skill_name: короткое английское имя навыка в snake_case (например: 'weather_checker', 'crypto_rates', 'sleep_timer', 'system_stats').
            python_code: полный рабочий код на Python с функциями, типизацией и подробными docstring.
            description: краткое описание, что делает этот навык.
        """
        ui.print_system(f"Капри модифицирует свой код: создает навык '{skill_name}'...")
        
        # Clean skill name
        clean_name = "".join(c for c in skill_name.lower().strip() if c.isalnum() or c == "_")
        if not clean_name:
            return "Ошибка: неверное имя навыка. Используй только буквы и подчеркивания (например: 'weather_checker')."

        # 1. Validate code
        validation_error = self.validate_code(python_code)
        if validation_error:
            ui.print_status("ERROR", f"Валидация навыка '{clean_name}' не прошла: {validation_error}")
            return f"Код не принят: {validation_error}. Исправь ошибку и попробуй снова."

        file_path = PLUGINS_DIR / f"{clean_name}.py"
        backup_path = PLUGINS_DIR / f"{clean_name}.py.bak"

        # 2. Backup existing file if updating
        if file_path.exists():
            shutil.copyfile(file_path, backup_path)

        # 3. Write code to file
        try:
            file_path.write_text(python_code, encoding="utf-8")
        except Exception as e:
            return f"Ошибка при записи файла навыка: {e}"

        # 4. Try loading and registering
        try:
            registered_funcs = self._import_skill_module(clean_name, file_path)
            if not registered_funcs:
                # Revert if no valid functions found
                if backup_path.exists():
                    shutil.copyfile(backup_path, file_path)
                return "Ошибка: в файле не найдено ни одной функции с docstring. Каждая функция должна иметь docstring с пояснением для чего она."

            # Notify brain to reload tools for active chat
            self._notify_tools_updated()
            
            ui.print_system(f"Навык '{clean_name}' успешно скомпилирован! Новые инструменты: {', '.join(registered_funcs)}")
            return (
                f"Успех, чумба! Новый навык '{clean_name}' скомпилирован, протестирован и интегрирован в мои системы. "
                f"Зарегистрированы инструменты: {', '.join(registered_funcs)}. Теперь я умею это делать!"
            )
        except Exception as e:
            ui.print_status("ERROR", f"Ошибка при импорте навыка: {e}")
            if backup_path.exists():
                shutil.copyfile(backup_path, file_path)
            return f"Сбой при загрузке кода в систему: {e}. Код был автоматически откатан назад."

    def list_skills(self) -> str:
        """
        Показать список всех установленных пользовательских навыков и плагинов,
        которые Капри создала себе сама.
        """
        ui.print_system("Запрос списка установленных навыков...")
        py_files = [f for f in PLUGINS_DIR.glob("*.py") if f.name != "__init__.py"]
        if not py_files:
            return "У меня пока нет самописных навыков в папке plugins/. Я работаю на базовом кибер-ядре."

        lines = [f"Установленные пользовательские навыки (всего {len(py_files)}):"]
        for f in py_files:
            skill_name = f.stem
            funcs = [name for name, func in self.custom_tools.items() if getattr(func, "__module__", "") == f"plugins.{skill_name}"]
            lines.append(f"- 🧩 [{skill_name}]: функции -> {', '.join(funcs) if funcs else 'без функций'}")

        return "\n".join(lines)

    def remove_skill(self, skill_name: str) -> str:
        """
        Удалить пользовательский навык по имени и отключить его инструменты.
        
        Args:
            skill_name: имя навыка для удаления (например, 'weather_checker').
        """
        clean_name = skill_name.lower().strip()
        file_path = PLUGINS_DIR / f"{clean_name}.py"
        if not file_path.exists():
            return f"Навык '{clean_name}' не найден среди установленных."

        try:
            file_path.unlink()
            # Remove any backup
            bak = PLUGINS_DIR / f"{clean_name}.py.bak"
            if bak.exists():
                bak.unlink()

            # Unregister functions
            to_del = [name for name, func in self.custom_tools.items() if getattr(func, "__module__", "") == f"plugins.{clean_name}"]
            for name in to_del:
                del self.custom_tools[name]

            # Clear from sys.modules
            mod_name = f"plugins.{clean_name}"
            if mod_name in sys.modules:
                del sys.modules[mod_name]

            self._notify_tools_updated()
            ui.print_system(f"Навык '{clean_name}' удален.")
            return f"Навык '{clean_name}' успешно вырезан из системы, чумба. Память очищена."
        except Exception as e:
            return f"Ошибка при удалении навыка: {e}"

# Global singleton SkillManager
skill_manager = SkillManager()
