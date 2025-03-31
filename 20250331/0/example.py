import time

text = input("Введите текст для анализа: ")

words = text.split()
chars = len(text)
letters = sum(c.isalpha() for c in text)
digits = sum(c.isdigit() for c in text)
spaces = sum(c.isspace() for c in text)

print("\nРезультаты анализа:")
print(f"Слов: {len(words)}")
print(f"Символов (всего): {chars}")
print(f"Букв: {letters}")
print(f"Цифр: {digits}")
print(f"Пробелов: {spaces}")
