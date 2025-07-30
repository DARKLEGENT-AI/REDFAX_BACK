# Настройка MongoDB
MONGO_URI = "mongodb://root:example@mongo:27017"
DB_NAME   = "messenger"

# Настройка ключей JWT
SECRET_KEY                = "your-secret-key"
ALGORITHM                 = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Настройка максимального размера и количиства файлов для юзера
MAX_FILE_SIZE  = 50 * 1024 * 1024  # Каждый файл максимум 50 МБ
MAX_FILE_COUNT = 20 # Максимум 20 файлов у каждого пользователя

# CORS
ALLOWED_ORIGINS = ["*"]

# Сервер
HOST = "0.0.0.0"
PORT = 8000

# Сообщение
MAX_MESSAGE_LENGTH = 4096