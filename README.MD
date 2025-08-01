# RED FAX

> **P2P‑мессенджер нового поколения**  
> С централизованным бэкендом с планами по переходу на полностью децентрализованную архитектуру.

![Скриншот интерфейса RED FAX](assets/image.png)

---
## https://redfax.netlify.app/
---

## 🔍 Описание

На данный момент RED FAX — клиент‑серверный мессенджер с собственным API на FastAPI и хранилищем в MongoDB/GridFS.  
Пользователи могут:
- Регистрироваться и авторизоваться;
- Создавать личные и групповые чаты;
- Отправлять текст, голосовые сообщения и файлы;
- Управлять профилем, списком друзей и задачами;
- Общаться в реальном времени через WebSocket и обмен WebRTC‑сигналингом.

---

## 🚀 Текущие возможности

- **Регистрация и авторизация** по JWT (FastAPI + OAuth2)  
- **Личные и групповые чаты** через WebSocket  
- **Текстовые сообщения**: AES‑шифрование симметричным ключом  
- **Голосовые сообщения**: хранятся в GridFS 
- **Отправка и приём файлов** (GridFS, до 50 МБ, до 20 файлов на пользователя)  
- **Профиль пользователя**: аватар, BIO, имя, город и прочие поля  
- **Управление друзьями**: взаимные «френд‑запросы»  
- **Задачи/напоминания**: CRUD через REST API  
- **WebRTC‑сигналинг**: обмен SDP и ICE‑кандидатами по тому же WebSocket  
- **Контейнеризация**: Docker & Docker Compose

---

## 🏗 Технологический стек

| Компонент       | Технологии                                         |
| --------------- | -------------------------------------------------- |
| **Backend**     | Python, FastAPI, Motor (async MongoDB), GridFS     |
| **Realtime**    | WebSocket (FastAPI), JSON‑сообщения                |
| **Файловое хранилище** | MongoDB GridFS, StreamingResponse           |
| **Авторизация** | JWT, bcrypt, OAuth2PasswordBearer                  |
| **Frontend**    | React/Vue/Angular + WebSocket + Fetch API + Tailwind CSS + TypeScript + Vite |
| **Контроль версий** | Git, GitHub                                    |

---

## 🛣 Дорожная карта

1. **Контент‑адресуемое хранение файлов**  
   - Чанки (256 КБ) → Merkle‑DAG → корневой CID  
   - Шифрование чанков (X25519+ECDH)  

2. **Репликация через P2P‑сеть**  
   - PubSub‑топик для метаданных  
   - Bitswap / DHT (libp2p + WebRTC)  
   - Кэширование в IndexedDB (offline‑first)  

3. **Восстановление чатов и файлов на новом клиенте**  
   - Подписка на PubSub → загрузка метаданных  
   - Запрос недостающих чанков по CID  
   - Сборка и дешифровка «плавающих» файлов в UI  

4. **Голосовые и видео‑звонки (WebRTC)**  
   - Full‑mesh (1:1, малые группы)  
   - SFU‑вариант для больших групп (DTLS‑SRTP)  
   - Фоллбэки: libp2p DataChannel или WebSocket  

5. **Ключевые моменты и caveats**  
   - Уровни репликации: pin‑скрепление vs всегда‑он  
   - NAT и STUN/TURN: надёжность P2P  
   - Безопасность метаданных в PubSub  
   - Версионирование (новые rootCID как «обновление»)  

6. **Потенциальные интеграции**  
   - js‑IPFS, libp2p + bitswap + pubsub  
   - OrbitDB, Hypercore/Hyperdrive, GunDB  

---

## ⚙ Установка и запуск

# 1. Клонировать репозиторий
   - git clone https://github.com/DARKLEGENT_AI/REDFAX.git
   - cd REDFAX

# 2. Установить зависимости
   - pip install -r requirements.txt

# 3. Запустить MongoDB в Docker
   - docker compose -f docker-compose.yml up -d --build mongodb

# 4. Запустить API-сервер
   - uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   - Примечание: Если у вас нет внешнего IP, можно воспользоваться обратным пробросом портов.
   - Для этого запустите скрипт lt-loop-15min.bat.
   
---

   - REDFAX_SERVER/
   - ├── main.py              # Точка входа (FastAPI, маршруты)
   - ├── models.py            # MongoDB модели и подключение
   - ├── schemas.py           # Pydantic схемы
   - ├── auth.py              # JWT, bcrypt, OAuth2
   - ├── crypto.py            # AES‑шифрование/дешифровка
   - ├── docker-compose.yml   # MongoDB сервис
   - └── site/                # Фронтенд (React/Vue/Angular + Vite)