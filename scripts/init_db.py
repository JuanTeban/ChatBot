from langchain_community.chat_message_histories import SQLChatMessageHistory
from src.core.config import settings

def initialize_database():
    """
    Crea la tabla 'message_store' en la base de datos SQLite si no existe.
    
    Al instanciar SQLChatMessageHistory en un script síncrono, su constructor
    se encarga de crear la tabla de forma segura sin conflictos asíncronos.
    """
    print("Initializing database...")
    
    # Creamos una instancia con un ID de sesión temporal.
    # Esto es suficiente para que el constructor cree la tabla.
    SQLChatMessageHistory(
        session_id="initialization_session",
        connection_string=f"sqlite:///{settings.SQLITE_DB_PATH}"
    )
    
    print(f"Database table 'message_store' checked/created in '{settings.SQLITE_DB_PATH}'")

if __name__ == "__main__":
    initialize_database()
