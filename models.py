# Autore: Federico Sabbatani

import tg_ui_utils

# Classi di Modello ----------------------------------------------------------------------------------------------------

# Classe per la Rappresentazione dello Stato del Bot
# Contiene le Variabili Necessarie per Gestire lo Stato del Bot e le Interazioni
class BotState:
    def __init__(self, db_utils = None):
        # Flag per lo Stato di Autenticazione
        self.is_auth = False
        # Lista di ID dei Messaggi Inviati
        self.msg_ids = []
        # Lingua per la Ricerca della Parola
        self.search_lang = 'it'
        # Numero di Sinonimi da Mostrare (Default: 3)
        self.num_synon = 3
        # Lista delle Parole Salvate nel Database Ordinata in Ordine Alfabetico per Parola (Default: Vuota)
        self.searched_words_list = []
        # Parola Cercata
        self.word_obj_searched = None
        # Messaggio della Parola Cercata
        self.msg_word_obj_searched = None
        # Lista con il Significato della Parola Cercata
        self.meaning_word_searched = None
        # Lista di Sinonimi della Parola Cercata
        self.synonyms_word_searched = None
        # Flag per l'Esistenza di Significato
        self.there_is_meaning = False
        # Flag per l'Esistenza di Sinonimi
        self.there_are_synonyms = False
        # Flag per la Decisione Presa per il Significato
        self.mean_dec_taken = False
        # Flag per la Decisione Presa per il Significato
        self.synon_dec_taken = False
        # Flag per l'Esito della Decisione per il Significato
        self.accept_meaning = False
        # Flag per l'Esito della Decisione per i Sinonimi
        self.accept_synonyms = False
        # Parola da Cancellare
        self.word_obj_todelete = None
        # Lista delle Parole da Importare
        self.words_list_to_import = []
        # Numero di Parole Importate
        self.num_words_imported = 0
        # Flag per la Decisione Presa per le Parole da Importare Già Cercate
        self.import_dec_taken = False
        # Flag per l'Esito della Decisione per le Parole da Importare Già Cercate
        self.accept_import_words = False

        # Se il Modulo db_utils è stato Fornito, Caricamento di Impostazioni dal Database
        if db_utils is not None:
            self.num_synon = db_utils.load_setting('num_synon', on_error = print) or self.num_synon
            self.searched_words_list = db_utils.get_searched_words_list(on_error = print) or self.searched_words_list


# Classe per la Rappresentazione di una Parola
class Word:
    def __init__(self, word, lang, timestamp, meaning, synonyms):
        self.word = word
        self.lang = lang
        self.timestamp = timestamp
        self.meaning = meaning
        self.synonyms = synonyms

    def __str__(self):
        return f'{tg_ui_utils.bold_str('Parola:')} {self.word}\n{tg_ui_utils.bold_str('· Lingua:')} {self.lang}\n{tg_ui_utils.bold_str('· Data e Ora Inserimento:')} {self.timestamp}\n{tg_ui_utils.bold_str('· Significato:')} {self.meaning}\n{tg_ui_utils.bold_str('· Sinonimi:')} {self.synonyms}'

    def to_dict(self):
        return {
            'word': self.word,
            'lang': self.lang,
            'timestamp': self.timestamp,
            'meaning': self.meaning,
            'synonyms': self.synonyms
        }