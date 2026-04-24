# Autore: Federico Sabbatani

import os
from dotenv import load_dotenv

# Costanti Globali -----------------------------------------------------------------------------------------------------

# Caricamento delle Variabili d'Ambiente dal File .env
load_dotenv()

# Ottenere le Variabili d'Ambiente

# Token del Bot
BOT_TOKEN = os.getenv('BOT_TOKEN')

# ID della Chat del Mio Account Telegram
# Chat ID di Default Se _CHAT_ID NON Impostato
MY_CHAT_ID = os.getenv('MY_CHAT_ID')

# ID della Chat del Gruppo che Funge da DB Visivo
DB_CHAT_ID = os.getenv('DB_CHAT_ID')

# Codice di Autenticazione
AUTH_CODE = os.getenv('AUTH_CODE')

# Nome del File del Database
DB_FILE_NAME = os.getenv('DB_FILE_NAME')

# Lista Comandi
CMD_LIST = ['start', 'auth', 'help', 'print', 'print_all', 'add', 'delete', 'delete_all', 'words_count', 'words_list', 'num_synon', 'import_words', 'export_words','clear', 'shutdown']

# Dizionario dei Tipi Supportati per le Impostazioni (chiave: funzione)
SUPPORTED_SETTING_TYPES = {
    'int': int,
    'str': str,
    'bool': lambda x: x == 'True'
}

# Numero di Default di Sinonimi da Mostrare
DEFAULT_NUM_SYNON = 3

# Massimo Numero di Sinonimi da Mostrare
MAX_NUM_SYNON = 10

# ID della Chat dell'Account Telegram che Esegue il Bot
# DA IMPOSTARE DAL CHIAMANTE DEL BOT NEL COMANDO /start
_CHAT_ID = None

# Ottenere _CHAT_ID
def get_chat_id():
    if _CHAT_ID is None:
        raise ValueError('Chat ID NON Impostato')
    return str(_CHAT_ID)

# Impostare _CHAT_ID
def set_chat_id(chat_id):
    global _CHAT_ID
    _CHAT_ID = str(chat_id)