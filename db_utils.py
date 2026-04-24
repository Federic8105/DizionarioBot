# Autore: Federico Sabbatani

import sqlite3
from contextlib import contextmanager
import config
from models import Word

# Funzioni di Gestione Database ----------------------------------------------------------------------------------------

# Controllo della Connessione al Database SQLite
def check_connection(conn):
    if conn is None:
        return False
    else:
        return True


# Creazione della Connessione al Database SQLite
@contextmanager
def get_new_db_connection(on_error = None):
    conn = None
    try:
        # Creazione del File DB SQLite se Non Esiste e Apertura della Connessione
        conn = sqlite3.connect(config.DB_FILE_NAME)
        # Abilitare il Write-Ahead Logging (WAL)
        conn.execute('PRAGMA journal_mode = WAL')
        # Impostare il Livello di Sincronizzazione su FULL per Garantire la Massima Sicurezza dei Dati
        conn.execute('PRAGMA synchronous = FULL')
        # Configurare la Dimensione della Cache a ~4MB per Migliorare le Prestazioni delle Query
        conn.execute('PRAGMA cache_size = -4000')
        # Impostare la Modalità di Locking su NORMAL per Evitare Blocchi Esclusivi
        conn.execute('PRAGMA locking_mode = NORMAL')
        # Utilizzare la Memoria per i File Temporanei per Velocizzare le Operazioni
        conn.execute('PRAGMA temp_store = MEMORY')

        # Sospensione dell'Esecuzione della Funzione Attuale e Restituzione della Connessione al Chiamante
        yield conn

        # Salvataggio delle Modifiche al Database
        conn.commit()

    except sqlite3.Error as e:
        if on_error:
            on_error(f'Errore nella Connessione al Database SQLite: {e}')
        yield None

    finally:
        if conn is not None:
            # Chiusura della Connessione al Database
            conn.close()


# Creazione di un Nuovo Cursore per Eseguire le Query sul Database SQLite
@contextmanager
def get_new_db_cursor(on_error = None):
    # Gestione Automatica della Chiusura e del Rollback
    with get_new_db_connection(on_error = on_error) as conn:
        if check_connection(conn):
            # Creazione del Cursore per Eseguire le Query
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                # Chiusura del Cursore
                cursor.close()
        else:
            yield None


# Creazione e Inizializzazione del Database SQLite
def create_db(on_error = None):
    try:
        with get_new_db_cursor(on_error = on_error) as cursor:
            if cursor is None:
                return

            # Creazione della Tabella "Words" Se Non Esiste Già
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL UNIQUE,
                    lang TEXT NOT NULL DEFAULT 'it',
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    meaning TEXT,
                    synonyms TEXT
                )
            ''')
            # Creazione dell'Indice per la Colonna "word" per Velocizzare le Ricerche
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_word ON Words(word)')

            # Stringa dei Tipi Supportati per le Impostazioni
            supported_setting_types_str = f"('{"', '".join(config.SUPPORTED_SETTING_TYPES.keys())}')"

            # Creazione della Tabella "Settings" Se Non Esiste Già
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS Settings (
                    setting_name TEXT PRIMARY KEY NOT NULL UNIQUE,
                    setting_value TEXT NOT NULL,
                    setting_type TEXT NOT NULL DEFAULT 'int' CHECK(setting_type IN {supported_setting_types_str})
                )
            ''')

            # Creazione dell'Indice per la Colonna "setting_name" per Velocizzare le Ricerche
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_setting_name ON Settings(setting_name)')

            # Inserimento del Valore Predefinito per il Numero di Sinonimi Se Non Esiste Già il Record
            cursor.execute('INSERT OR IGNORE INTO Settings (setting_name, setting_value, setting_type) VALUES (?, ?, ?)',
                            ('num_synon', str(config.DEFAULT_NUM_SYNON), 'int'))

    except sqlite3.Error as e:
        if on_error:
            on_error(f'Errore nella Creazione del Database SQLite: {e}')


# Ottenere Lista di Parole Salvate nel Database Ordinate in Ordine Alfabetico per Parola
def get_searched_words_list(on_error = None):
    try:
        with get_new_db_cursor(on_error = on_error) as cursor:
            if cursor is None:
                return []

            # Esecuzione della Query per Ottenere le Parole Salvate
            # Ordinamento della Lista di Parole in Ordine Alfabetico
            cursor.execute('SELECT word, lang, timestamp, meaning, synonyms FROM Words ORDER BY word')
            rows = cursor.fetchall()
            return [Word(word, lang, timestamp, meaning, synonyms) for (word, lang, timestamp, meaning, synonyms) in rows]

    except sqlite3.Error as e:
        if on_error:
            on_error(f'Errore nella Lettura del Database SQLite: {e}')
        return []


# Salvare un'Impostazione nel Database
def save_setting(setting_name, setting_value, on_error = None):
    try:
        with get_new_db_cursor(on_error = on_error) as cursor:
            if cursor is None:
                return

            # Salvare il Tipo dell'Impostazione
            setting_type = type(setting_value).__name__
            if setting_type not in config.SUPPORTED_SETTING_TYPES:
                raise ValueError(f'Tipo NON Valido per l\'Impostazione "{setting_name}": "{setting_type}".\nSupportati Solo: {list(config.SUPPORTED_SETTING_TYPES.keys())}')

            cursor.execute('REPLACE INTO Settings (setting_name, setting_value, setting_type) VALUES (?, ?, ?)',
                           (setting_name, str(setting_value), setting_type))

    except sqlite3.Error as e:
        if on_error:
            on_error(f'Errore nel Salvataggio dell\'Impostazione "{setting_name}": {e}')


# Ottenere un'Impostazione dal Database
def load_setting(setting_name, on_error = None):
    try:
        with get_new_db_cursor(on_error = on_error) as cursor:
            if cursor is None:
                return None

            cursor.execute('SELECT setting_value, setting_type FROM Settings WHERE setting_name = ?', (setting_name,))
            # Ottenere la Prima e Unica Riga della Query
            row = cursor.fetchone()
            if row:
                # Unpacking della Tupla row (Primo Elemento Asseganto a setting_value, Secondo Elemento Asseganto a setting_type)
                setting_value, setting_type = row
                # Ottenere la Funzione di Conversione dal Dizionario dei Tipi Supportati in base al Tipo dell'Impostazione
                converter = config.SUPPORTED_SETTING_TYPES.get(setting_type)

                if converter is None:
                    raise ValueError(f'Tipo NON Valido per l\'Impostazione "{setting_name}": "{setting_type}".\nSupportati Solo: {list(config.SUPPORTED_SETTING_TYPES.keys())}')
                else:
                    # Ottenere il Valore dell'Impostazione Convertito al Tipo Corretto
                    return converter(setting_value)

            else:
                raise ValueError(f'Impostazione "{setting_name}" Non Trovata nel Database')

    except sqlite3.Error as e:
        if on_error:
            on_error(f'Errore nel Caricamento dell\'Impostazione "{setting_name}": {e}')
        return None


# Inserimento di una Parola nel Database
def insert_word_db(word_obj, on_error = None):
    try:
        with get_new_db_cursor(on_error = on_error) as cursor:
            if cursor is None:
                return

            # Inserimento della Parola nel Database
            cursor.execute('INSERT INTO Words (word, lang, timestamp, meaning, synonyms) VALUES (?, ?, ?, ?, ?)',
                           (word_obj.word, word_obj.lang, word_obj.timestamp, word_obj.meaning, word_obj.synonyms))

    except sqlite3.Error as e:
        if on_error:
            on_error(f'Errore nell\'Inserimento della Parola "{word_obj.word}" nel Database SQLite: {e}')


# Aggiornamento di una Parola nel Database
def update_word_db(word_obj, on_error = None):
    try:
        with get_new_db_cursor(on_error = on_error) as cursor:
            if cursor is None:
                return

            # Aggiornamento della Parola Esistente nel Database
            cursor.execute('UPDATE Words SET lang = ?, timestamp = ?, meaning = ?, synonyms = ? WHERE word = ?',
                           (word_obj.lang, word_obj.timestamp, word_obj.meaning, word_obj.synonyms, word_obj.word))

            # Controllo Se la Parola è Stata Aggiornata
            if cursor.rowcount == 0:
                if on_error:
                    on_error(f'Errore nell\'Aggiornamento della Parola "{word_obj.word}" nel Database SQLite: Parola NON Trovata')

    except sqlite3.Error as e:
        if on_error:
            on_error(f'Errore nell\'Aggiornamento della Parola "{word_obj.word}" nel Database SQLite: {e}')


# Cancellazione di una Parola dal Database
def delete_word_db(word_obj, on_error = None):
    try:
        with get_new_db_cursor(on_error = on_error) as cursor:
            if cursor is None:
                return

            # Esecuzione della Query per Cancellare la Parola dal Database
            cursor.execute('DELETE FROM Words WHERE word = ?', (word_obj.word,))

    except sqlite3.Error as e:
        if on_error:
            on_error(f'Errore nell\'Eliminazione della Parola "{word_obj.word}" dal Database SQLite: {e}')
