# Autore: Federico Sabbatani

import json
import config, tg_ui_utils, db_utils
from models import Word

# Classe per gli Handlers dei Comandi del Bot --------------------------------------------------------------------------

class CommandHandlers:
    def __init__(self, bot_services):
        self.bot_services = bot_services
        self.bot = bot_services.bot
        self.bot_state = bot_services.bot_state


    # Gestione MSG Successivo a '/print'
    def print_word_handler(self, message):
        self.bot_state.msg_ids.append(message.message_id)

        word_obj_to_print = Word(message.text.upper(), self.bot_state.search_lang, -1, '', '')

        # Controllo se la Parola è Salvata nel Database
        if self.bot_services.word_already_saved(word_obj_to_print):
            word_obj_to_print = next(w_obj_searched for w_obj_searched in self.bot_state.searched_words_list if
                                     w_obj_searched.word == word_obj_to_print.word)
            self.bot_services.send_msg(word_obj_to_print)
        else:
            self.bot_services.send_msg(f'Parola "{word_obj_to_print.word}" Non Trovata nel Dizionario')


    # Gestione MSG Successivo a '/delete'
    def delete_word_handler(self, message):
        self.bot_state.msg_ids.append(message.message_id)

        self.bot_state.word_obj_todelete = Word(message.text.upper(), self.bot_state.search_lang, -1, '', '')

        # Controllo se la Parola è Salvata nel Database
        if self.bot_services.word_already_saved(self.bot_state.word_obj_todelete):
            continue_delete_button = tg_ui_utils.create_button('Conferma', 'continue_delete')
            stop_delete_button = tg_ui_utils.create_button('Annulla', 'stop_delete')

            keyboard = tg_ui_utils.create_keyboard([continue_delete_button, stop_delete_button])
            self.bot_services.send_msg(f'Eliminare la Parola "{self.bot_state.word_obj_todelete.word}" dal Dizionario?', reply_markup = keyboard)
        else:
            self.bot_services.send_msg(f'Parola "{self.bot_state.word_obj_todelete.word}" Non Trovata nel Dizionario')


    # Gestione MSG Successivo a '/num_synon'
    def num_synon_handler(self, message):
        self.bot_state.msg_ids.append(message.message_id)

        if not message.text.isdigit():
            self.bot_services.reply_to(message, 'Numero di Sinonimi Non Valido')
            self.bot_services.send_msg('Inserire il Nuovo Numero di Sinonimi:')
            self.bot.register_next_step_handler(message, self.num_synon_handler)
        elif int(message.text) < 0:
            self.bot_services.reply_to(message, 'Numero di Sinonimi Negativo Non Valido')
            self.bot_services.send_msg('Inserire il Nuovo Numero di Sinonimi:')
            self.bot.register_next_step_handler(message, self.num_synon_handler)
        elif int(message.text) > config.MAX_NUM_SYNON:
            self.bot_services.reply_to(message, f'Numero di Sinonimi Troppo Grande\nNumero Massimo di Sinonimi: {config.MAX_NUM_SYNON}')
            self.bot_services.send_msg('Inserire il Nuovo Numero di Sinonimi:')
            self.bot.register_next_step_handler(message, self.num_synon_handler)
        else:
            self.bot_state.num_synon = int(message.text)
            db_utils.save_setting('num_synon', self.bot_state.num_synon, on_error = self.bot_services.send_msg)
            self.bot_services.send_msg(f'Numero di Sinonimi Aggiornato a: {self.bot_state.num_synon}')


    # Gestione MSG Successivo a '/import_words'
    def import_words_handler(self, message):
        self.bot_state.msg_ids.append(message.message_id)

        # Controllo Se il Messaggio è un Documento
        if message.document:
            # Controllo Se il File è un File JSON
            if message.document.mime_type == 'application/json':
                # Scaricare il File JSON Inviato
                file_info = self.bot.get_file(message.document.file_id)
                file = self.bot.download_file(file_info.file_path)

                # Caricamento del File JSON in un Oggetto Python
                try:
                    # Ottenere il Contenuto del File JSON in un Dizionario
                    json_data = json.loads(file.decode())

                    # Controllare Se il File JSON è Vuoto
                    if not json_data:
                        self.bot_services.send_msg('File JSON Vuoto')
                        return

                    # Ottenere la Lista di Parole da Importare
                    # Costruzione dell'Oggetto Word da un Dizionario Facendo Unpacking delle Coppie Chiave-Valore e Mappando i Valori ai Parametri del Costruttore
                    # Alza Eccezione TypeError Se il Dizionario Non Contiene Tutti i Parametri Necessari per Creare un Oggetto Word o Sintassi JSON Errata
                    self.bot_state.words_list_to_import = [Word(**word_dict) for word_dict in json_data]

                    msg_text = 'Lista delle Parole da Importare:\n'
                    for word_obj in self.bot_state.words_list_to_import:
                        msg_text += f' - {word_obj.word} ({word_obj.lang})\n'
                    self.bot_services.send_msg(msg_text)

                    update_words_button = tg_ui_utils.create_button('Aggiorna Parole', 'import_words')
                    continue_import_button = tg_ui_utils.create_button('Continua Importazione', 'continue_import')

                    keyboard = tg_ui_utils.create_keyboard([update_words_button, continue_import_button])

                    self.bot_services.send_msg('In Caso di Parole Già nel Dizionario,\nImportare e Aggiornare le Parole già Cercate?',
                        reply_markup=keyboard)

                except (json.JSONDecodeError, TypeError):
                    self.bot_services.send_msg('Errore nel Caricamento del File JSON.\nControllare il Formato del File')
            else:
                self.bot_services.send_msg('File Non Valido.\nInviare un File JSON')
        else:
            self.bot_services.send_msg('Messaggio Non Valido.\nInviare un File JSON')


    # Gestione MSG Successivo a '/add'
    def add_word_handler(self, message):
        self.bot_state.msg_ids.append(message.message_id)

        self.bot_state.msg_word_obj_searched = message
        self.bot_state.word_obj_searched = Word(message.text.upper(), self.bot_state.search_lang, -1, '', '')

        if self.bot_services.word_already_saved(self.bot_state.word_obj_searched):
            self.bot_services.send_msg(tg_ui_utils.bold_str('Parola già Cercata'))
            # Ottenere la Parola già Cercata
            self.bot_services.send_msg(f'Parola nel Dizionario:\n{next(w_obj_searched for w_obj_searched in self.bot_state.searched_words_list if w_obj_searched.word == self.bot_state.word_obj_searched.word)}')

            continue_searching_button = tg_ui_utils.create_button('Continua', 'continue_searching')
            stop_searching_button = tg_ui_utils.create_button('Interrompi', 'stop_searching')

            keyboard = tg_ui_utils.create_keyboard([continue_searching_button, stop_searching_button])
            self.bot_services.send_msg('Continuare la Ricerca?', reply_markup = keyboard)
        else:
            self.bot_services.search_word(self.bot_state.msg_word_obj_searched)