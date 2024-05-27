import requests
import psycopg2
import random
import time


# Токена API HH.ru
hh_api_token = ''

# Конфигурация БД PostgreSQL
db_config = {
    'dbname': 'default_db',
    'user': 'gen_user',
    'password': '',
    'host': '',
    'port': ''
}


# Функция для создания таблицы vacancies
def create_table(conn):
    cursor = conn.cursor()

    create_table_query = """
        CREATE TABLE IF NOT EXISTS resumes (
            id SERIAL PRIMARY KEY,
            region VARCHAR(50),
            company VARCHAR(200),
            title VARCHAR(200),
            keywords TEXT,
            education TEXT,
            experience VARCHAR(50),
            salary VARCHAR(50),
        )
    """
    cursor.execute(create_table_query)

    conn.commit()
    cursor.close()
    print("Таблица 'resumes' успешно создана.")


# Функция для получения резюме
def get_resumes(region, profession, page):
    url = 'https://api.hh.ru/resumes'
    params = {
        'text': f"{profession} {region}",
        'area': region,
        'specialization': 1,
        'per_page': 50,
        'page': page,
        'label': 'only_with_age'
    }
    headers = {
        'Authorization': f'Bearer {hh_api_token}'
    }

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()




# Функция для парсинга резюме
def parse_resumes():
    regions = {
        'Москва': 1,
        'Санкт-Петербург': 2
    }

    professions = [
        'BI Developer', 'Business Development Manager', 'Community Manager', 'Computer vision',
        'Data Analyst', 'Data Engineer', 'Data Science', 'Data Scientist', 'ML Engineer',
        'Machine Learning Engineer', 'ML OPS инженер', 'ML-разработчик', 'Machine Learning',
        'Product Manager', 'Python Developer', 'Web Analyst', 'Аналитик данных',
        'Бизнес-аналитик', 'Веб-аналитик', 'Системный аналитик', 'Финансовый аналитик'
    ]

    with psycopg2.connect(**db_config) as conn:

        create_table(conn)

        for region, region_id in regions.items():
            for profession in professions:
                page = 0
                while True:
                    try:
                        data = get_resumes(region_id, profession, page)

                        if not data.get('items'):
                            break

                        with conn.cursor() as cursor:
                            for item in data['items']:
                                if profession.lower() not in item['name'].lower():
                                    continue

                                title = f"{item['name']} ({region})"
                                keywords = item['snippet'].get('requirement', '')
                                experience = item['experience'].get('name', '')
                                business = item['business'].get('name', '')
                                education = item['education']
                                company = item['company_title'].get('name', '')
                                salary = item['salary']
                                if salary is None:
                                    salary = "з/п не указана"
                                else:
                                    salary = salary.get('from', '')

                                insert_query = """
                                    INSERT INTO vacancies 
                                    (region, company, title, keywords, experience, business, education, salary) 
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """
                                cursor.execute(insert_query,
                                               (region, title, company, keywords, experience, business, education, salary))

                            if page >= data['pages'] - 1:
                                break

                            page += 1


                            time.sleep(random.uniform(3, 6))

                    except requests.HTTPError as e:
                        print(f"Ошибка при обработке региона {region}: {e}")
                        continue

        conn.commit()

    print("Парсинг завершен. Данные сохранены в базе данных PostgreSQL.")


def remove_duplicates():
    with psycopg2.connect(**db_config) as conn:
        cursor = conn.cursor()

        # Удалить дубликаты на основе столбца «url»
        delete_duplicates_query = """
            DELETE FROM resumes
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM resumes
                GROUP BY url
            )
        """
        cursor.execute(delete_duplicates_query)

        conn.commit()
        cursor.close()

    print("Дубликаты в таблице 'resumes' успешно удалены.")


def run_parsing_job():
    print("Запуск парсинга...")

    try:
        parse_resumes()
        remove_duplicates()
    except Exception as e:
        print(f"Ошибка при выполнении задачи парсинга: {e}")


