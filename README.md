# 🏢 JARVIS4 — AI OFFICE

**Autonomous AI Organization** — виртуальная AI-компания, где множество интеллектуальных агентов совместно работают над сложными задачами.

Система работает непрерывно в облаке и поддерживает управление через **текст**, **голос** и **Telegram**.

---

## 🌟 Ключевые особенности

- **🤖 Мульти-агентная система** — Master, Project Manager, Agent Factory + Worker Agents
- **📱 Telegram как панель управления** — каждый агент имеет свой Telegram-бот
- **🎙 Голосовое управление** — Speech → Text → AI → Text → Speech
- **🧠 Самообучение** — short-term, long-term memory, knowledge base
- **🔧 Инструменты** — поиск, браузер, генерация изображений, код, API
- **🌐 REST API** — FastAPI сервер для интеграций
- **📡 WebSocket** — real-time обновления
- **🐳 Docker** — готов к деплою в облако
- **🔒 Безопасность** — bcrypt, JWT, rate limiting, валидация

---

## 📋 Архитектура

```
┌─────────────────────────────────────────────────┐
│                   USER                           │
│         (Telegram / Voice / API)                 │
└──────────┬──────────┬──────────┬────────────────┘
           │          │          │
    ┌──────▼──┐  ┌────▼────┐  ┌─▼──────────┐
    │Telegram │  │ Voice   │  │ REST API   │
    │  Bots   │  │ System  │  │ (FastAPI)  │
    └──────┬──┘  └────┬────┘  └─┬──────────┘
           │          │          │
    ┌──────▼──────────▼──────────▼────────────┐
    │           MASTER AGENT                   │
    │    (координация, декомпозиция задач)     │
    └──────┬──────────┬──────────┬────────────┘
           │          │          │
    ┌──────▼──┐ ┌─────▼────┐ ┌──▼──────────┐
    │ Project │ │  Agent   │ │   Worker    │
    │ Manager │ │ Factory  │ │   Agents    │
    └─────────┘ └──────────┘ └─────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              ┌─────▼──┐    ┌──────▼──┐    ┌───────▼──┐
              │Research│    │Program  │    │ Analyst  │
              │  er    │    │  mer    │    │          │
              └────────┘    └─────────┘    └──────────┘
              ┌────────┐    ┌─────────┐    ┌──────────┐
              │Designer│    │ Artist  │    │ Marketer │
              └────────┘    └─────────┘    └──────────┘
```

---

## 🤖 Агенты

| Агент | Роль | Описание |
|-------|------|----------|
| **Master** | Главный управляющий | Координация, декомпозиция задач, синтез результатов |
| **ProjectManager** | Менеджер проектов | Планирование, приоритизация, отслеживание |
| **AgentFactory** | Фабрика агентов | Создание новых агентов по запросу |
| **Researcher** | Исследователь | Поиск информации, анализ источников |
| **Programmer** | Программист | Написание кода, отладка, API |
| **Analyst** | Аналитик | Анализ данных, отчёты, прогнозы |
| **Designer** | Дизайнер | UI/UX, макеты, прототипы |
| **Artist** | Художник | Генерация изображений, иллюстрации |
| **Marketer** | Маркетолог | Стратегии, контент, SMM |

---

## 📱 Telegram Integration

### Каждый агент = свой бот

Каждый агент имеет **уникальный Telegram-бот** для прямого общения:

```
User → Telegram → Dev Agent Bot
         ↓
Dev Agent executes task
         ↓
Dev Agent sends updates
         ↓
Dev Agent sends final result
```

### Команды агента

- `/task <описание>` — дать задачу
- `/status` — текущий статус
- `/capabilities` — возможности
- `/history` — история задач
- `/cancel` — отменить задачу

### Control Panel Bot

Главный бот для управления всей системой:

- `/task <описание>` — задача для Master Agent
- `/assign <агент> <задача>` — задача конкретному агенту
- `/status` — статус всех агентов
- `/agents` — список агентов
- `/report` — полный отчёт

### Уведомления

Каждый агент отправляет:
- 📋 Задача получена
- 🧠 Начало анализа
- ⚙️ Выполнение
- 📊 Прогресс (%)
- ✅ Результат
- ❌ Ошибки

---

## 🎙 Voice System

Голосовой пайплайн:

```
Speech → Text → AI → Text → Speech
```

Голосовые ответы:
- Короткие
- Чёткие
- Естественные
- Разговорные

---

## 🧠 Self-Learning System

Три типа памяти:

| Тип | Описание | Хранение |
|-----|----------|----------|
| **Short-term** | Текущая сессия, контекст | In-memory (deque) |
| **Long-term** | История задач и решений | ChromaDB |
| **Knowledge Base** | Стратегии и факты | ChromaDB |

После каждой задачи:
1. Анализ результатов
2. Сохранение успешных стратегий
3. Переиспользование знаний

---

## 🛠 Инструменты

- 🔍 **Поиск в интернете** (DuckDuckGo)
- 🌐 **Браузер** (aiohttp + BeautifulSoup)
- 🎨 **Генерация изображений** (Stable Diffusion)
- 💻 **Выполнение кода** (Python sandbox)
- 🔗 **API вызовы** (HTTP client)

---

## 🚀 Установка

### 1. Клонирование

```bash
git clone https://github.com/YOUR_USERNAME/Jarvis4.git
cd Jarvis4
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка

```bash
cp .env.example .env
# Отредактируйте .env — добавьте API ключи и Telegram токены
```

### 4. Запуск

```bash
python run.py
```

### Docker

```bash
docker-compose up -d
```

---

## ⚙️ Конфигурация

Все настройки в файле `.env`:

- **AI API Keys** — OpenAI, Anthropic, Google
- **Telegram Tokens** — по одному на каждого агента
- **Server** — FastAPI host/port, WebSocket host/port
- **Voice** — язык, TTS engine
- **Memory** — пути к ChromaDB
- **Security** — secret key, JWT

---

## 📡 API Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Статус системы |
| POST | `/task` | Новая задача |
| GET | `/status` | Полный статус |
| GET | `/agents` | Список агентов |
| GET | `/tasks` | Все задачи |
| GET | `/task/{id}` | Статус задачи |
| POST | `/assign` | Задача агенту |
| GET | `/memory/stats` | Статистика памяти |
| POST | `/voice` | Голосовой ввод |

---

## 📁 Структура проекта

```
Jarvis4/
├── run.py                          # Точка входа
├── requirements.txt                # Зависимости
├── Dockerfile                      # Docker образ
├── docker-compose.yml              # Docker Compose
├── .env.example                    # Шаблон конфигурации
├── .gitignore
├── config/
│   ├── __init__.py
│   └── settings.py                 # Настройки
├── src/
│   ├── __init__.py
│   ├── agents/                     # AI Агенты
│   │   ├── __init__.py
│   │   ├── base_agent.py           # Базовый агент
│   │   ├── master_agent.py         # Master Agent
│   │   ├── project_manager_agent.py # Project Manager
│   │   ├── agent_factory.py        # Agent Factory
│   │   └── worker_agents.py        # Worker Agents
│   ├── core/                       # Ядро системы
│   │   ├── __init__.py
│   │   ├── agent_manager.py        # Менеджер агентов
│   │   └── task_engine.py          # Движок задач
│   ├── communication/              # Коммуникации
│   │   ├── __init__.py
│   │   ├── telegram_bot.py         # Telegram боты
│   │   └── websocket_server.py     # WebSocket
│   ├── voice/                      # Голосовая система
│   │   ├── __init__.py
│   │   └── voice_system.py         # STT + TTS
│   ├── memory/                     # Память и обучение
│   │   ├── __init__.py
│   │   └── memory_system.py        # 3-уровневая память
│   ├── tools/                      # Инструменты
│   │   ├── __init__.py
│   │   └── tools.py                # Поиск, браузер, код, API
│   ├── security/                   # Безопасность
│   │   ├── __init__.py
│   │   └── security_manager.py     # Auth, JWT, rate limit
│   └── api/                        # REST API
│       ├── __init__.py
│       └── server.py               # FastAPI сервер
├── data/
│   ├── logs/                       # Логи
│   ├── memory/                     # ChromaDB
│   └── knowledge/                  # База знаний
├── workspace/                      # Рабочая директория
└── generated_images/               # Сгенерированные изображения
```

---

## 🔒 Безопасность

- API ключи в переменных окружения (никогда не в коде)
- Пароли хешируются bcrypt
- JWT токены для авторизации
- Rate limiting на Telegram команды
- Валидация и санитизация ввода
- Безопасное выполнение кода в sandbox

---

## 📜 Принципы

> **Telegram = ПАНЕЛЬ УПРАВЛЕНИЯ**

- Агенты работают **автономно** в облаке
- Пользователь может **вмешаться в любой момент**
- Система работает **24/7**
- Коммуникация **прозрачна**
- Система ведёт себя как **настоящая AI-компания**

---

## 📄 License

MIT License
