import hashlib
import base64
from app.utils.encryption import EncryptionManager

class SecurityManager:
    @staticmethod
    def get_master_hash(db):
        return db.get_setting("master_hash")

    @staticmethod
    def set_master_password(db, password):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        db.set_setting("master_hash", hashed)
        return hashed

    @staticmethod
    def has_master_password(db):
        return db.get_setting("master_hash") is not None

    @staticmethod
    def verify_password(password, stored_hash):
        if not stored_hash:
            return False
        return hashlib.sha256(password.encode()).hexdigest() == stored_hash
    
    @staticmethod
    def get_encryption_salt(db):
        """
        Get or create the encryption salt for key derivation.
        
        Args:
            db: DatabaseManager instance
            
        Returns:
            bytes: Salt for encryption key derivation
        """
        salt_b64 = db.get_setting("encryption_salt")
        if salt_b64:
            return base64.b64decode(salt_b64)
        else:
            # Generate new salt
            salt = EncryptionManager.generate_salt()
            db.set_setting("encryption_salt", base64.b64encode(salt).decode())
            return salt
    
    @staticmethod
    def create_encryption_manager(password, db):
        """
        Factory method to create an EncryptionManager with the master password.
        
        Args:
            password (str): Master password
            db: DatabaseManager instance
            
        Returns:
            EncryptionManager: Configured encryption manager
        """
        salt = SecurityManager.get_encryption_salt(db)
        return EncryptionManager(password, salt)
