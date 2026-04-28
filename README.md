## Django JWT

### Запуск в режиме отладки

1. git clone https://github.com/IlyaBril/QualityApp.git

2. Переименуйте  *qualityapp/env-dev-sample* в *qualityapp/.env.dev*.
3. При необходимости обновите параметры в *docker-compose.yaml* и *.env.dev* файлах
4. Создайте образ и запустите контейнеры:

    ```sh
    $ docker compose up -d --build
    $ docker compose -f docker-compose.yaml exec quality_app python qualityapp/manage.py migrate
    ```
5. Создайте суперпользователя:
   ```sh
   $ docker compose -f docker-compose.yaml exec quality_app python qualityapp/manage.py createsuperuser
   ```
6. Загрузите демонстрационные данные:
   ```sh
   $ docker compose -f docker-compose.yaml exec quality_app python qualityapp/manage.py loaddata qualityapp/demodata.json
   ```
   
7. [http://127.0.0.1:8000/login ](http:/127.0.0.1:8000/login).

   - Пользователь ilya пароль qwe1234### - Супер пользователь. Может видеть все данные.
   - Пользователь guset пароль qwe123### - Обычный пользователь. Может видеть данные своего департамента.

6. Административную панель. [http://127.0.0.1:8000/admin](http:/127.0.0.1:8000/admin).


### Производство

В разработке...