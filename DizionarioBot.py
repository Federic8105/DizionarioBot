# Autore: Federico Sabbatani
# Titolo Bot: DizionarioBot
# Descrizione: Bot Telegram per la Gestione di un Dizionario Personale Online
# Versione 4.0
# Data: 23-04-2025

# TODO: async, webhook, decoratori, insert or replace, clear esplode con tanti messaggi, eliminare parte in inglese di significato, print in altro posto, documentazione
# TODO X Versioni di Python Future: Controllo Uso di With con Cursor

import telebot
import config, tg_ui_utils, db_utils
from models import BotState
from bot_utils import BotServices
from command_handlers import CommandHandlers

# Creazione Bot Telegram -----------------------------------------------------------------------------------------------

# Inizializzazione Bot
bot = telebot.TeleBot(config.BOT_TOKEN)

# Inizializzazione del Database SQLite
db_utils.create_db(on_error = print)

# Creazione dello Stato del Bot con Caricamento delle Impostazioni dal Database
bot_state = BotState(db_utils)

# Creazione dei Servizi del Bot (Funzioni di Utilità per il Bot)
bot_services = BotServices(bot, bot_state)

# Creazione degli Handlers dei Comandi del Bot
command_handlers = CommandHandlers(bot_services)

# Funzioni di Gestione Bot ---------------------------------------------------------------------------------------------

# Gestore dei Comandi del Bot
@bot.message_handler(func = lambda message: True)
def msg_handler(message):
    # Aggiungere ID del Messaggio alla Lista di ID dei Messaggi Inviati
    bot_state.msg_ids.append(message.message_id)

    # Controllare Se il Messaggio è Testo
    if not message.text:
        bot_services.reply_to(message, 'Usa /help per la Lista dei Comandi')
    else:
        # Controllare Se il Messaggio Inizia con un Commando (Testo che Inizia con '/')
        if message.text.startswith('/'):
            command = message.text
            match command:
                case '/start':
                    # Impostare il Chat ID dell'Utente che Esegue il Bot
                    config.set_chat_id(message.chat.id)

                    if bot_services.check_chat_id(config.get_chat_id()):
                        bot_services.send_msg(tg_ui_utils.bold_str('!! - Benvenuto su DizionarioBot - !!'))
                        bot_services.check_auth(message)

                case '/auth':
                    config.set_chat_id(message.chat.id)

                    if bot_services.check_chat_id(config.get_chat_id()):
                        bot_services.check_auth(message)

                case '/help':
                    config.set_chat_id(message.chat.id)

                    if bot_services.check_chat_id(config.get_chat_id()):
                        msg_str = 'Lista Comandi:\n'
                        for cmd in config.CMD_LIST:
                            msg_str += f'/{cmd}\n'
                        bot_services.send_msg(msg_str)

                case '/print':
                    if bot_state.is_auth:
                        if not bot_state.searched_words_list:
                            bot_services.send_msg('Nessuna Parola Salvata nel Dizionario')
                        else:
                            bot_services.send_msg('Lista delle Parole Salvate nel Dizionario:')
                            # Ordinamento della Lista di Parole in Ordine Alfabetico
                            bot_state.searched_words_list.sort(key=lambda w_obj: w_obj.word)
                            for word in bot_state.searched_words_list:
                                bot_services.send_msg(f'- {word.word} ({word.lang})')

                            bot_services.send_msg('Inserire la Parola da Stampare:')
                            bot.register_next_step_handler(message, command_handlers.print_word_handler)
                    else:
                        bot_services.send_msg(f'{tg_ui_utils.bold_str('Autenticazione Richiesta.')}\nUsa /auth per Autenticarsi')

                case '/print_all':
                    if bot_state.is_auth:
                        if not bot_state.searched_words_list:
                            bot_services.send_msg('Nessuna Parola Salvata nel Dizionario')
                        else:
                            bot_services.send_msg('Parole Salvate nel Dizionario:')
                            # Ordinamento della Lista di Parole in Ordine Alfabetico
                            bot_state.searched_words_list.sort(key=lambda w_obj: w_obj.word)
                            for word in bot_state.searched_words_list:
                                bot_services.send_msg(word)
                    else:
                        bot_services.send_msg(f'{tg_ui_utils.bold_str('Autenticazione Richiesta.')}\nUsa /auth per Autenticarsi')

                case '/add':
                    if bot_state.is_auth:
                        if bot_state.word_obj_searched is not None:
                            bot_services.send_msg(f'{tg_ui_utils.bold_str('!! - Attenzione - !!')}')
                            bot_services.send_msg(f'La Parola "{bot_state.word_obj_searched.word}" è in Attesa di Salvataggio nel Dizionario.\n\nScegliere le Opzioni di Salvataggio Rimanenti per la Parola')
                        else:
                            bot_services.send_msg('Inserire la Parola da Cercare:')
                            # Registrazione del Gestore per MSG Successivo a '/add'
                            bot.register_next_step_handler(message, command_handlers.add_word_handler)
                    else:
                        bot_services.send_msg(f'{tg_ui_utils.bold_str('Autenticazione Richiesta.')}\nUsa /auth per Autenticarsi')

                case '/delete':
                    if bot_state.is_auth:
                        if not bot_state.searched_words_list:
                            bot_services.send_msg('Nessuna Parola Salvata nel Dizionario')
                        else:
                            bot_services.send_msg('Lista delle Parole Salvate nel Dizionario:')
                            # Ordinamento della Lista di Parole in Ordine Alfabetico
                            bot_state.searched_words_list.sort(key = lambda w_obj: w_obj.word)
                            for word in bot_state.searched_words_list:
                                bot_services.send_msg(f'- {word.word} ({word.lang})')

                            bot_services.send_msg('Inserire la Parola da Eliminare:')
                            bot.register_next_step_handler(message, command_handlers.delete_word_handler)
                    else:
                        bot_services.send_msg(f'{tg_ui_utils.bold_str('Autenticazione Richiesta.')}\nUsa /auth per Autenticarsi')

                case '/delete_all':
                    if bot_state.is_auth:
                        if not bot_state.searched_words_list:
                            bot_services.send_msg('Nessuna Parola Salvata nel Dizionario')
                        else:
                            continue_delete_all_button = tg_ui_utils.create_button('Conferma', 'continue_delete_all')
                            stop_delete_all_button = tg_ui_utils.create_button('Annulla', 'stop_delete_all')

                            keyboard = tg_ui_utils.create_keyboard([continue_delete_all_button, stop_delete_all_button])
                            bot_services.send_msg(f'Eliminare {tg_ui_utils.bold_str('TUTTO')} il Dizionario?', reply_markup = keyboard)
                    else:
                        bot_services.send_msg(f'{tg_ui_utils.bold_str('Autenticazione Richiesta.')}\nUsa /auth per Autenticarsi')

                case '/words_count':
                    if bot_state.is_auth:
                        bot_services.send_msg(f'Numero di Parole Salvate nel Dizionario: {len(bot_state.searched_words_list)}')
                    else:
                        bot_services.send_msg(f'{tg_ui_utils.bold_str('Autenticazione Richiesta.')}\nUsa /auth per Autenticarsi')

                case '/words_list':
                    if bot_state.is_auth:
                        if not bot_state.searched_words_list:
                            bot_services.send_msg('Nessuna Parola Salvata nel Dizionario')
                        else:
                            bot_services.send_msg('Lista delle Parole Salvate nel Dizionario:')
                            # Ordinamento della Lista di Parole in Ordine Alfabetico
                            bot_state.searched_words_list.sort(key = lambda w_obj: w_obj.word)
                            for word in bot_state.searched_words_list:
                                bot_services.send_msg(f'- {word.word} ({word.lang})')
                            bot_services.send_msg(f'Numero di Parole Salvate: {len(bot_state.searched_words_list)}')
                    else:
                        bot_services.send_msg(f'{tg_ui_utils.bold_str('Autenticazione Richiesta.')}\nUsa /auth per Autenticarsi')

                case '/num_synon':
                    if bot_state.is_auth:
                        bot_services.send_msg(f'Numero Attuale di Sinonimi da Mostrare (Se Presenti): {bot_state.num_synon}')
                        bot_services.send_msg(f'Numero Massimo di Sinonimi: {config.MAX_NUM_SYNON}')

                        change_num_synon_button = tg_ui_utils.create_button('Cambia', 'change_num_synon')

                        keyboard = tg_ui_utils.create_keyboard([change_num_synon_button])
                        bot_services.send_msg('Cambiare il Numero di Sinonimi?', reply_markup = keyboard)
                    else:
                        bot_services.send_msg(f'{tg_ui_utils.bold_str('Autenticazione Richiesta.')}\nUsa /auth per Autenticarsi')

                case '/import_words':
                    if bot_state.is_auth:
                        bot_services.send_msg('Invia il File JSON con le Parole da Importare:')
                        # Registrazione del Gestore per MSG Successivo a '/import_words'
                        bot.register_next_step_handler(message, command_handlers.import_words_handler)

                    else:
                        bot_services.send_msg(f'{tg_ui_utils.bold_str('Autenticazione Richiesta.')}\nUsa /auth per Autenticarsi')

                case '/export_words':
                    if bot_state.is_auth:
                        if not bot_state.searched_words_list:
                            bot_services.send_msg('Nessuna Parola Salvata nel Dizionario')
                        else:
                            bot_services.send_msg('Esportazione delle Parole Salvate nel Dizionario in Corso...')
                            bot_services.send_document(bot_services.create_export_json())
                    else:
                        bot_services.send_msg(f'{tg_ui_utils.bold_str('Autenticazione Richiesta.')}\nUsa /auth per Autenticarsi')

                case '/clear':
                    if bot_state.is_auth:
                        bot_services.send_msg('Cancellazione dei Messaggi della Sessione Corrente in Corso...')
                        # Cancellazione dei Messaggi della Sessione Corrente
                        tg_ui_utils.delete_msgs(bot, bot_state.msg_ids)
                        # Reset della Lista dei Messaggi
                        bot_state.msg_ids = []
                    else:
                        bot_services.send_msg(f'{tg_ui_utils.bold_str('Autenticazione Richiesta.')}\nUsa /auth per Autenticarsi')

                case '/shutdown':
                    if bot_state.is_auth:
                        bot_services.send_msg('Cancellazione dei Messaggi della Sessione Corrente e\nSpegnimento del Bot in Corso...')
                        # Cancellazione dei Messaggi della Sessione Corrente
                        tg_ui_utils.delete_msgs(bot, bot_state.msg_ids)
                        # Chiusura del Bot
                        bot.stop_bot()
                    else:
                        bot_services.send_msg(f'{tg_ui_utils.bold_str('Autenticazione Richiesta.')}\nUsa /auth per Autenticarsi')

                case _:
                    bot_services.reply_to(message, f'{tg_ui_utils.bold_str('Comando Non Valido.')}\nUsa /help per la Lista dei Comandi')
        else:
            bot_services.reply_to(message, 'Usa /help per la Lista dei Comandi')


# Gestione dei CallBack dei Pulsanti
@bot.callback_query_handler(func = lambda call: True)
def callback_query(call):
    match call.data:
        case 'continue_searching':
            bot_services.search_word(bot_state.msg_word_obj_searched)
            tg_ui_utils.delete_keyboard(bot, call.message.message_id)

        case 'stop_searching':
            # Eliminazione della Parola Cercata Attualmente dallo Stato del Bot
            bot_state.word_obj_searched = None
            bot_services.send_msg('Ricerca Interrotta')
            tg_ui_utils.delete_keyboard(bot, call.message.message_id)

        case 'accept_meaning':
            if not bot_state.mean_dec_taken:
                bot_state.accept_meaning = True
                bot_state.mean_dec_taken = True
                bot_services.send_msg('Significato Accettato')
                tg_ui_utils.delete_keyboard(bot, call.message.message_id)

        case 'refuse_meaning':
            if not bot_state.mean_dec_taken:
                bot_state.mean_dec_taken = True
                bot_services.send_msg('Significato Rifiutato')
                tg_ui_utils.delete_keyboard(bot, call.message.message_id)

        case 'accept_synonyms':
            if not bot_state.synon_dec_taken:
                bot_state.accept_synonyms = True
                bot_state.synon_dec_taken = True
                bot_services.send_msg('Sinonimi Accettati')
                tg_ui_utils.delete_keyboard(bot, call.message.message_id)

        case 'refuse_synonyms':
            if not bot_state.synon_dec_taken:
                bot_state.synon_dec_taken = True
                bot_services.send_msg('Sinonimi Rifiutati')
                tg_ui_utils.delete_keyboard(bot, call.message.message_id)

        case 'save_nonexistent_word':
            bot_services.save(bot_state.word_obj_searched)
            tg_ui_utils.delete_keyboard(bot, call.message.message_id)

        case 'refuse_nonexistent_word':
            bot_services.send_msg(f'Parola Inesistente "{bot_state.word_obj_searched.word}" Non Salvata nel Dizionario')
            bot_state.word_obj_searched = None
            tg_ui_utils.delete_keyboard(bot, call.message.message_id)

        case 'continue_delete':
            bot_services.delete(bot_state.word_obj_todelete)
            bot_state.word_obj_todelete = None
            tg_ui_utils.delete_keyboard(bot, call.message.message_id)

        case 'stop_delete':
            bot_services.send_msg('Eliminazione Interrotta')
            tg_ui_utils.delete_keyboard(bot, call.message.message_id)

        case 'continue_delete_all':
            # Cancellazione di Tutte le Parole Salvate nel Database
            for word_obj in bot_state.searched_words_list:
                db_utils.delete_word_db(word_obj, on_error = bot_services.send_msg)
            # Cancellazione della Lista di Parole Cercate
            bot_state.searched_words_list.clear()
            bot_services.send_msg('Tutte le Parole Salvate nel Dizionario sono state Cancellate')
            tg_ui_utils.delete_keyboard(bot, call.message.message_id)

        case 'stop_delete_all':
            bot_services.send_msg('Eliminazione Interrotta')
            tg_ui_utils.delete_keyboard(bot, call.message.message_id)

        case 'change_num_synon':
            bot_services.send_msg('Inserire il Nuovo Numero di Sinonimi:')
            # Registrazione del Gestore per MSG Successivo a "change_num_synon" quando si Clicca sul Pulsante di Cambio
            bot.register_next_step_handler(call.message, command_handlers.num_synon_handler)
            tg_ui_utils.delete_keyboard(bot, call.message.message_id)

        case 'import_words':
            bot_state.accept_import_words = True
            bot_state.import_dec_taken = True
            tg_ui_utils.delete_keyboard(bot, call.message.message_id)

        case 'continue_import':
            bot_state.import_dec_taken = True
            tg_ui_utils.delete_keyboard(bot, call.message.message_id)

    if ((bot_state.mean_dec_taken is True and bot_state.synon_dec_taken is True) or
            (bot_state.there_is_meaning is False and bot_state.synon_dec_taken is True) or
            (bot_state.mean_dec_taken is True and bot_state.there_are_synonyms is False)):
        bot_state.mean_dec_taken = False
        bot_state.synon_dec_taken = False

        if bot_state.accept_meaning:
            bot_state.word_obj_searched.meaning = bot_state.meaning_word_searched

        if bot_state.accept_synonyms:
            bot_state.word_obj_searched.synonyms = bot_state.synonyms_word_searched

        bot_state.accept_synonyms = False
        bot_state.accept_meaning = False

        bot_services.save(bot_state.word_obj_searched)

    if bot_state.import_dec_taken:
        bot_services.import_words(bot_state.accept_import_words)

        bot_state.words_list_to_import = []
        bot_state.accept_import_words = False
        bot_state.import_dec_taken = False


# Esecuzione del Bot ---------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    bot.polling()