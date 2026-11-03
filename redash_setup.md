# Запуск анализа и сборка дашборда Redash

Команды выполняются из корня проекта. Для анализа нужен Python 3.12, для Redash — Docker Compose. Стенд использует Redash 26.9.0, PostgreSQL 16.9 и Redis 7.

## Ноутбук

В подготовленном окружении:

```bash
.venv/bin/python -m jupyterlab sms_ab_analysis.ipynb
```

Установка окружения на новой машине:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m jupyterlab sms_ab_analysis.ipynb
```

В ноутбуке сохранены результаты выполнения. Для пересчёта выполните все ячейки сверху вниз. Если исходного `data/uplift_train.csv.gz` нет, ноутбук скачает его; таблицы сохраняются в `results/`, графики — в `figures/`. В анализ входят планирование выборки, синтетические A/A и A/B, оценка эффекта и проверка согласованности критерия с доверительными границами.

## Подготовленный стенд

```bash
docker compose up -d
```

Откройте [бизнес-дашборд](http://127.0.0.1:5055/dashboards/1-sms-). Учётная запись уже создана; её локальные реквизиты сохранены в `.env` как `REDASH_ADMIN_EMAIL` и `REDASH_ADMIN_PASSWORD`.

Для остановки с сохранением данных:

```bash
docker compose stop
```

## Новый стенд

1. Скопируйте `.env.example` в `.env`. Задайте собственный `POSTGRES_PASSWORD`, тот же пароль в `DATABASE_URL`, пароль `REDASH_PG_PASSWORD` для пользователя чтения и случайные значения `REDASH_COOKIE_SECRET` и `REDASH_SECRET_KEY`, например через `openssl rand -hex 32`. Если меняете `POSTGRES_PORT`, укажите тот же порт в `DATABASE_URL`.
2. Инициализируйте пустую базу Redash:

   ```bash
   docker compose up -d postgres redis
   docker compose run --rm server create_db
   docker compose up -d
   ```

   `create_db` выполняется один раз для пустой базы. На странице [Redash](http://127.0.0.1:5055) создайте организацию и учётную запись через форму первоначальной настройки.

3. Выполните ноутбук. Он использует `uplift_train.csv.gz` из [X5 RetailHero](https://ods.ai/competitions/x5-retailhero-uplift-modeling/data) и сформирует расчётные CSV.
4. Загрузите данные в PostgreSQL:

   ```bash
   .venv/bin/python scripts/load_postgres.py
   ```

   Загрузчик создаёт схему `sms_ab`, переносит исходных клиентов и результаты ноутбука одной транзакцией, сверяет агрегаты и сохраняет отчёт `results/postgres_check.json`. Повторная загрузка заменяет таблицы без дублирования строк. Для стандартной роли `sms_ab_reader` он задаёт пароль из `REDASH_PG_PASSWORD` и права чтения.

5. В **Settings → Data Sources → New Data Source → PostgreSQL** укажите:

   | Поле | Значение |
   |---|---|
   | Name | `sms_ab_postgres` |
   | Host | `postgres` |
   | Port | `5432` |
   | Database | `redash` |
   | User | `sms_ab_reader` |
   | Password | Значение `REDASH_PG_PASSWORD` из `.env` |

   Нажмите **Test Connection**.

## Запросы и визуализации через интерфейс

В **Create → New Query** выберите источник `sms_ab_postgres`, вставьте SQL из файла, выполните запрос и сохраните его. Для каждого запроса создайте указанные визуализации:

| SQL | Визуализация | Настройки |
|---|---|---|
| [totals.sql](sql/totals.sql) | Два Counter | `clients_total` — участники; `buyers_total` — покупатели; целые числа |
| [effect.sql](sql/effect.sql) | Два Counter | `effect_pp` — прирост в п.п., 3 знака; `relative_lift_pct` — относительный рост в %, 2 знака |
| [group_metrics.sql](sql/group_metrics.sql) | Column Chart | X: `group_name`; Y: `conversion_pct`; подпись оси Y: «Конверсия, %» |
| [group_metrics.sql](sql/group_metrics.sql) | Table | Группа, клиенты, покупатели, конверсия |
| [inference.sql](sql/inference.sql) | Table | p-value и статистический вывод |
| [intervals.sql](sql/intervals.sql) | Table | Прирост и границы 95% интервала, 3 знака |

Создайте дашборд **«SMS: результат эксперимента»** через **Create → New Dashboard**. Расположите сверху четыре Counter, ниже — график и сводку групп, затем — значимость и доверительный интервал. Добавьте текстовые блоки с определением конверсии и решением для бизнеса, как на [скриншоте](figures/redash_result.png). Сохраните и опубликуйте дашборд внутри Redash.

На новом стенде идентификатор дашборда может отличаться от ссылки в README. Для этой задачи достаточно одного бизнес-дашборда: он отвечает на вопрос об эффекте SMS и следующем шаге команды.

## Обновление результатов

После пересчёта ноутбука выполните:

```bash
.venv/bin/python scripts/load_postgres.py
```

Затем нажмите **Refresh** на дашборде Redash. При изменении структуры SQL отредактируйте соответствующие запросы через интерфейс. Планирование и симуляции остаются в ноутбуке; бизнес-дашборд использует пять запросов из таблицы выше.

`results/analysis_metadata.json` хранит хеши исходных данных и дизайна, параметры анализа и версии библиотек. `results/reproducibility_check.json` содержит сохранённую проверку воспроизводимости. Историческая проверка прежней конфигурации Redash помечена в `results/idempotency_check.json`; актуальное состояние стенда отражают `results/redash_check.json` и `results/browser_check.json`.
