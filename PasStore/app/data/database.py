import sqlite3
from app.config import DB_NAME

class DatabaseManager:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. Base table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credenciales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detalle TEXT,
                acceso_host TEXT,
                puerto TEXT,
                usuario TEXT,
                password TEXT,
                rol TEXT,
                instancia_tipo TEXT,
                web TEXT,
                ip_pub TEXT
            )
        ''') 
        
        # Tabs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tabs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                color TEXT NOT NULL,
                position INTEGER DEFAULT 0
            )
        ''')

        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # 2. Migrations
        cursor.execute("PRAGMA table_info(credenciales)")
        existing_cols = [info[1] for info in cursor.fetchall()]
        
        if "tipo_acceso" not in existing_cols:
            cursor.execute("ALTER TABLE credenciales ADD COLUMN tipo_acceso TEXT")
            
        if "contiene" not in existing_cols:
            cursor.execute("ALTER TABLE credenciales ADD COLUMN contiene TEXT")

        if "tab_id" not in existing_cols:
            cursor.execute("ALTER TABLE credenciales ADD COLUMN tab_id INTEGER DEFAULT 1")

        if "ip_priv" not in existing_cols:
            cursor.execute("ALTER TABLE credenciales ADD COLUMN ip_priv TEXT")
            
        if "rol" not in existing_cols:
            cursor.execute("ALTER TABLE credenciales ADD COLUMN rol TEXT")
            
        if "row_color" not in existing_cols:
            cursor.execute("ALTER TABLE credenciales ADD COLUMN row_color TEXT")
        
        if "display_order" not in existing_cols:
            cursor.execute("ALTER TABLE credenciales ADD COLUMN display_order INTEGER DEFAULT 0")
            # Set initial order based on current ID
            cursor.execute("UPDATE credenciales SET display_order = id WHERE display_order IS NULL OR display_order = 0")
            
        # Tabs migration
        cursor.execute("PRAGMA table_info(tabs)")
        tab_cols = [info[1] for info in cursor.fetchall()]
        if "position" not in tab_cols:
            cursor.execute("ALTER TABLE tabs ADD COLUMN position INTEGER DEFAULT 0")
        
        # Default tab
        cursor.execute("SELECT count(*) FROM tabs")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO tabs (name, color, position) VALUES (?, ?, ?)", ("Principal", "#e0e0e0", 0))
            cursor.execute("UPDATE credenciales SET tab_id = 1 WHERE tab_id IS NULL")

        conn.commit()
        conn.close()

    def get_tabs(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, color FROM tabs ORDER BY position ASC, id ASC")
            return cursor.fetchall()
            
    def get_setting(self, key, default=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            return result[0] if result else default

    def set_setting(self, key, value):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            conn.commit()

    def add_tab(self, name, color):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Get max position
            cursor.execute("SELECT MAX(position) FROM tabs")
            res = cursor.fetchone()
            max_pos = res[0] if res[0] is not None else -1
            new_pos = max_pos + 1
            
            cursor.execute("INSERT INTO tabs (name, color, position) VALUES (?, ?, ?)", (name, color, new_pos))
            conn.commit()

    def update_tab_order(self, tab_ids):
        # tab_ids list of ints in order
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for index, tab_id in enumerate(tab_ids):
                cursor.execute("UPDATE tabs SET position = ? WHERE id = ?", (index, tab_id))
            conn.commit()

    def rename_tab(self, tab_id, new_name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tabs SET name = ? WHERE id = ?", (new_name, tab_id))
            conn.commit()

    def update_tab_color(self, tab_id, new_color):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tabs SET color = ? WHERE id = ?", (new_color, tab_id))
            conn.commit()

    def add_credential(self, data, encryption_manager=None):
        """Add a new credential, encrypting data if encryption_manager is provided."""
        # Encrypt data if encryption manager is provided
        if encryption_manager:
            data = encryption_manager.encrypt_credential(data)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Get max display_order for this tab
            tab_id = data[-1]  # Last element is tab_id
            cursor.execute("SELECT MAX(display_order) FROM credenciales WHERE tab_id = ?", (tab_id,))
            res = cursor.fetchone()
            max_order = res[0] if res[0] is not None else 0
            new_order = max_order + 1
            
            cursor.execute('''
                INSERT INTO credenciales (detalle, tipo_acceso, acceso_host, puerto, usuario, password, rol, contiene, instancia_tipo, ip_priv, ip_pub, tab_id, display_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*data, new_order))
            conn.commit()

    def update_credential(self, record_id, data, encryption_manager=None):
        """Update a credential, encrypting data if encryption_manager is provided."""
        # Encrypt data if encryption manager is provided
        if encryption_manager:
            # Add a dummy value for tab_id since encrypt_credential expects it
            data_with_tab = (*data, None)
            encrypted = encryption_manager.encrypt_credential(data_with_tab)
            # Remove the dummy tab_id
            data = encrypted[:-1]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE credenciales 
                SET detalle=?, tipo_acceso=?, acceso_host=?, puerto=?, usuario=?, password=?, rol=?, contiene=?, instancia_tipo=?, ip_priv=?, ip_pub=?
                WHERE id=?
            ''', (*data, record_id))
            conn.commit()

    def delete_credential(self, record_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM credenciales WHERE id=? ", (record_id,))
            conn.commit()
    
    def update_row_color(self, record_id, color):
        """Update the color marking for a specific row."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE credenciales SET row_color=? WHERE id=? ", (color, record_id))
            conn.commit()

    def delete_tab(self, tab_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Cascade delete credentials in tab
            cursor.execute("DELETE FROM credenciales WHERE tab_id=?", (tab_id,))
            # Delete tab
            cursor.execute("DELETE FROM tabs WHERE id=?", (tab_id,))
            conn.commit()

    def get_credentials(self, tab_id, encryption_manager=None):
        """Get credentials for a tab, decrypting data if encryption_manager is provided."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, detalle, tipo_acceso, acceso_host, puerto, usuario, password, rol, contiene, instancia_tipo, ip_priv, ip_pub, row_color FROM credenciales WHERE tab_id = ? ORDER BY display_order ASC, id ASC", (tab_id,))
            results = cursor.fetchall()
        
        # Decrypt data if encryption manager is provided
        if encryption_manager and results:
            decrypted_results = []
            for row in results:
                decrypted_results.append(encryption_manager.decrypt_credential(row))
            return decrypted_results
        
        return results
    
    def is_data_encrypted(self):
        """Check if data in the database is already encrypted."""
        return self.get_setting("data_encrypted", "false") == "true"
    
    def mark_data_encrypted(self):
        """Mark that data in the database is encrypted."""
        self.set_setting("data_encrypted", "true")
    
    def migrate_to_encrypted(self, encryption_manager):
        """Migrate all existing unencrypted data to encrypted format."""
        if self.is_data_encrypted():
            return  # Already encrypted
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all credentials
            cursor.execute("SELECT id, detalle, tipo_acceso, acceso_host, puerto, usuario, password, rol, contiene, instancia_tipo, ip_priv, ip_pub, tab_id FROM credenciales")
            all_credentials = cursor.fetchall()
            
            # Encrypt and update each credential
            for cred in all_credentials:
                cred_id = cred[0]
                # Extract data fields (skip id)
                # cred structure: (id, detalle, tipo_acceso, acceso_host, puerto, usuario, password, rol, contiene, instancia_tipo, ip_priv, ip_pub, tab_id)
                # Indices:         0    1        2            3             4       5         6         7     8         9               10        11        12
                data = cred[1:12]  # detalle through ip_pub (indices 1-11)
                tab_id = cred[12]  # tab_id is at index 12
                
                # Encrypt the data
                data_with_tab = (*data, tab_id)
                encrypted = encryption_manager.encrypt_credential(data_with_tab)
                encrypted_data = encrypted[:-1]  # Remove tab_id from encrypted data
                
                # Update the record
                cursor.execute('''
                    UPDATE credenciales 
                    SET detalle=?, tipo_acceso=?, acceso_host=?, puerto=?, usuario=?, password=?, rol=?, contiene=?, instancia_tipo=?, ip_priv=?, ip_pub=?
                    WHERE id=?
                ''', (*encrypted_data, cred_id))
            
            conn.commit()
        
        # Mark as encrypted
        self.mark_data_encrypted()
    
    def move_entry_up(self, record_id, tab_id):
        """Move an entry up in the display order."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get current order
            cursor.execute("SELECT display_order FROM credenciales WHERE id = ?", (record_id,))
            result = cursor.fetchone()
            if not result:
                return False
            
            current_order = result[0]
            
            # Find the entry above (with lower order in same tab)
            cursor.execute("""
                SELECT id, display_order FROM credenciales 
                WHERE tab_id = ? AND display_order < ? 
                ORDER BY display_order DESC LIMIT 1
            """, (tab_id, current_order))
            
            above_entry = cursor.fetchone()
            if not above_entry:
                return False  # Already at top
            
            above_id, above_order = above_entry
            
            # Swap orders
            cursor.execute("UPDATE credenciales SET display_order = ? WHERE id = ?", (above_order, record_id))
            cursor.execute("UPDATE credenciales SET display_order = ? WHERE id = ?", (current_order, above_id))
            
            conn.commit()
            return True
    
    def move_entry_down(self, record_id, tab_id):
        """Move an entry down in the display order."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get current order
            cursor.execute("SELECT display_order FROM credenciales WHERE id = ?", (record_id,))
            result = cursor.fetchone()
            if not result:
                return False
            
            current_order = result[0]
            
            # Find the entry below (with higher order in same tab)
            cursor.execute("""
                SELECT id, display_order FROM credenciales 
                WHERE tab_id = ? AND display_order > ? 
                ORDER BY display_order ASC LIMIT 1
            """, (tab_id, current_order))
            
            below_entry = cursor.fetchone()
            if not below_entry:
                return False  # Already at bottom
            
            below_id, below_order = below_entry
            
            # Swap orders
            cursor.execute("UPDATE credenciales SET display_order = ? WHERE id = ?", (below_order, record_id))
            cursor.execute("UPDATE credenciales SET display_order = ? WHERE id = ?", (current_order, below_id))
            
            conn.commit()
            return True
