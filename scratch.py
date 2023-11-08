import requests
from fake_useragent import UserAgent
import json
import telebot
import time

# Initialize the bot
bot = telebot.TeleBot('6299712350:AAExbr_GuH68xou3M8QjyfhWN713GuFpU24')

# Global variables for tracking the parsing process and output
min_price = None
max_price = None
data_collected = False
stop_output = False  # Flag to control continuous element output

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton("Set Min Price")
    item2 = telebot.types.KeyboardButton("Set Max Price")
    item3 = telebot.types.KeyboardButton("Start Parsing")
    item4 = telebot.types.KeyboardButton("Stop Output")  # Add a button to stop output
    markup.row(item1, item2)
    markup.row(item3)
    markup.row(item4)
    bot.send_message(message.chat.id, "Hello, user!", reply_markup=markup)
    bot.send_message(message.chat.id, "You can set min and max prices, start parsing, or stop continuous output.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global min_price, max_price, data_collected, stop_output

    if message.text == "Set Min Price":
        bot.send_message(message.chat.id, "Please enter the minimum price:")
    elif message.text == "Set Max Price":
        bot.send_message(message.chat.id, "Please enter the maximum price:")
    elif message.text.isdigit():
        if min_price is None:
            min_price = int(message.text)
            bot.send_message(message.chat.id, f"Minimum price set to {min_price}.")
        elif max_price is None:
            max_price = int(message.text)
            bot.send_message(message.chat.id, f"Maximum price set to {max_price}.")
    elif message.text == "Start Parsing":
        if min_price is not None and max_price is not None:
            if not data_collected:
                collect_data()
                data_collected = True
                with open('result.json', 'r') as file:
                    data = json.load(file)
                filtered_data = [item for item in data if min_price <= item["Pricing"] <= max_price]
                for item in filtered_data:
                    if not stop_output:
                        bot.send_message(message.chat.id, f"Full name: {item['Full name']}\nPricing: {item['Pricing']}\nDiscount: {item['Discount']}")
                        time.sleep(1)
                    else:
                        bot.send_message(message.chat.id, "Continuous output has been stopped.")
                        break
                if not filtered_data:
                    bot.send_message(message.chat.id, "No items found in the specified price range.")
            else:
                bot.send_message(message.chat.id, "Data has already been collected.")
        else:
            bot.send_message(message.chat.id, "Please set both min and max prices before starting parsing.")
    elif message.text == "Stop Output":
        if data_collected:
            stop_output = True
            bot.send_message(message.chat.id, "Continuous output has been stopped.")
        else:
            bot.send_message(message.chat.id, "Parsing has not started yet.")

def collect_data():
    ua = UserAgent()
    offset = 0
    page_size = 60
    result = []
    count = 0
    error_count = 0
    usermin = min_price
    usermax = max_price

    while True:
        url = f"https://cs.money/1.0/market/sell-orders?limit=60&offset={offset}&maxPrice={usermax}&minPrice={usermin}"
        response = requests.get(
            url=url,
            headers={'User-Agent': ua.random}
        )

        offset += page_size

        if response.status_code != 200:
            error_count += 1
            if error_count == 3:
                print("Data collection failed.")
                break
            else:
                print(f"Error {error_count}: Request failed. Retrying...")
                continue

        data = response.json()

        if "items" not in data:
            print("No more data available.")
            break

        items = data["items"]

        for item in items:
            if "pricing" in item and item["pricing"]["discount"] > 0.13:
                name = item["asset"]["names"]["short"]
                price = item["pricing"]["computed"]
                discount = item["pricing"]["discount"]
                result.append(
                    {
                        "Full name": name,
                        "Pricing": price,
                        "Discount": discount
                    }
                )

        count += 1
        print(f'Page #{count}')
        print(url)

    result.sort(key=lambda x: x["Discount"], reverse=True)
    name_dict = {}
    for item in result:
        full_name = item["Full name"]
        if full_name in name_dict:
            name_dict[full_name].append(item)
        else:
            name_dict[full_name] = [item]

    final_result = []
    for full_name, items in name_dict.items():
        items.sort(key=lambda x: x["Discount"], reverse=True)
        final_result.extend(items[:3])

    if len(final_result) > 0:
        with open('result.json', 'w') as file:
            json.dump(final_result, file, indent=4, ensure_ascii=True)
    print("Data collection and sorting ended.")

def main():
    collect_data()

if __name__ == '__main__':
    bot.polling(none_stop=True)
