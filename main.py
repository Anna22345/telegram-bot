import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import random
import re

TOKEN = "7817316909:AAGVK_xjG21VC1iDPvfZ-jktWqgN6WQG2_U"
bot = telebot.TeleBot(TOKEN)

# ID администратора (директора), куда будут пересылаться вопросы
ADMIN_ID = 1207597105

# Хранилище заказов (Order ID -> информация о заказе)
orders = {}

# Хранилище текущих заказов (chat_id -> данные пользователя)
user_orders = {}

# Функция для динамического приветствия
def greeting():
    hour = datetime.now().hour
    if hour < 3:
        return "🌞 Good morning!"
    elif hour < 13:
        return "🌤 Good afternoon!"
    elif hour < 17:
        return "🌆 Good evening!"
    else:
        return "🌙 Good night!"

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📖 About the Project", "🐛 Pest Catalog", "🛒 Products")
    markup.add("ℹ️ FAQ", "📞 Contact Us")
    return markup

# Словарь с продуктами
products = {
    "basic": {
        "name": "🌱 AgroGuard Basic",
        "photo": "https://thumbs.dreamstime.com/b/агрономист-владеет-планшетным-сенсорным-компьютером-в-кукурузном-152805061.jpg",
        "desc": "📌 Free access to general pest information.",
        "plans": {"Free": 0}
    },
    "pro": {
        "name": "💰 AgroGuard Pro",
        "photo": "https://st5.depositphotos.com/10539404/67437/i/450/depositphotos_674378862-stock-photo-agronomist-inspecting-soya-bean-crops.jpg",
        "desc": "📊 Advanced forecasts and recommendations.",
        "plans": {"Small farms": 50, "Large enterprises": 500}
    },
    "pestvision": {
        "name": "📊 PestVision One",
        "photo": "https://latifundist.com/media/specproject/original/00/00/520/tech-farm-111087.jpg",
        "desc": "🔍 Detailed pest forecast.",
        "plans": {"10 ha": 10, "100 ha": 100}
    },
    "api": {
        "name": "🔗 AgroShield API",
        "photo": "https://istoki.tv/upload/resize_cache/iblock/8fa/817_410_1/zdyauqzv9lrrz892b4dpx2fv8gqd39v3.webp",
        "desc": "💻 Real-time pest forecasting API.",
        "plans": {"Starter": 1000}
    }
}

# Меню товаров
def product_menu():
    markup = types.InlineKeyboardMarkup()
    for key, product in products.items():
        markup.add(types.InlineKeyboardButton(product["name"], callback_data=f"product_{key}"))
    return markup

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, f"{greeting()} Choose an option:", reply_markup=main_menu())

# Показываем товары
@bot.message_handler(func=lambda message: message.text == "🛒 Products")
def show_products(message):
    bot.send_message(message.chat.id, "📋 Select a product:", reply_markup=product_menu())

# Обработчик выбора товара
@bot.callback_query_handler(func=lambda call: call.data.startswith("product_"))
def product_callback(call):
    product_key = call.data.replace("product_", "")
    product = products[product_key]

    user_orders[call.message.chat.id] = {"product": product["name"]}

    markup = types.InlineKeyboardMarkup()
    for plan, price in product["plans"].items():
        markup.add(types.InlineKeyboardButton(f"{plan} - ${price}", callback_data=f"plan_{product_key}_{plan}_{price}"))

    bot.send_photo(call.message.chat.id, product["photo"], caption=f"{product['name']}\n{product['desc']}\nChoose a plan:", reply_markup=markup)

# Обработчик выбора плана с валидацией
@bot.callback_query_handler(func=lambda call: call.data.startswith("plan_"))
def plan_selected(call):
    try:
        _, product_key, plan_name, price = call.data.split("_")
        if not price.isdigit():
            raise ValueError("Invalid price format")
        user_orders[call.message.chat.id].update({"plan": plan_name, "price": int(price)})
        bot.send_message(call.message.chat.id, "\U0001F3E2 Enter your organization name:")
        bot.register_next_step_handler(call.message, get_organization)
    except ValueError:
        bot.send_message(call.message.chat.id, "❌ Invalid plan selection. Please choose again.")

# Получение данных
def get_organization(message):
    user_orders[message.chat.id]["organization"] = message.text
    bot.send_message(message.chat.id, "\U0001F4E9 Enter your email:")
    bot.register_next_step_handler(message, get_email)

def get_email(message):
    email_pattern = re.compile(r"^[\w.-]+@[a-zA-Z\d.-]+\.[a-zA-Z]{2,}$")

    # Если email не соответствует шаблону
    if not email_pattern.match(message.text):
        bot.send_message(message.chat.id, "❌ Invalid email format. Please enter a valid email like example@mail.com.")
        # Перерегистрируем обработчик, чтобы снова запросить email
        bot.register_next_step_handler(message, get_email) 
        return

    user_orders[message.chat.id]["email"] = message.text
    bot.send_message(message.chat.id, "\U0001F4DE Enter your phone number:")
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    phone_pattern = re.compile(r"^\+?[0-9]{10,15}$")

    # Если номер телефона не соответствует шаблону
    if not phone_pattern.match(message.text):
        bot.send_message(message.chat.id, "❌ Invalid phone number. Please enter a valid number like +79149509953.")
        # Перерегистрируем обработчик, чтобы снова запросить номер телефона
        bot.register_next_step_handler(message, get_phone)  
        return

    # Если номер телефона верный, сохраняем и идем дальше
    user_orders[message.chat.id]["phone"] = message.text
    confirm_order(message)

def confirm_order(message):
    order_id = str(random.randint(10000, 99999))
    orders[order_id] = user_orders[message.chat.id]
    orders[order_id]["order_id"] = order_id

    order = orders[order_id]
    summary = (f"\U0001F6D2 **Order Summary:**\n"
               f"🆔 **Order ID:** {order_id}\n"
               f"🛍 **Product:** {order['product']}\n"
               f"💳 **Plan:** {order['plan']}\n"
               f"🏢 **Organization:** {order['organization']}\n"
               f"📩 **Email:** {order['email']}\n"
               f"📞 **Phone:** {order['phone']}\n"
               f"💵 **Total Price:** ${order['price']}\n\n"
               "✅ Confirm order?")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ YES", callback_data=f"confirm_{order_id}"))
    markup.add(types.InlineKeyboardButton("❌ NO", callback_data="cancel_order"))

    bot.send_message(message.chat.id, summary, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def final_confirmation(call):
    order_id = call.data.split("_")[1]
    bot.send_message(call.message.chat.id, f"🎉 Your order has been placed!\n🆔 Order ID: {order_id}\n"
                                           "📦 Use /trackorder to check the status.")
    del user_orders[call.message.chat.id]

@bot.callback_query_handler(func=lambda call: call.data == "cancel_order")
def cancel_order(call):
    bot.send_message(call.message.chat.id, "❌ Order cancelled. You can start a new order anytime.")
    user_orders.pop(call.message.chat.id, None)

@bot.message_handler(commands=['trackorder'])
def ask_order_id(message):
    bot.send_message(message.chat.id, "🔍 Enter your Order ID to check the status:")

@bot.message_handler(func=lambda message: message.text.isdigit() and len(message.text) == 5)
def check_order_status(message):
    order = orders.get(message.text)
    if order:
        status = (f"📦 **Order Status:**\n"
                  f"🛍 **Product:** {order['product']}\n"
                  f"💳 **Plan:** {order['plan']}\n"
                  f"🏢 **Organization:** {order['organization']}\n"
                  f"📞 **Phone:** {order['phone']}\n"
                  f"💵 **Total Price:** ${order['price']}\n"
                  f"🚀 Status: **Processing...**")
        bot.send_message(message.chat.id, status, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ Order ID not found. Please check and try again.")

# Обработчик для отлова всех текстовых сообщений, которые не соответствуют ожидаемому формату
@bot.message_handler(func=lambda message: True)
def catch_all(message):
    # Логируем любой нераспознанный ввод
    logging.debug(f"User {message.chat.id} sent: {message.text}")
    bot.send_message(message.chat.id, "Sorry, I didn't understand that. Please follow the steps correctly.")

# Меню контактов
def contactus_button():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("📍 Share Location", request_location=True))
    markup.add(KeyboardButton("📞 Share Contact", request_contact=True))
    markup.add(KeyboardButton("⬅️ Back to Menu"))  
    return markup


# Обработчик кнопки "Contact Us"
@bot.message_handler(func=lambda message: message.text == "📞 Contact Us")
def request_location(message):
    bot.send_message(
        message.chat.id,
        "📍 Our location:\n📌 *Nevsky Prospekt, 15, Saint Petersburg*\n📞 *Phone:* +7 914 950 65 45",
        parse_mode="Markdown",
        reply_markup=contactus_button()
    )
    bot.send_location(message.chat.id, latitude=59.9342802, longitude=30.3350986)

# Обработчик локации
@bot.message_handler(content_types=['location'])
def location_handler(message):
    bot.send_message(
        message.chat.id,
        f"📍 You shared your location:\nLatitude: {message.location.latitude}\nLongitude: {message.location.longitude}"
    )
# Обработчик кнопки "Back to Menu"
@bot.message_handler(func=lambda message: message.text == "⬅️ Back to Menu")
def back_to_menu(message):
    bot.send_message(message.chat.id, "⬅ Returning to main menu...", reply_markup=main_menu())
    
# Обработчик контакта
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    bot.send_message(
        message.chat.id,
        f"📞 Thank you! We received your contact: {message.contact.phone_number}"
    )
    
# 🔥 Обработчик кнопки "📖 About the Project"
@bot.message_handler(func=lambda message: message.text == "📖 About the Project")
def about_project(message):
    try:
        text = ("🌍 **CropFort – Protecting Agriculture and Forestry from Pests!**\n\n"
                "🌾 CropFort is an innovative service for farmers, agronomists, and forestry professionals, "
                "helping to combat pests and prevent threats to crops, trees, and ecosystems.\n\n"
                "🔹 **What Can CropFort Do?**\n"
                "✅ Pest catalog with descriptions and images\n"
                "✅ Selection of solutions for plant, forest, and orchard protection\n"
                "✅ Easy request submission for pest threat forecasting\n"
                "✅ Analytics on pest threat levels\n\n"
                "🌱 **Why Choose CropFort?**\n"
                "🔬 Cutting-edge technology for agriculture and forestry protection\n"
                "📊 Data-driven analytics and forecasting\n"
                "🤝 Trusted by farmers, agronomists, and forestry experts\n\n"
                "📞 **Learn More About Us:**\n"
                "🌐 Website: [CropFort Official](https://bxb.wus.mybluehost.me/website_01066f10/)\n\n"
                "🌿 **CropFort – Protecting Nature Through Innovation!** 🚀")

        bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error: {e}")


# Словарь со всеми вредителями
Pest_Catalog= {
    "Siberian Silk Moth": {
        "latin_name": "Dendrolimus sibiricus",
        "description": "A major pest of coniferous forests in Siberia. Larvae feed on needles, weakening trees.",
        "distribution_region": "Siberia, Ural region, parts of northern Kazakhstan.",
        "photo_url": "https://pbs.twimg.com/media/FOXmo2VXEAE77kf?format=jpg&name=large"
    },
    "Large Pine Weevil": {
        "latin_name": "Hylobius abietis",
        "description": "Significant pest of pine forests, damaging young trees by feeding on bark and roots.",
        "distribution_region": "Siberia, European Russia, Northern Asia.",
        "photo_url": "https://cdn.britannica.com/30/124730-004-5FD673FA/Pine-weevil.jpg"
    },
    "Colorado Potato Beetle": {
        "latin_name": "Leptinotarsa decemlineata",
        "description": "Affects potatoes, tomatoes, and eggplants. Both larvae and adult beetles feed on leaves, reducing crop yields.",
        "distribution_region": "Widely distributed across Russia, especially in southern regions.",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/2/21/Colorado_potato_beetle.jpg"
    },
    "Onion Fly": {
        "latin_name": "Delia antiqua",
        "description": "Damages onion plants; larvae burrow into bulbs, causing rot.",
        "distribution_region": "Central Russia, Siberia, the Far East.",
        "photo_url": "https://www.nature-and-garden.com/wp-content/uploads/sites/4/2021/04/onion-fly.jpg"
    },
    "Wireworm": {
        "latin_name": "Agriotes spp.",
        "description": "Click beetle larvae damage root crops, potato tubers, and cereals.",
        "distribution_region": "Found throughout Russia.",
        "photo_url": "https://assets.gardeners.com/transform/2acaab0d-341a-4c45-9bae-33c7190d0697/5311-wireworm"
    },
    "Cabbage White Butterfly": {
        "latin_name": "Pieris brassicae",
        "description": "Caterpillars feed on cabbage leaves, leading to crop loss.",
        "distribution_region": "European Russia, Siberia.",
        "photo_url": "https://images.theconversation.com/files/562916/original/file-20231201-25-m00fvc.jpg?ixlib=rb-4.1.0&rect=0%2C247%2C3849%2C1924&q=45&auto=format&w=1356&h=668&fit=crop"
    },
    "Codling Moth": {
        "latin_name": "Cydia pomonella",
        "description": "Larvae damage apple, pear, and quince fruits by boring into them.",
        "distribution_region": "Central Russia, North Caucasus.",
        "photo_url": "https://content.ces.ncsu.edu/media/images/codling_crop_UOdy8no.jpg"
    },
    "Cherry Fruit Fly": {
        "latin_name": "Rhagoletis cerasi",
        "description": "Larvae infest cherry fruits, causing rot.",
        "distribution_region": "Central and southern Russia.",
        "photo_url": "https://extension.usu.edu/planthealth/images/factsheets/labels-archive/CherryFly.jpg"
    },
    "Cereal Aphid": {
        "latin_name": "Schizaphis graminum",
        "description": "Feeds on wheat, barley, and oats, reducing yields.",
        "distribution_region": "Widely distributed.",
        "photo_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTxSHk1kNv4D873zpptuwGdzBfmDCpcIE6PtQ&s"
    },
    "Pine Lappet Moth": {
        "latin_name": "Dendrolimus pini",
        "description": "Caterpillars feed on pine needles, weakening trees.",
        "distribution_region": "Forested areas of Russia.",
        "photo_url": "https://butterfly-conservation.org/sites/default/files/styles/large/public/2019-01/30022149698_7d20789cee_o%20%281%29.jpg?itok=gO_fA4R1"
    },
    "Apple Blossom Weevil": {
        "latin_name": "Anthonomus pomorum",
        "description": "Beetles feed on apple buds, causing them to dry out.",
        "distribution_region": "Central Russia, Volga region.",
        "photo_url": "https://media.istockphoto.com/id/1313718287/photo/anthonomus-pomorum-or-the-apple-blossom-weevil-is-a-major-pests-of-apple-trees-malus-domestica.jpg?s=612x612&w=0&k=20&c=i_U2PaeHyUe9g5ByG21C38GxkLhgjCPGGPraxSksx8o="
    },
    "May Beetle (Cockchafer)": {
        "latin_name": "Melolontha melolontha",
        "description": "Larvae damage roots of trees and crops.",
        "distribution_region": "European Russia.",
        "photo_url": "https://www.nhm.ac.uk/content/dam/nhm-www/about-us/old-news/2014/cockchafer-1160-557.jpg.thumb.1160.1160.png"
    },
    "Poplar Leaf Beetle": {
        "latin_name": "Chrysomela populi",
        "description": "Feeds on poplar leaves, weakening trees.",
        "distribution_region": "Forest-steppe zone.",
        "photo_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQXlSPksOtjfnPt46PwvFWcYPX2ZVV6sLrn_Q&s"
    },
    "Spruce Bark Beetle": {
        "latin_name": "Ips typographus",
        "description": "Larvae damage coniferous trees by burrowing under the bark.",
        "distribution_region": "Forested regions of Russia.",
        "photo_url": "https://www.waldwissen.net/assets/_processed_/e/b/csm_wsl_biologie_buchdrucker_jungkaefer_598364654f.jpeg"
    },
    "Stem Nematode": {
        "latin_name": "Ditylenchus dipsaci",
        "description": "Microscopic worms damage plant tissues, causing deformation.",
        "distribution_region": "Central and southern Russia.",
        "photo_url": "https://extension.umn.edu/sites/extension.umn.edu/files/d._dipsaci.jpg"
    },
    "Gypsy Moth": {
        "latin_name": "Lymantria dispar",
        "description": "Caterpillars feed on leaves of deciduous trees, harming forests.",
        "distribution_region": "Russian forests.",
        "photo_url": "https://butterfly-conservation.org/sites/default/files/styles/masthead/public/2018-06/19550973254_6d26ef1b7a_o.jpg?itok=6EfFEiP5"
    },
}

# Обработчик кнопки "🐛 Pest Catalog"
@bot.message_handler(func=lambda message: message.text == "🐛 Pest Catalog")
def show_pest_catalog(message):
    pest_list = "\n".join([f"🔍 {name}" for name in Pest_Catalog.keys()])

    bot.send_message(
        message.chat.id,
        f"🦗 *Pest Catalog:*\n\n{pest_list}\n\n"
        "Tap on a pest's name to get more info.",
        parse_mode="Markdown",
        reply_markup=pest_catalog_buttons()
    )

# Функция для создания Inline-кнопок с вредителями
def pest_catalog_buttons():
    keyboard = InlineKeyboardMarkup()
    for pest_name in Pest_Catalog.keys():
        keyboard.add(InlineKeyboardButton(text=f"🔍 {pest_name}", callback_data=f"pest_{pest_name}"))

    keyboard.add(InlineKeyboardButton(text="🌍 More Info on Website", url="https://bxb.wus.mybluehost.me/website_01066f10/"))
    return keyboard

# Обработчик нажатий на кнопки вредителей
@bot.callback_query_handler(func=lambda call: call.data.startswith("pest_"))
def pest_info(call):
    pest_name = call.data[5:]  # Убираем префикс "pest_"
    pest = Pest_Catalog.get(pest_name)

    if pest:
        text = f"**{pest_name}**\n\n" \
               f"🔬 *Latin Name:* {pest['latin_name']}\n" \
               f"📖 *Description:* {pest['description']}\n" \
               f"🌍 *Distribution:* {pest['distribution_region']}"

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text="🌍 More Info on Website", url="https://bxb.wus.mybluehost.me/website_01066f10/"))

        if pest.get('photo_url'):
            bot.send_photo(call.message.chat.id, pest['photo_url'], caption=text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=keyboard)

# Словарь с вопросами и ответами
faq_data = {
    "How will you get your report?": "Via email 📧\nIn your personal account on our website\nDirectly in our Telegram Bot 🤖",
    "How does your pest outbreak prediction system work?": "We use artificial intelligence to analyze weather conditions, seasonality, environmental factors, and past outbreak data to predict pest activity.",
    "What data do I need to provide to get a forecast?": "You only need to specify the location and size of your area. We automatically analyze climate and environmental conditions.",
    "What types of pests can the system predict?": "Our database covers a wide range of agricultural and forest pests, including insects, fungal infections, and rodents.",
    "Can I get information not only about outbreaks but also about control methods?": "Yes! Our system selects the most effective chemical and biological protection methods, considering weather conditions.",
    "How often is the data updated?": "We use real-time data, and forecasts are updated whenever weather conditions change or new risk factors appear.",
    "Is your service suitable for small farms?": "Absolutely! We offer the AgroGuard Basic plan, which provides essential pest information even for small farms.",
    "How can I access the API for agribusinesses?": "You can subscribe to the AgroShield API to integrate our system into your infrastructure.",
    "What are your pricing plans and payment methods?": "We offer a free basic version, one-time reports, and a subscription with extended features. Payments can be made by card, bank transfer, or subscription.",
    "Can your system be used in different regions?": "Yes, we work with global data, and our system adapts to various climate zones.",
    "How can I contact you for a consultation?": "You can reach out to us via a dedicated Telegram bot, and our specialists will assist you."
}

# Функция для очистки текста от спецсимволов, которые могут вызвать ошибку
def sanitize_text(text):
    # Заменяем пробелы на подчеркивания, удаляем спецсимволы и проверяем длину
    sanitized_text = text.replace(" ", "_").replace("?", "").replace("!", "").replace("&", "and")
    # Убедимся, что длина callback_data не превышает 64 символа
    return sanitized_text[:64]

# Обработчик кнопки FAQ
@bot.message_handler(func=lambda message: message.text == "ℹ️ FAQ")
def show_faq_menu(message):
    try:
        markup = types.InlineKeyboardMarkup()

        # Создаем кнопку для каждого вопроса из faq_data
        for index, question in enumerate(faq_data.keys()):
            # Используем индекс вместо текста вопроса для callback_data
            sanitized_question = f"faq_{index}"
            button = types.InlineKeyboardButton(question, callback_data=sanitized_question)
            markup.add(button)

        # Отправляем пользователю список вопросов
        bot.send_message(message.chat.id, "Choose a question:", reply_markup=markup)

    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error: {e}")

# Обработчик выбора вопроса
@bot.callback_query_handler(func=lambda call: call.data.startswith("faq_"))
def send_faq_answer(call):
    try:
        # Извлекаем индекс вопроса из callback_data
        index = int(call.data[4:])  # Убираем "faq_" из callback_data
        question = list(faq_data.keys())[index]
        answer = faq_data.get(question, "Sorry, I couldn't find the answer.")

        # Создаем кнопку для нового вопроса
        markup = types.InlineKeyboardMarkup()
        ask_button = types.InlineKeyboardButton("❓ Ask a Question", callback_data="ask_question")
        markup.add(ask_button)

        # Отправляем пользователю ответ на выбранный вопрос
        bot.send_message(call.message.chat.id, f"*{question}*\n\n{answer}", parse_mode="Markdown", reply_markup=markup)

    except Exception as e:
        bot.send_message(call.message.chat.id, f"⚠️ Error: {e}")

# Обработчик кнопки "Ask a Question"
@bot.callback_query_handler(func=lambda call: call.data == "ask_question")
def ask_question(call):
    bot.send_message(call.message.chat.id, "Please type your question, and we will get back to you soon! ✍️")
    bot.register_next_step_handler(call.message, forward_question_to_admin)

# Функция пересылки вопроса в личные сообщения
def forward_question_to_admin(message):
    try:
        user_info = f"📩 New question from {message.from_user.first_name} (@{message.from_user.username}):\n\n"
        bot.send_message(ADMIN_ID, user_info + message.text)
        bot.send_message(message.chat.id, "Your question has been sent! We will contact you soon. ✅")

    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error: {e}")

# Запуск бота
bot.polling(none_stop=True)
