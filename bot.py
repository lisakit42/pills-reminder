import telebot
from telebot import types
import threading
import time
import datetime

TOKEN = "8049915801:AAGZ3vtyN8YIM6euzEe_j1gENP-8c5dBd-0"

bot = telebot.TeleBot(TOKEN)
user_times = {}  # {chat_id: [список выбранных часов]}


@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    user_times[chat_id] = []
    markup = types.InlineKeyboardMarkup(row_width=2)

    btn_10 = types.InlineKeyboardButton("10:00", callback_data="time_10")
    btn_14 = types.InlineKeyboardButton("14:00", callback_data="time_14")
    btn_21 = types.InlineKeyboardButton("21:00", callback_data="time_21")
    done_btn = types.InlineKeyboardButton("котик закончил выбор времени", callback_data="done")

    markup.add(btn_10, btn_14, btn_21)
    markup.add(done_btn)

    bot.send_message(
        chat_id,
        "Привет, котик🐱\nВыбери время, в которое ты хочешь получать уведомления:",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
def select_time(call):
    chat_id = call.message.chat.id
    time_choice = call.data.split("_")[1]
    chosen = user_times.get(chat_id, [])

    if time_choice in chosen:
        chosen.remove(time_choice)
    else:
        chosen.append(time_choice)

    user_times[chat_id] = chosen

    markup = types.InlineKeyboardMarkup(row_width=2)
    for t in ["10", "14", "21"]:
        text = f"✅ {t}:00" if t in chosen else f"{t}:00"
        markup.add(types.InlineKeyboardButton(text, callback_data=f"time_{t}"))
    markup.add(types.InlineKeyboardButton("котик закончил выбор времени", callback_data="done"))

    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "done")
def finish_selection(call):
    chat_id = call.message.chat.id
    chosen = user_times.get(chat_id, [])

    if chosen:
        chosen_str = ", ".join(f"{t}:00" for t in sorted(chosen))
        bot.edit_message_text(
            f"Отлично, котик, теперь ты будешь получать уведомления в это время: {chosen_str}",
            chat_id,
            call.message.message_id
        )
    else:
        bot.answer_callback_query(call.id, "Ты не выбрал ни одно время, котик 🐾")


def reminder_loop():
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        for chat_id, times in user_times.items():
            if now[:2] in times and now.endswith(":00"):
                send_reminder(chat_id, now)
        time.sleep(60)


def send_reminder(chat_id, now):
    markup = types.InlineKeyboardMarkup()
    done_btn = types.InlineKeyboardButton("сделано", callback_data=f"done_{now}")
    markup.add(done_btn)
    bot.send_message(chat_id, "Котик, выпей таблеточку💊", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("done_"))
def pill_done(call):
    chat_id = call.message.chat.id
    time_taken = call.data.split("_")[1]
    bot.edit_message_text(f"Котик выпил таблеточку в {time_taken}", chat_id, call.message.message_id)


# запускаем поток для напоминаний
threading.Thread(target=reminder_loop, daemon=True).start()

bot.polling(none_stop=True)
