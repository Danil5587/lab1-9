import re
import sqlite3

# Исходные данные студентов (включая заведомо ошибочный email у Тимура для демонстрации)
students = [
    {
        'name': 'Aida',
        'group': 'IS-24-01',
        'score': 82,
        'attendance': 91,
        'email': 'aida@atu.edu.kz',
    },
    {
        'name': 'Miras',
        'group': 'IS-24-01',
        'score': 69,
        'attendance': 88,
        'email': 'miras@atu.edu.kz',
    },
    {
        'name': 'Dana',
        'group': 'IS-24-02',
        'score': 91,
        'attendance': 96,
        'email': 'dana@atu.edu.kz',
    },
    {
        'name': 'Timur',
        'group': 'IS-24-02',
        'score': 74,
        'attendance': 62,
        'email': 'timur_at_atu.kz',
    },  # Ошибочный email (нет знака @)
    {
        'name': 'Aliya',
        'group': 'IS-24-03',
        'score': 87,
        'attendance': 79,
        'email': 'aliya@atu.edu.kz',
    },
    {
        'name': 'Arman',
        'group': 'IS-24-03',
        'score': 55,
        'attendance': 72,
        'email': 'arman@atu.edu.kz',
    },
]

# Создание базы данных в оперативной памяти и загрузка данных
connection = sqlite3.connect(':memory:')
cursor = connection.cursor()

cursor.execute("""
    CREATE TABLE students (
        name TEXT NOT NULL,
        group_name TEXT NOT NULL,
        score INTEGER NOT NULL,
        attendance INTEGER NOT NULL,
        email TEXT NOT NULL
    )
""")

rows = [
    (s['name'], s['group'], s['score'], s['attendance'], s['email'])
    for s in students
]
cursor.executemany('INSERT INTO students VALUES (?, ?, ?, ?, ?)', rows)
connection.commit()

print('=== ИНДИВИДУАЛЬНЫЙ ВАРИАНТ №7: ПРОВЕРКА ДАННЫХ ===')

# Условие 1 и 2: Получить все записи из базы данных и найти ошибочные email
query_all = """
    SELECT name, group_name, score, attendance, email
    FROM students
"""
all_students = cursor.execute(query_all).fetchall()

email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

print('Общий список всех студентов из базы:')
for s in all_students:
  print(
      f' - {s[0]} ({s[1]}): балл = {s[2]}, посещаемость = {s[3]}%, email ='
      f' {s[4]}'
  )

# Декларативная фильтрация ошибочных email с формированием списка исправлений
corrections_list = []
for name, group_name, score, attendance, email in all_students:
  if not re.fullmatch(email_pattern, email):
    # Предлагаем вариант исправления (например, заменяем '_at_' на '@')
    suggested_email = email.replace('_at_', '@')
    corrections_list.append({
        'name': name,
        'group': group_name,
        'invalid_email': email,
        'suggested_email': (
            suggested_email
            if re.fullmatch(email_pattern, suggested_email)
            else email + '@atu.edu.kz'
        ),
    })

print('\n--- Результат проверки данных ---')
if corrections_list:
  print(f'Обнаружено ошибок в email: {len(corrections_list)}')
  print('\nСписок сформированных исправлений:')
  for item in corrections_list:
    print(f" Студент: {item['name']} (группа {item['group']})")
    print(f"   Ошибочный email:   {item['invalid_email']}")
    print(f"   Рекомендуемый исх: {item['suggested_email']}")
else:
  print('Ошибочных email-адресов не обнаружено. Все данные корректны.')

connection.close()