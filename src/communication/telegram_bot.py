"""
Telegram Bot System — Individual bots for each agent + Control Panel.

Architecture:
- Each agent has its own unique Telegram bot
- Control Panel bot manages the entire system
- User can send tasks directly to specific agents
- Agents send real-time status updates

Flow:
  User → Telegram → Agent Bot → Agent executes → Agent sends updates → Result
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from telegram import Update, Bot
    from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot not installed. Telegram disabled.")


class AgentTelegramBot:
    """Individual Telegram bot for a specific agent."""

    def __init__(self, agent, bot_token: str):
        self.agent = agent
        self.bot_token = bot_token
        self.application = None
        self.bot = None
        self.chat_ids: List[int] = []
        self._running = False
        self.logger = logging.getLogger(f"tg.{agent.name}")

    async def start(self):
        """Start this agent's Telegram bot."""
        if not TELEGRAM_AVAILABLE or not self.bot_token or self.bot_token.startswith("your_"):
            self.logger.warning(f"Telegram bot skipped for {self.agent.name} (no token)")
            return

        try:
            self.application = Application.builder().token(self.bot_token).build()
            self.bot = Bot(token=self.bot_token)

            self.application.add_handler(CommandHandler("start", self._cmd_start))
            self.application.add_handler(CommandHandler("help", self._cmd_help))
            self.application.add_handler(CommandHandler("task", self._cmd_task))
            self.application.add_handler(CommandHandler("status", self._cmd_status))
            self.application.add_handler(CommandHandler("capabilities", self._cmd_caps))
            self.application.add_handler(CommandHandler("cancel", self._cmd_cancel))
            self.application.add_handler(CommandHandler("history", self._cmd_history))
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text)
            )

            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            self._running = True
            self.logger.info(f"Bot started for {self.agent.name}")
            self.agent.set_telegram_notifier(self)
        except Exception as e:
            self.logger.error(f"Failed to start bot for {self.agent.name}: {e}")

    async def stop(self):
        if self.application and self._running:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self._running = False

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        cid = update.message.chat_id
        if cid not in self.chat_ids:
            self.chat_ids.append(cid)
        info = self.agent.get_info()
        caps = "\n".join(f"• {c}" for c in info["capabilities"][:6])
        await update.message.reply_text(
            f"🤖 *{info['name']}* — {info['role']}\n\n"
            f"Возможности:\n{caps}\n\n"
            f"Команды:\n"
            f"/task <описание> — дать задачу\n"
            f"/status — статус\n"
            f"/capabilities — возможности\n"
            f"/history — история\n"
            f"/cancel — отменить\n\n"
            f"Или просто напишите задачу!",
            parse_mode="Markdown"
        )

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        await update.message.reply_text(
            f"📖 *{self.agent.name}* — {self.agent.role}\n\n"
            f"/task — назначить задачу\n"
            f"/status — текущий статус\n"
            f"/capabilities — возможности\n"
            f"/history — история задач\n"
            f"/cancel — отменить задачу",
            parse_mode="Markdown"
        )

    async def _cmd_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        cid = update.message.chat_id
        if cid not in self.chat_ids:
            self.chat_ids.append(cid)
        desc = " ".join(context.args) if context.args else ""
        if not desc:
            await update.message.reply_text("⚠️ Укажите задачу: /task <описание>")
            return
        await self._process_task(update, desc)

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        info = self.agent.get_info()
        emojis = {"idle": "⚪", "thinking": "💭", "working": "🔧",
                  "finished": "✅", "error": "❌"}
        await update.message.reply_text(
            f"📊 *{info['name']}*\n"
            f"Состояние: {emojis.get(info['state'], '❓')} {info['state']}\n"
            f"Задач в очереди: {info['task_queue_length']}\n"
            f"Выполнено: {info['completed_tasks_count']}\n"
            + (f"Текущая: {info['current_task']}" if info['current_task'] else ""),
            parse_mode="Markdown"
        )

    async def _cmd_caps(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        info = self.agent.get_info()
        caps = "\n".join(f"{i}. {c}" for i, c in enumerate(info["capabilities"], 1))
        await update.message.reply_text(
            f"🛠 *{info['name']}*\n\n{caps}", parse_mode="Markdown"
        )

    async def _cmd_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        if self.agent.current_task:
            desc = self.agent.current_task.description
            self.agent.current_task = None
            from src.agents.base_agent import AgentState
            self.agent.state = AgentState.IDLE
            await update.message.reply_text(f"🛑 Отменено: {desc[:100]}")
        else:
            await update.message.reply_text("ℹ️ Нет активных задач")

    async def _cmd_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        history = self.agent.completed_tasks[-10:]
        if not history:
            await update.message.reply_text("📜 История пуста")
            return
        text = f"📜 *{self.agent.name}* — последние задачи:\n\n"
        for i, t in enumerate(history, 1):
            s = "✅" if t.get("success") else "❌"
            text += f"{i}. {s} {t.get('description', 'N/A')[:60]}\n"
        await update.message.reply_text(text, parse_mode="Markdown")

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle plain text — chat as AI agent, not immediately as task.
        The agent can:
        - Greet and have conversations
        - Answer questions
        - Confirm tasks before executing
        - Support casual dialogue
        """
        if not update.message or not update.message.text:
            return
        cid = update.message.chat_id
        if cid not in self.chat_ids:
            self.chat_ids.append(cid)

        text = update.message.text.strip()

        # Check if user is confirming a pending task
        if hasattr(self, '_pending_task') and self._pending_task:
            if text.lower() in ['да', 'yes', 'ок', 'ok', 'давай', 'выполняй', 'go', 'подтверждаю', '+']:
                task_desc = self._pending_task
                self._pending_task = None
                await self._process_task(update, task_desc)
                return
            elif text.lower() in ['нет', 'no', 'отмена', 'cancel', 'не надо', '-']:
                self._pending_task = None
                await update.message.reply_text("👌 Задача отменена. Чем ещё могу помочь?")
                return

        # Use LLM to chat naturally
        if self.agent._llm_client:
            try:
                # Build conversation context
                history = getattr(self, '_chat_history', {}).get(cid, [])

                system_prompt = (
                    f"Ты — {self.agent.name}, AI-агент в системе Jarvis4 AI Office. "
                    f"Твоя роль: {self.agent.role}. "
                    f"Твои возможности: {', '.join(self.agent.capabilities[:5])}. "
                    f"Общайся дружелюбно и профессионально на русском языке. "
                    f"Если пользователь просит выполнить задачу или работу, "
                    f"НЕ выполняй сразу — спроси подтверждение: "
                    f"'Хотите, чтобы я выполнил эту задачу? Ответьте Да/Нет'. "
                    f"Если это просто разговор, приветствие или вопрос — отвечай как собеседник. "
                    f"Будь кратким (до 200 слов)."
                )

                response = await self.agent._llm_client.chat(
                    message=text,
                    system_prompt=system_prompt,
                    history=history[-10:]  # Last 10 messages for context
                )

                reply = response.content

                # Save chat history
                if not hasattr(self, '_chat_history'):
                    self._chat_history = {}
                if cid not in self._chat_history:
                    self._chat_history[cid] = []
                self._chat_history[cid].append({"role": "user", "content": text})
                self._chat_history[cid].append({"role": "assistant", "content": reply})
                # Keep last 20 messages
                self._chat_history[cid] = self._chat_history[cid][-20:]

                # Check if LLM suggested task confirmation
                if any(phrase in reply.lower() for phrase in [
                    'хотите, чтобы я выполнил', 'выполнить эту задачу',
                    'приступить к выполнению', 'начать работу',
                    'ответьте да/нет', 'да/нет'
                ]):
                    self._pending_task = text

                await update.message.reply_text(reply)

            except Exception as e:
                self.logger.error(f"LLM chat error: {e}")
                # Fallback: simple response
                await self._simple_chat(update, text)
        else:
            # No LLM — use simple pattern matching
            await self._simple_chat(update, text)

    async def _simple_chat(self, update, text: str):
        """Simple chat without LLM — pattern-based responses."""
        text_lower = text.lower()

        # Greetings
        if any(w in text_lower for w in ['привет', 'здравствуй', 'hello', 'hi', 'хай', 'добр']):
            await update.message.reply_text(
                f"👋 Привет! Я {self.agent.name} — {self.agent.role}.\n"
                f"Чем могу помочь? Напишите /task чтобы дать мне задачу."
            )
            return

        # How are you
        if any(w in text_lower for w in ['как дела', 'как ты', 'how are']):
            state = self.agent.state.value
            await update.message.reply_text(
                f"Спасибо, что спрашиваете! Сейчас я в состоянии: {state}. "
                f"Готов к работе! 💪"
            )
            return

        # What can you do
        if any(w in text_lower for w in ['что умеешь', 'что можешь', 'возможности', 'help']):
            caps = "\n".join(f"• {c}" for c in self.agent.capabilities[:6])
            await update.message.reply_text(
                f"🛠 Мои возможности:\n{caps}\n\n"
                f"Используйте /task <описание> чтобы дать мне задачу."
            )
            return

        # Looks like a task — ask for confirmation
        if len(text) > 20 and any(w in text_lower for w in [
            'сделай', 'создай', 'найди', 'напиши', 'разработай', 'проанализируй',
            'исследуй', 'нарисуй', 'спроектируй', 'make', 'create', 'find', 'write',
            'build', 'design', 'analyze', 'research'
        ]):
            self._pending_task = text
            await update.message.reply_text(
                f"📋 Похоже на задачу:\n_{text}_\n\n"
                f"Выполнить? Ответьте *Да* или *Нет*",
                parse_mode="Markdown"
            )
            return

        # Default
        await update.message.reply_text(
            f"Я {self.agent.name}. Напишите /task <описание> чтобы дать задачу, "
            f"или просто пообщаемся! 😊"
        )

    async def _process_task(self, update: Update, description: str):
        from src.agents.base_agent import Task
        await update.message.reply_text(
            f"📋 *Задача принята!*\n_{description}_", parse_mode="Markdown"
        )
        task = Task(description=description, assigned_to=self.agent.name,
                    metadata={"source": "telegram", "chat_id": update.message.chat_id})
        try:
            await self.agent.assign_task(task)
            await self.agent.think(task)
            result = await self.agent.work(task)

            # Check if result contains an image URL
            image_url = None
            if isinstance(result, dict):
                image_url = result.get("image_url")

            if image_url:
                # Send image
                try:
                    await update.message.reply_photo(
                        photo=image_url,
                        caption=f"✅ {result.get('task', description)}"
                    )
                except Exception as img_err:
                    await update.message.reply_text(
                        f"✅ Изображение создано!\nURL: {image_url}"
                    )
            else:
                result_text = str(result)
                if len(result_text) > 3500:
                    result_text = result_text[:3500] + "...(обрезано)"
                try:
                    await update.message.reply_text(f"✅ Готово!\n\n{result_text}")
                except Exception:
                    await update.message.reply_text(f"✅ Готово!\n\n{result_text[:1000]}")
        except Exception as e:
            try:
                await update.message.reply_text(f"❌ Ошибка: {e}")
            except Exception:
                await update.message.reply_text("❌ Произошла ошибка при выполнении задачи")

    async def send_notification(self, notification: Dict[str, Any]):
        """Send notification to all registered chats."""
        if not self._running or not self.bot:
            return
        msg = notification.get("data", {}).get("message", str(notification.get("type", "")))
        for cid in self.chat_ids:
            try:
                await self.bot.send_message(chat_id=cid, text=msg)
            except Exception as e:
                self.logger.error(f"Notification send error: {e}")
                try:
                    # Fallback: send without special chars
                    clean_msg = msg.replace('*', '').replace('_', '').replace('`', '')
                    await self.bot.send_message(chat_id=cid, text=clean_msg)
                except Exception:
                    pass


class ControlPanelBot:
    """
    Main control panel Telegram bot.
    
    Telegram acts as a CONTROL PANEL:
    - View all agents
    - Send tasks to any agent
    - Monitor system status
    - Override decisions
    """

    def __init__(self, task_engine, agent_manager, bot_token: str):
        self.task_engine = task_engine
        self.agent_manager = agent_manager
        self.bot_token = bot_token
        self.application = None
        self._running = False

    async def start(self):
        if not TELEGRAM_AVAILABLE or not self.bot_token or self.bot_token.startswith("your_"):
            logger.warning("Control Panel bot skipped (no token)")
            return

        try:
            self.application = Application.builder().token(self.bot_token).build()
            self.application.add_handler(CommandHandler("start", self._cmd_start))
            self.application.add_handler(CommandHandler("task", self._cmd_task))
            self.application.add_handler(CommandHandler("status", self._cmd_status))
            self.application.add_handler(CommandHandler("agents", self._cmd_agents))
            self.application.add_handler(CommandHandler("report", self._cmd_report))
            self.application.add_handler(CommandHandler("assign", self._cmd_assign))
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text)
            )

            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            self._running = True
            logger.info("Control Panel bot started")
        except Exception as e:
            logger.error(f"Control Panel bot error: {e}")

    async def stop(self):
        if self.application and self._running:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self._running = False

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        await update.message.reply_text(
            "🏢 *AI OFFICE — Панель управления*\n\n"
            "Команды:\n"
            "/task <описание> — новая задача\n"
            "/assign <агент> <задача> — задача конкретному агенту\n"
            "/status — статус системы\n"
            "/agents — список агентов\n"
            "/report — полный отчёт\n\n"
            "Или просто напишите задачу!",
            parse_mode="Markdown"
        )

    async def _cmd_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        desc = " ".join(context.args) if context.args else ""
        if not desc:
            await update.message.reply_text("⚠️ /task <описание задачи>")
            return
        await update.message.reply_text(f"📋 Задача принята: _{desc}_", parse_mode="Markdown")
        task = await self.task_engine.submit_task(desc)
        asyncio.create_task(self._execute_and_reply(update, task))

    async def _execute_and_reply(self, update, task):
        try:
            result = await self.task_engine.execute_task(task)

            # Check for images in results
            if isinstance(result, dict):
                for r in result.get("results", []):
                    res = r.get("result", {})
                    if isinstance(res, dict) and res.get("image_url"):
                        try:
                            await update.message.reply_photo(
                                photo=res["image_url"],
                                caption=f"🎨 {r.get('agent', 'Artist')}: изображение"
                            )
                        except Exception:
                            await update.message.reply_text(f"🎨 Изображение: {res['image_url']}")

            # Send text result
            text = str(result)
            if len(text) > 3500:
                text = text[:3500] + "..."
            try:
                await update.message.reply_text(f"✅ Результат:\n{text}")
            except Exception:
                await update.message.reply_text(f"✅ Результат:\n{text[:1000]}")
        except Exception as e:
            try:
                await update.message.reply_text(f"❌ Ошибка: {e}")
            except Exception:
                await update.message.reply_text("❌ Ошибка при выполнении задачи")

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        statuses = self.agent_manager.get_all_statuses()
        emojis = {"idle": "⚪", "thinking": "💭", "working": "🔧",
                  "finished": "✅", "error": "❌"}
        text = "🏢 *Статус AI Office*\n\n"
        for s in statuses:
            e = emojis.get(s["state"], "❓")
            text += f"{e} *{s['name']}* ({s['role']}): {s['state']}\n"
        await update.message.reply_text(text, parse_mode="Markdown")

    async def _cmd_agents(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        statuses = self.agent_manager.get_all_statuses()
        text = "👥 *Агенты AI Office*\n\n"
        for s in statuses:
            caps = ", ".join(s.get("capabilities", [])[:3])
            text += f"• *{s['name']}* — {s['role']}\n  _{caps}_\n\n"
        await update.message.reply_text(text, parse_mode="Markdown")

    async def _cmd_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        tasks = self.task_engine.get_all_tasks()
        done = [t for t in tasks if t["state"] == "finished"]
        active = [t for t in tasks if t["state"] != "finished"]
        text = (
            f"📊 *Отчёт AI Office*\n\n"
            f"Всего задач: {len(tasks)}\n"
            f"Выполнено: {len(done)}\n"
            f"Активных: {len(active)}\n\n"
        )
        if done:
            text += "*Последние выполненные:*\n"
            for t in done[-5:]:
                text += f"• {t['description'][:60]}\n"
        await update.message.reply_text(text, parse_mode="Markdown")

    async def _cmd_assign(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Assign task to specific agent: /assign researcher Find AI trends"""
        if not update.message or not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "⚠️ /assign <агент> <задача>\nПример: /assign researcher Найти тренды AI"
            )
            return
        agent_name = context.args[0]
        desc = " ".join(context.args[1:])
        agent = self.agent_manager.get_agent(agent_name)
        if not agent:
            await update.message.reply_text(f"❌ Агент '{agent_name}' не найден")
            return
        await update.message.reply_text(
            f"📋 Задача для *{agent_name}*: _{desc}_", parse_mode="Markdown"
        )
        task = await self.task_engine.submit_task(desc, target_agent=agent_name)
        asyncio.create_task(self._execute_and_reply(update, task))

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Chat with Master Agent via LLM, confirm tasks before executing."""
        if not update.message or not update.message.text:
            return
        text = update.message.text.strip()

        # Check pending task confirmation
        if hasattr(self, '_pending_task') and self._pending_task:
            if text.lower() in ['да', 'yes', 'ок', 'ok', 'давай', 'go', '+']:
                desc = self._pending_task
                self._pending_task = None
                await update.message.reply_text(f"⚡ Выполняю: _{desc}_", parse_mode="Markdown")
                task = await self.task_engine.submit_task(desc)
                asyncio.create_task(self._execute_and_reply(update, task))
                return
            elif text.lower() in ['нет', 'no', 'отмена', 'cancel', '-']:
                self._pending_task = None
                await update.message.reply_text("👌 Отменено. Чем ещё помочь?")
                return

        # Try LLM chat
        master = self.agent_manager.get_agent("master")
        if master and master._llm_client:
            try:
                system_prompt = (
                    "Ты — Jarvis, главный AI-ассистент системы AI Office. "
                    "Ты управляешь командой AI-агентов: Researcher, Programmer, Analyst, Designer, Artist, Marketer. "
                    "Общайся дружелюбно на русском. Если пользователь просит выполнить работу, "
                    "спроси подтверждение: 'Выполнить задачу? Ответьте Да/Нет'. "
                    "Если это разговор — поддержи беседу. Будь кратким."
                )
                response = await master._llm_client.chat(
                    message=text, system_prompt=system_prompt
                )
                reply = response.content

                if any(p in reply.lower() for p in ['выполнить задачу', 'да/нет', 'приступить']):
                    self._pending_task = text

                await update.message.reply_text(reply)
            except Exception as e:
                logger.error(f"Control panel LLM error: {e}")
                await self._simple_control_chat(update, text)
        else:
            await self._simple_control_chat(update, text)

    async def _simple_control_chat(self, update, text: str):
        """Fallback chat without LLM."""
        t = text.lower()
        if any(w in t for w in ['привет', 'hello', 'hi', 'здравствуй']):
            await update.message.reply_text(
                "👋 Привет! Я Jarvis — управляющий AI Office.\n"
                "Используйте /task для задач или просто пообщаемся!"
            )
        elif any(w in t for w in ['как дела', 'как ты']):
            await update.message.reply_text(
                "Отлично! Все агенты на местах и готовы к работе. 🏢"
            )
        elif len(text) > 15 and any(w in t for w in ['сделай', 'создай', 'найди', 'напиши']):
            self._pending_task = text
            await update.message.reply_text(
                f"📋 Задача: _{text}_\n\nВыполнить? *Да/Нет*", parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "Я Jarvis! Напишите /task для задачи или /status для статуса. 😊"
            )


class TelegramBotManager:
    """Manages all Telegram bots (agent bots + control panel)."""

    def __init__(self, agent_manager, task_engine, settings):
        self.agent_manager = agent_manager
        self.task_engine = task_engine
        self.settings = settings
        self.agent_bots: Dict[str, AgentTelegramBot] = {}
        self.control_bot: Optional[ControlPanelBot] = None

    async def initialize(self):
        """Create bots for all agents. Avoid duplicate tokens (one token = one bot)."""
        used_tokens = set()

        # Control panel bot gets priority for the main token
        control_token = self.settings.TELEGRAM_CONTROL_TOKEN
        if control_token and not control_token.startswith("your_"):
            self.control_bot = ControlPanelBot(
                self.task_engine, self.agent_manager, control_token
            )
            used_tokens.add(control_token)
            logger.info(f"Control Panel bot registered")

        # Agent bots — only if they have UNIQUE tokens (not same as control)
        for name, agent in self.agent_manager.agents.items():
            token = self.settings.TELEGRAM_TOKENS.get(name, "")
            if token and not token.startswith("your_") and token not in used_tokens:
                bot = AgentTelegramBot(agent, token)
                self.agent_bots[name] = bot
                used_tokens.add(token)
                logger.info(f"Agent bot registered: {name}")

        logger.info(f"Total bots: {len(self.agent_bots)} agents + {'1 control' if self.control_bot else '0 control'}")

    async def start_all(self):
        """Start all bots."""
        tasks = []
        for name, bot in self.agent_bots.items():
            tasks.append(asyncio.create_task(bot.start()))
        if self.control_bot:
            tasks.append(asyncio.create_task(self.control_bot.start()))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"Started {len(self.agent_bots)} agent bots + control panel")

    async def stop_all(self):
        """Stop all bots."""
        tasks = []
        for bot in self.agent_bots.values():
            tasks.append(asyncio.create_task(bot.stop()))
        if self.control_bot:
            tasks.append(asyncio.create_task(self.control_bot.stop()))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
