import random
import json
import os
import re

# Списки для генерации предложений
ad_keywords_ru = [
    "купить", "распродажа", "скидка", "доставка", "премиум", "новинка", "заказать", "бесплатно",
    "аниме", "шопинг", "пицца", "сериал", "гаджеты", "игры", "обувь", "одежда", "спорт",
    "фитнес", "каникулы", "отдых", "красота", "макияж", "маникюр", "авто", "техника", "еда",
    "рецепты", "доставка", "зимняя распродажа", "летняя акция", "школа", "университет", "работа",
    "коллеги", "отпуск", "туризм", "путешествия", "гарантия", "в наличии", "хит продаж",
    "распродажа обуви", "тренд сезона", "новый гаджет", "онлайн магазин", "новинка месяца",
    "лучшие цены", "прямо сейчас", "скидка недели", "доставка на дом", "оформить заказ",
    "уникальное предложение", "лучшее качество", "безопасная доставка", "легко заказать",
    "айфон", "самокат", "ноутбук", "гаджет", "умные часы", "аксессуары", "хорошие товары",
    "распродажа техники", "обновление", "скидка на технику", "новинки", "доставка электроники",
    "гаджеты года", "большие скидки", "покупки онлайн", "купить сейчас", "горячие предложения",
    "быстрая доставка", "акции недели", "новые устройства", "магазин аксессуаров", "промокоды",
    "акции выходного дня", "удобные условия", "подарочные карты", "распродажа игр", "мода",
    "модные тренды", "сезонные предложения", "уникальные скидки", "лучшие товары",
    "популярные устройства", "гаджеты для дома", "скидки выходного дня", "лучшие условия",
    "игровые ноутбуки", "компьютеры", "наушники", "тренды", "устройства", "аксессуары для телефонов",
    "школьные принадлежности", "акции для студентов", "игровая консоль", "эксклюзивные товары",
    "покупки в рассрочку", "электронные книги", "уход за кожей", "уход за волосами", "спортивные товары",
    "одежда для детей", "обувь для спорта", "инструменты", "умный дом", "подарки на праздники",
    "новогодние распродажи", "лучшие акции", "гигиена", "офисные товары", "спортивное питание",
    "аксессуары для авто", "игровые кресла", "видеокарты", "мониторы", "компьютерные мыши",
    "клавиатуры", "швейные машины", "электрические скутеры", "детские игрушки", "зимняя одежда",
    "летние аксессуары", "программы для здоровья", "программное обеспечение", "путевки"
]

profanity_keywords_ru = [
    "дурак", "идиот", "осёл", "тупица", "глупец", "паразит", "мерзавец", "лентяй", "негодяй",
    "мудак", "кретин", "тварь", "ублюдок", "шлюха", "поганец", "лох", "гнида", "шарлатан",
    "мерзавец", "сволочь", "подонок", "паразит", "тупорылый", "гадина", "жлоб", "дрянь",
    "свинья", "шакал", "мразь", "обманщик", "грубиян", "хам", "осёл", "психопат", "придурок",
    "задрот", "говнюк", "балбес", "уродец", "пьяница", "недоумок", "обормот", "чёрт", "сука",
    "мразота", "раздолбай", "жмот", "трусишка", "засранец", "бездарь", "ничтожество", "наглец",
    "жопа", "козёл", "баран", "гнида", "дрянь", "хлюпик", "сопляк", "шакал", "дерьмо",
    "паразитка", "скандалист", "хапуга", "сраный", "чмошник", "врун", "гадёныш", "подлюка",
    "засранец", "говноед", "гадёныш", "кретинка", "балабол", "идиотина", "придурь",
    "хитрожопый", "обормотка", "жмотина", "мелочь пузатая", "капризуля", "хамло", "долбоёб",
    "грязный трус", "сопляк", "мошенник", "стукач", "врун", "разгильдяй", "гадюка", "никчемный",
    "злодей", "ничтожество", "жалкий", "трусливый", "дерьмовый", "дрянной", "лицемер"
]

neutral_keywords_ru = [
    "доброе утро", "как дела", "что нового", "здравствуйте", "добрый вечер", "спокойной ночи",
    "привет", "как жизнь", "что делаешь", "какой фильм посмотреть", "как погода", "отличный день",
    "чудесный вечер", "как настроение", "хорошие новости", "тёплая погода", "всё ли в порядке",
    "приятно слышать", "удачи в работе", "хорошего отпуска", "всё отлично", "новости дня",
    "приятный вечер", "чудесный рассвет", "как выходные", "добрый день", "планы на вечер",
    "обсудим новости", "долгожданная встреча", "что в мире", "всё ли спокойно", "успехи на работе",
    "что в кино", "всё ли ладится", "встреча с друзьями", "интересная книга", "что в тренде",
    "новости погоды", "обсудим планы", "приятно общаться", "доброй ночи", "хорошего настроения",
    "выспался", "погода шепчет", "встреча на ура", "какая красивая луна", "готовимся к вечеру",
    "день рождения", "праздники на носу", "всё отлично", "спокойный день", "впереди работа",
    "время обеда", "вкусный завтрак", "вечерний чай", "приятная беседа", "как каникулы",
    "с новым годом", "поздравляю", "удача на экзамене", "удачи на собеседовании", "доброй дороги",
    "теплый вечер", "расслабляющий выходной", "отличная новость", "всё в порядке дома",
    "надеюсь на успех", "спокойной дороги", "приятного чтения", "дружеская беседа"
]

ad_keywords_us = [
    "buy", "sale", "discount", "delivery", "promotion", "deal", "store", "online", "offer",
    "bestseller", "new", "shop", "now", "fast", "worldwide", "price", "cheap", "flash sale",
    "limited offer", "exclusive deal", "easy checkout", "secure delivery", "buy 1 get 1 free",
    "order online", "best deals", "holiday sale", "gifts", "fast shipping", "electronics",
    "beauty", "fitness", "clothes", "trendy", "fashion", "kitchen", "tech", "gaming",
    "gadget", "travel", "airfare", "discount card", "seasonal sale", "holiday discount",
    "gift cards", "special event", "exclusive access", "free shipping", "best gadgets",
    "seasonal discounts", "fashion week", "home decor", "best tech deals", "beauty products",
    "summer sale", "winter sale", "electronics deals", "order now", "limited stock",
    "biggest discounts", "brand offers", "shoes sale", "kitchen appliances", "online shopping",
    "best offers", "holiday gifts", "affordable prices", "tech trends", "best quality",
    "kids toys", "home security", "smartphones", "laptops", "gift boxes", "holiday deals",
    "stylish shoes", "gaming setups", "headphones", "camera equipment", "tablets", "PC accessories",
    "travel gadgets", "healthcare devices", "home automation", "energy efficient gadgets"
]

profanity_keywords_us = [
    "fool", "idiot", "donkey", "blockhead", "dumb", "scoundrel", "lazy", "rascal", "thief",
    "drunkard", "boor", "cheater", "rude", "greedy", "liar", "coward", "trickster", "villain",
    "mean", "fake", "troublemaker", "fraudster", "hypocrite", "pessimist", "slacker", "rowdy",
    "charlatan", "ignorant", "arrogant", "loser", "complainer", "jerk", "bastard", "asshole",
    "moron", "douche", "prick", "shithead", "fucktard", "wanker", "twat", "dumbass",
    "scumbag", "motherfucker", "dickhead", "shitbag", "cockroach", "dipshit", "peabrain",
    "tosser", "douchebag", "jackass", "cretin", "numskull", "nitwit", "blockhead", "buffoon",
    "imbecile", "halfwit", "bonehead", "knucklehead", "slob", "meathead", "fartknocker",
    "asshat", "knobhead", "twit", "muppet", "pillock", "arsehole", "git", "berk"
]

neutral_keywords_us = [
    "good morning", "how are you", "what's new", "hello", "good evening", "good night",
    "have a great day", "nice to see you", "how's your health", "lovely weather", "interesting book",
    "feeling good", "plans for the weekend", "exciting movie", "pleasant conversation",
    "successful meeting", "everything is fine", "thank you", "you're welcome", "hoping for the best",
    "how's life", "it's been a while", "long time no see", "how's it going", "missed you",
    "what's up", "everything okay", "good to hear from you", "great news", "lovely day",
    "so nice to meet you", "have a wonderful evening", "all the best", "take care", "sounds good",
    "nice weather", "good vibes", "peaceful day", "rest well", "catch up soon", "lovely chat"
]

# Генерация уникальных предложений в разговорном стиле

def generate_sentence_conversational(word_list, max_length=120):
    while True:
        sentence_length = random.randint(3, 15)  # Количество слов в предложении
        words = random.sample(word_list, min(sentence_length, len(word_list)))
        sentence = " ".join(words).capitalize()
        if 3 <= len(sentence) <= max_length:
            return sentence + random.choice([".", "!", "?"])

# Генерация уникальных оскорблений на основе шаблонов

def generate_unique_profanity():
    prefixes = ["глупый", "жадный", "тупой", "наглый", "мерзкий", "ленивый"]
    roots = ["козел", "осел", "жлоб", "хам", "негодяй", "паразит", "мудак", "кретин", "тварь"]
    suffixes = ["!", "!!", "!!!"]
    return f"{random.choice(prefixes)} {random.choice(roots)}{random.choice(suffixes)}"

# Генерация уникальных объявлений

def generate_unique_ads():
    actions = ["Купите", "Закажите", "Получите"]
    offers = ["скидку 50%", "бесплатную доставку", "подарок при покупке"]
    call_to_action = ["сейчас", "сегодня", "до конца недели"]
    return f"{random.choice(actions)} {random.choice(offers)} {random.choice(call_to_action)}!"

# Создание датасетов

def create_dataset(file_path, keywords, size=1000, max_length=120, generate_unique=None):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure directories exist
    dataset = []
    for _ in range(size):
        if generate_unique and random.random() > 0.7:  # Добавление уникального контента
            dataset.append(generate_unique())
        else:
            dataset.append(generate_sentence_conversational(keywords, max_length))
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    # Папки для сохранения
    dataset_paths = {
        "ru": {
            "profanity": "./dataset/ru/profanity.json",
            "ads": "./dataset/ru/ads.json",
            "neutral": "./dataset/ru/neutral.json",
        },
        "us": {
            "profanity": "./dataset/us/profanity.json",
            "ads": "./dataset/us/ads.json",
            "neutral": "./dataset/us/neutral.json",
        },
    }

    for lang, paths in dataset_paths.items():
        print(f"Генерация датасетов для языка: {lang}")
        if lang == "ru":
            create_dataset(paths["profanity"], profanity_keywords_ru, generate_unique=generate_unique_profanity)
            create_dataset(paths["ads"], ad_keywords_ru, generate_unique=generate_unique_ads)
            create_dataset(paths["neutral"], neutral_keywords_ru)
        elif lang == "us":
            create_dataset(paths["profanity"], profanity_keywords_us, generate_unique=generate_unique_profanity)
            create_dataset(paths["ads"], ad_keywords_us, generate_unique=generate_unique_ads)
            create_dataset(paths["neutral"], neutral_keywords_us)