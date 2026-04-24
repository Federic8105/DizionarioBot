# Autore: Federico Sabbatani

import os, io, json
from PyMultiDictionary import MultiDictionary
from datetime import datetime
import config, tg_ui_utils, db_utils

# Classe per i Servizi del Bot (Funzioni di Utilità per il Bot) --------------------------------------------------------

class BotServices:
    def __init__(self, bot, bot_state):
        self.bot = bot
        self.bot_state = bot_state
        # Inizializzazione Dizionario
        self.dictionary = MultiDictionary()


    # Inviare un Messaggio con Testo Formattato in HTML
    def send_msg(self, text, chat_id = None, reply_markup = None):
        if not chat_id:
            try:
                chat_id = config.get_chat_id()
            except ValueError:
                chat_id = config.MY_CHAT_ID

        self.bot_state.msg_ids.append(self.bot.send_message(chat_id, text, parse_mode = 'HTML', reply_markup = reply_markup).message_id)


    # Inviare una Risposta a un Messaggio con Testo Formattato in HTML
    def reply_to(self, message_to_reply, text, reply_markup = None):
        self.bot_state.msg_ids.append(self.bot.reply_to(message_to_reply, text, parse_mode = 'HTML', reply_markup = reply_markup).message_id)


    # Inviare un Documento
    def send_document(self, file, chat_id = None):
        if not chat_id:
            try:
                chat_id = config.get_chat_id()
            except ValueError:
                chat_id = config.MY_CHAT_ID

        # Controllo Se è un File Virtuale (BytesIO)
        if isinstance(file, io.BytesIO):
            if file.getbuffer().nbytes == 0:
                raise ValueError('File Virtuale Vuoto')
            # Controllare Se il File Virtuale ha un Nome
            if not hasattr(file, 'name'):
                # Assegnare un Nome Predefinito Generico
                file.name = 'unknown_document.json'

            # Impostare la Posizione del Puntatore del File Virtuale all'Inizio per Assicurare che il Contenuto sia Inviato per Intero
            file.seek(0)
            self.bot_state.msg_ids.append(self.bot.send_document(chat_id, file).message_id)

        # Se file è un Percorso a un File Fisico
        elif isinstance(file, str):
            # Controllo Se il File è un Percorso a un File Fisico Valido
            if not os.path.exists(file):
                raise FileNotFoundError(f'Il File "{file}" NON Esiste')
            with open(file, 'rb') as f:
                self.bot_state.msg_ids.append(self.bot.send_document(chat_id, f).message_id)

        # Se file Non è un Percorso a un File Fisico o un Oggetto BytesIO
        else:
            raise TypeError("Parametro 'file' Deve Essere un Percorso (str) o un Oggetto BytesIO")


    # Controllare Se il Chat ID dell'Utente che Esegue il Bot Corrisponde a MY_CHAT_ID
    # Ritorna True Se il Chat ID è Corretto, Altrimenti Invia un Messaggio di Avviso e Ritorna False
    def check_chat_id(self, current_chat_id):
        if config.MY_CHAT_ID != current_chat_id:
            self.send_msg(
                f'{tg_ui_utils.bold_str('!! - ATTENZIONE - !!')}\nQualcun Altro Sta Usando il Bot da un Chat ID Diverso!\nChat_ID: {config.get_chat_id()}',
                chat_id=config.MY_CHAT_ID)
            return False
        return True


    def check_auth(self, message):
        if self.bot_state.is_auth is False:
            self.send_msg('Inserire il Codice di Autenticazione:')

            # Registrazione del Gestore per MSG Successivo a check_auth
            self.bot.register_next_step_handler(message, self.check_auth_handler)
            return None
        else:
            self.send_msg('Autenticazione già Effettuata')
            return True


    # Gestione MSG Successivo a check_auth
    def check_auth_handler(self, message):
        self.bot_state.msg_ids.append(message.message_id)

        if message.text == config.AUTH_CODE:
            self.bot_state.is_auth = True
            self.send_msg('Autenticazione Effettuata con Successo')
        else:
            self.send_msg('Codice di Autenticazione Errato')
            self.check_auth(message)


    # Controllo se la Parola è già Stata Salvata nel Database
    def word_already_saved(self, word_obj):
        if any(searched_word.word == word_obj.word for searched_word in self.bot_state.searched_words_list):
            return True
        else:
            return False


    # Salvataggio della Parola nel Database
    def save(self, word_obj):
        # Inserimento Timestamp Attuale alla Parola da Salvare nel Databse
        word_obj.timestamp = datetime.now().strftime('%d-%m-%Y %H:%M')

        # Controllo se la Parola è già Presente nella Lista di Parole Cercate (Aggiornamento della Parola già Salvata)
        if self.word_already_saved(word_obj):
            db_utils.update_word_db(word_obj, on_error = self.send_msg)
            # Eliminazione della Parola Già Cercata dalla Lista di Parole Cercate
            self.bot_state.searched_words_list.remove(next(w_obj_searched for w_obj_searched in self.bot_state.searched_words_list if w_obj_searched.word == word_obj.word))
        else:
            db_utils.insert_word_db(word_obj, on_error = self.send_msg)

        # Aggiunta della Parola alla Lista di Parole Cercate
        self.bot_state.searched_words_list.append(word_obj)

        # Ordinamento della Lista di Parole Cercate in Ordine Alfabetico
        self.bot_state.searched_words_list.sort(key = lambda w_obj: w_obj.word)
        # Eliminazione della Parola Cercata Attualmente dallo Stato del Bot
        self.bot_state.word_obj_searched = None
        self.send_msg(f'Parola "{word_obj.word}" Salvata nel Dizionario')


    # Cancellazione della Parola dal Database
    def delete(self, word_obj):
        db_utils.delete_word_db(word_obj, on_error = self.send_msg)
        # Rimozione della Parola dalla Lista di Parole Cercate
        self.bot_state.searched_words_list.remove(next(w_obj_searched for w_obj_searched in self.bot_state.searched_words_list if w_obj_searched.word == word_obj.word))
        self.send_msg(f'Parola "{word_obj.word}" Eliminata dal Dizionario')


    # Ricerca della Parola
    def search_word(self, msg_word_searched):
        self.search_meaning(msg_word_searched, self.bot_state.word_obj_searched)
        self.search_synonyms(msg_word_searched, self.bot_state.word_obj_searched)

        # Controllo se Non ci Sono Sinonimi e Non c'è Significato
        if not self.bot_state.there_is_meaning and not self.bot_state.there_are_synonyms:
            save_nonexistent_word_button = tg_ui_utils.create_button('Salvare', 'save_nonexistent_word')
            refuse_nonexistent_word_button = tg_ui_utils.create_button('Non Salvare', 'refuse_nonexistent_word')

            keyboard = tg_ui_utils.create_keyboard([save_nonexistent_word_button, refuse_nonexistent_word_button])
            self.send_msg(f'Salvare Comunque la Parola Inesistente "{self.bot_state.word_obj_searched.word}" nel Dizionario?', reply_markup = keyboard)


    # Ricerca del Significato di una Parola
    def search_meaning(self, message, word_obj):
        self.reply_to(message, 'Cercando il Significato della Parola...')

        self.bot_state.meaning_word_searched = self.dictionary.meaning(self.bot_state.search_lang, word_obj.word)

        # Controllo se tutti gli Elementi della Tupla "meaning" sono Vuoti
        if all(not element for element in self.bot_state.meaning_word_searched):
            self.bot_state.there_is_meaning = False
            self.bot_state.accept_meaning = True
            self.bot_state.meaning_word_searched = ''
            self.reply_to(message, 'Significato Non Trovato')
        else:
            self.bot_state.there_is_meaning = True

            # Convertire la Lista in una Stringa
            self.bot_state.meaning_word_searched = ', '.join(str(item) for item in self.bot_state.meaning_word_searched)

            self.reply_to(message, f'Significato della Parola "{word_obj.word}":\n{self.bot_state.meaning_word_searched}')

            accept_mean_button = tg_ui_utils.create_button('Salvare', 'accept_meaning')
            refuse_mean_button = tg_ui_utils.create_button('Non Salvare', 'refuse_meaning')

            keyboard = tg_ui_utils.create_keyboard([accept_mean_button, refuse_mean_button])
            self.send_msg('Salvare il Significato nel Dizionario?', reply_markup = keyboard)


    # Ricerca dei Sinonimi di una Parola
    def search_synonyms(self, message, word_obj):
        # Controllo se il Numero di Sinonimi da Mostrare è 0
        if self.bot_state.num_synon == 0:
            self.bot_state.there_are_synonyms = False
            return

        self.reply_to(message, 'Cercando i Sinonimi della Parola...')

        self.bot_state.synonyms_word_searched = self.dictionary.synonym(self.bot_state.search_lang, word_obj.word)

        if not self.bot_state.synonyms_word_searched:
            self.bot_state.there_are_synonyms = False
            self.bot_state.accept_synonyms = True
            self.bot_state.synonyms_word_searched = ''
            self.reply_to(message, 'Sinonimi Non Trovati')
        else:
            self.bot_state.there_are_synonyms = True

            # Convertire la Lista in una Stringa
            self.bot_state.synonyms_word_searched = ', '.join(self.bot_state.synonyms_word_searched[:self.bot_state.num_synon])

            self. reply_to(message, f'{self.bot_state.num_synon} Sinonimi della Parola "{word_obj.word}":\n{self.bot_state.synonyms_word_searched}')

            accept_synon_button = tg_ui_utils.create_button('Salvare', 'accept_synonyms')
            refuse_synon_button = tg_ui_utils.create_button('Non Salvare', 'refuse_synonyms')

            keyboard = tg_ui_utils.create_keyboard([accept_synon_button, refuse_synon_button])
            self.send_msg('Salvare i Sinonimi nel Dizionario?', reply_markup = keyboard)


    # Importazione delle Parole nel Dizionario
    def import_words(self, update_words):
        self.bot_state.num_words_imported = 0

        for word_obj_to_import in self.bot_state.words_list_to_import:

            if self.word_already_saved(word_obj_to_import):
                if update_words:
                    # Aggiornamento della Parola già Cercata
                    db_utils.update_word_db(word_obj_to_import, on_error = self.send_msg)
                    # Ottenere la Parola già Cercata
                    word_obj_already_searched = next(
                        w_obj_searched for w_obj_searched in self.bot_state.searched_words_list if
                        w_obj_searched.word == word_obj_to_import.word)
                    # Eliminazione della Parola Già Cercata dalla Lista di Parole Cercate
                    self.bot_state.searched_words_list.remove(word_obj_already_searched)
                    # Aggiunta della Parola Importata alla Lista di Parole Cercate
                    self.bot_state.searched_words_list.append(word_obj_to_import)
                    self.bot_state.num_words_imported += 1
                    self.send_msg(
                        f'Parola "{word_obj_to_import.word}" Già Cercata.\n\nParola Importata:\n{word_obj_to_import}\n\nParola nel Dizionario Sovrascritta:\n{word_obj_already_searched}')
            else:
                # Inserimento della Parola nel Database
                db_utils.insert_word_db(word_obj_to_import, on_error = self.send_msg)
                # Aggiunta della Parola alla Lista di Parole Cercate
                self.bot_state.searched_words_list.append(word_obj_to_import)
                self.bot_state.num_words_imported += 1

        self.send_msg(f'Parole Importate: {self.bot_state.num_words_imported}/{len(self.bot_state.words_list_to_import)}')


    # Creare un File JSON con le Parole Salvate nel Dizionario (No Salvataggio sul Disco)
    def create_export_json(self):
        # Nome del File JSON da Esportare con Data e Ora Corrente
        json_file_name = f'exported_words-{datetime.now().strftime('%d-%m-%Y_%H-%M')}.json'
        # Creazione del File JSON Virtuale in Memoria
        buffer = io.BytesIO()
        # Convertire la Lista di Parole in un Oggetto JSON
        json_data = json.dumps([word.to_dict() for word in self.bot_state.searched_words_list], indent=4, ensure_ascii=False)
        # Scrivere i Dati in JSON nel Buffer
        buffer.write(json_data.encode())
        # Impostare la Posizione del Puntatore del File Virtuale all'Inizio
        buffer.seek(0)
        buffer.name = json_file_name
        return buffer