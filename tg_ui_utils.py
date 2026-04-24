# Autore: Federico Sabbatani

from telebot import types
import config

# Funzioni di Utilità per UI Telegram ----------------------------------------------------------------------------------

# Ottenere la Stringa in Grassetto in HTML
def bold_str(text):
    return f'<b>{text}</b>'

# Creazione di un Pulsante
def create_button(text, callback_data):
    return types.InlineKeyboardButton(text = text, callback_data = callback_data)

# Creazione di una Tastiera con Pulsanti
def create_keyboard(buttons):
    keyboard = types.InlineKeyboardMarkup()
    for button in buttons:
        keyboard.add(button)
    return keyboard


# Eliminazione della Tastiera Associata al Messaggio (per Rimuovere i Pulsanti)
def delete_keyboard(bot, msg_id):
    bot.edit_message_reply_markup(chat_id = config.get_chat_id(), message_id = msg_id)


# Cancellazione della Lista di Messaggi Inviati nella Sessione Corrente per ID
def delete_msgs(bot, msg_ids):
    bot.delete_messages(config.get_chat_id(), msg_ids)