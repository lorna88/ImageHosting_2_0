### *Проект ImageHosting*
- Сервис для просмотра и хранения картинок в виде веб-приложения.
- Пользователь заходит на сайт, загружает изображения, а взамен получает прямые ссылки на них.
- Есть удобная галерея для просмотра всех загруженных картинок. Галерея разделена на страницы
по 12 изображений на каждой.
- Каждая картинка содержит информацию:
  - оригинальное имя файла;
  - размер файла в КБ;
  - дату и время загрузки;
- Картинки кликабельны, перейдя по ссылке, можно просмотреть изображение и скопировать ссылку 
на него.
- Каждое изображение содержит кнопку удаления.

### *Поддерживаемые форматы:* 
.jpg, .jpeg, .png, .gif

### *Максимальный размер файла:*
5 МБ

### *Запуск*

```bash
docker compose up --build
```
Приложение доступно по адресу: `http://localhost:8080`

### *Маршруты*
- **Маршрут:** `/`
Главная страница проекта с приветственным сообщением. 
Содержит ссылки на основные маршруты.
- **Маршрут:** `/upload/`
Принимает файл изображения от пользователя через HTTP-запрос (метод POST). 
Сохраняет изображение в папку `/images` на сервере. Возвращает пользователю страницу 
со ссылкой на изображение.
- **Маршрут:** `/images/`
Галерея изображений - переход на первую страницу
- **Маршрут:** `/images/?page=<номер_страницы>`
Переход на конкретную страницу в галерее изображений
- **Маршрут:** `/images/<имя_файла>`
Доступ по прямой ссылке ко всем загруженным изображениям для просмотра и скачивания
- **Маршрут:** `/delete/<id>`
Удаление изображения с идентификатором id (метод DELETE)

### *Архитектура проекта*
Система состоит из трёх основных компонентов:
1. **Python-бэкенд:**
- Отвечает за обработку HTTP-запросов, загрузку и удаление изображений, валидацию 
данных и логирование.
- Выполняет бизнес-логику приложения, связанную с управлением загруженными файлами.
- Работает внутри Docker-контейнера, слушая запросы на порту `8000`.
- Написан без использования фреймворков, используя только стандартную библиотеку для 
обработки запросов http.server.
2. **Nginx-сервер:**
- Раздает статические файлы и загруженные изображения.
- Проксирует запросы на Python-бэкенд для запросов на получение списка изображений,
загрузку и удаление изображений.
- Работает в отдельном Docker-контейнере, слушая запросы на порту `80`.
3. **Сервер БД PostgreSQL:**
- Хранит метаданные изображений в отдельной таблице.
- Предоставляет возможность резервного копирования данных таблицы.

Сервис Python-бэкенд подключен к двум локальным сетям back-network и front-network,
созданных с помощью Docker Compose, что позволяет ему разграничить взаимодействие 
с сервером Nginx и с базой данных.

### *Резервное копирование базы данных*
1. **Запуск вручную**
с помощью bash-скрипта backup.sh. Запустить скрипт можно непосредственно в среде bash
либо командой:

```bash
bash backup.sh
```

Все резервные копии хранятся в папке `/backups`. 
Бэкап сохраняется с указанием даты и времени.

2. **Автоматическое резервное копирование**
возможно в случае запуска приложения отдельной командой:

```bash
docker compose -f auto_backup_compose.yml up --build
```

В этом случае в систему добавляется ещё один компонент - сервис автоматического 
резервного копирования [postgres-backup-local](https://github.com/prodrigestivill/docker-postgres-backup-local),
который создаёт резервные копии ежедневно. 
Копии хранятся в папке `/backups/daily`. Срок хранения 7 дней.
При желании частоту создания копий и время хранения можно настроить.

2. **Восстановление базы данных из резервной копии**

```bash
docker exec -i db psql -U postgres images_db < backups/<имя_файла>
```

### *Зависимости*
- Docker
- Python 3.12 или выше
- loguru
- pillow
- dotenv
- psycopg