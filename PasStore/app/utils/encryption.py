import base64
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet


class EncryptionManager:
    """Manages encryption and decryption of sensitive credential data using Fernet symmetric encryption."""
    
    def __init__(self, master_password, salt):
        """
        Initialize the encryption manager with a master password.
        
        Args:
            master_password (str): The master password to derive the encryption key from
            salt (bytes): Salt for key derivation (should be stored in database)
        """
        self.master_password = master_password
        self.salt = salt
        self.key = self._derive_key(master_password, salt)
        self.fernet = Fernet(self.key)
    
    @staticmethod
    def generate_salt():
        """Generate a random salt for key derivation."""
        return os.urandom(16)
    
    def _derive_key(self, password, salt):
        """
        Derive a Fernet-compatible key from the master password using PBKDF2.
        
        Args:
            password (str): Master password
            salt (bytes): Salt for key derivation
            
        Returns:
            bytes: Base64-encoded 32-byte key suitable for Fernet
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, plaintext):
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext (str): Text to encrypt
            
        Returns:
            str: Encrypted text as base64 string, or None if plaintext is None/empty
        """
        if plaintext is None or plaintext == "":
            return plaintext
        
        try:
            encrypted = self.fernet.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            print(f"Encryption error: {e}")
            return plaintext
    
    def decrypt(self, ciphertext):
        """
        Decrypt an encrypted string.
        
        Args:
            ciphertext (str): Encrypted text to decrypt
            
        Returns:
            str: Decrypted plaintext, or original value if decryption fails
        """
        if ciphertext is None or ciphertext == "":
            return ciphertext
        
        try:
            decrypted = self.fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            # If decryption fails, it might be unencrypted data
            return ciphertext
    
    def encrypt_credential(self, data):
        """
        Encrypt all fields in a credential tuple/list.
        
        Args:
            data (tuple/list): Credential data in order:
                (detalle, tipo_acceso, acceso_host, puerto, usuario, password, 
                 rol, contiene, instancia_tipo, ip_priv, ip_pub, tab_id)
        
        Returns:
            tuple: Encrypted credential data
        """
        # Convert to list for easier manipulation
        encrypted_data = list(data)
        
        # Encrypt all fields except tab_id (last field)
        for i in range(len(encrypted_data) - 1):
            if encrypted_data[i] is not None:
                encrypted_data[i] = self.encrypt(str(encrypted_data[i]))
        
        return tuple(encrypted_data)
    
    def decrypt_credential(self, data):
        """
        Decrypt all fields in a credential tuple/list.
        
        Args:
            data (tuple/list): Encrypted credential data from database
                (id, detalle, tipo_acceso, acceso_host, puerto, usuario, password,
                 rol, contiene, instancia_tipo, ip_priv, ip_pub)
        
        Returns:
            tuple: Decrypted credential data
        """
        # Convert to list for easier manipulation
        decrypted_data = list(data)
        
        # Skip id (index 0), decrypt all other fields
        for i in range(1, len(decrypted_data)):
            if decrypted_data[i] is not None:
                decrypted_data[i] = self.decrypt(str(decrypted_data[i]))
        
        return tuple(decrypted_data)
