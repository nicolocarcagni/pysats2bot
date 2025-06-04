import os
import json
import time
import requests
import telebot

user_currency_preferences = {}
awaiting_currency_input = {}
exchange_rate_cache = {}
exchange_rate_last_update = {}
cache_duration = 15 * 60  # 15 minutes
prefs_file = "preferences.json"

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
if not bot_token:
    print("TELEGRAM_BOT_TOKEN is not set")
    exit(1)

bot = telebot.TeleBot(bot_token)


def load_preferences():
    global user_currency_preferences
    if os.path.exists(prefs_file):
        with open(prefs_file, 'r') as file:
            user_currency_preferences = json.load(file)

def save_preferences():
    with open(prefs_file, 'w') as file:
        json.dump(user_currency_preferences, file, indent=2)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "❗​ Welcome! Send me a number in sats and I'll convert it to fiat. Use /settings to set your preferred currency."
    )

@bot.message_handler(commands=['settings'])
def settings(message):
    chat_id = message.chat.id
    awaiting_currency_input[chat_id] = True
    bot.send_message(chat_id, "🪙​ Please enter your preferred fiat currency (e.g., USD, EUR, GBP):")

@bot.message_handler(func=lambda message: message.chat.id in awaiting_currency_input)
def handle_currency_input(message):
    chat_id = message.chat.id
    currency = message.text.strip().upper()

    if len(currency) != 3:
        bot.send_message(chat_id, "❌​ Invalid currency code. Use a 3-letter code like USD or EUR.")
        return

    user_currency_preferences[chat_id] = currency
    save_preferences()
    del awaiting_currency_input[chat_id]
    bot.send_message(chat_id, f"💱​ Currency preference set to: {currency}")

@bot.message_handler(func=lambda message: True)
def handle_conversion(message):
    chat_id = message.chat.id
    text = message.text

    try:
        amount_in_satoshi = int(text)
    except ValueError:
        bot.send_message(chat_id, "❌ Please send a valid number representing sats!")
        return

    currency = user_currency_preferences.get(chat_id, "USD")  # default currency
    converted_value = convert_satoshi_to_fiat(amount_in_satoshi, currency)
    response = f"{amount_in_satoshi} sats ≈ {converted_value} {currency}"
    bot.send_message(chat_id, response)

def convert_satoshi_to_fiat(satoshi, currency):
    satoshi_to_btc = 0.00000001
    btc_value = satoshi * satoshi_to_btc
    exchange_rate = get_exchange_rate(currency)
    return f"{btc_value * exchange_rate:.2f}"

def get_exchange_rate(currency):
    currency = currency.lower()

    # Check for a valid cache
    if currency in exchange_rate_cache:
        if time.time() - exchange_rate_last_update[currency] < cache_duration:
            return exchange_rate_cache[currency]

    # Otherwise, call the API
    response = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": "bitcoin", "vs_currencies": currency}
    )

    if response.status_code != 200:
        return 0.0  # Fallback to 0.0 if API call fails

    data = response.json()
    price = data.get("bitcoin", {}).get(currency)

    if price is None:
        return 0.0  # Currency not found

    # Save to cache
    exchange_rate_cache[currency] = price
    exchange_rate_last_update[currency] = time.time()

    return price

def main():
    load_preferences()
    bot.polling()

if __name__ == '__main__':
    main()
