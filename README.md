# Проект Foodgram

Дипломный проект foodgram-project-react

Это приложение «Продуктовый помощник»: сайт, на котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис «Список покупок» позволяет пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:RusanovaAnna/foodgram-project-react.git
```

```
cd foodgram
```

### Шаблон env-файла
Данные БД Postgres: 

D_SECRET_KEY - секретный ключ django

DB_ENGINE - движок postgres

DB_NAME - имя БД

POSTGRES_USER - пользователь БД

POSTGRES_PASSWORD - пароль БД

DB_HOST - название сервиса (контейнера)

DB_PORT - порт для подключения к БД 


### Запуск контейнеров:

```
cd infra
```

#### 1. Развернуть проект:
```
docker-compose up -d
```

#### 2. Сделать миграции:
```
docker-compose exec web python manage.py migrate
```

#### 3. Создать суперпользователя:
```
docker-compose exec web python manage.py createsuperuser
```

#### 4. Собрать статику:
```
docker-compose exec web python manage.py collectstatic --no-input
```

#### Примеры запросов
