import sqlite3

# Connect to database
conn = sqlite3.connect('mis_passwords.db')
cursor = conn.cursor()

# Check if data is marked as encrypted
cursor.execute("SELECT value FROM settings WHERE key='data_encrypted'")
result = cursor.fetchone()
print(f"Data encrypted flag: {result[0] if result else 'Not set'}")

# Check a sample credential to see if it's encrypted
cursor.execute("SELECT usuario, password FROM credenciales LIMIT 1")
sample = cursor.fetchone()
if sample:
    print(f"\nSample usuario field: {sample[0][:50] if sample[0] else 'NULL'}...")
    print(f"Sample password field: {sample[1][:50] if sample[1] else 'NULL'}...")
    
    # Check if it looks like encrypted data (Fernet encrypted data starts with 'gAAAAA')
    if sample[0] and sample[0].startswith('gAAAAA'):
        print("\n✓ Data appears to be encrypted (Fernet format detected)")
    else:
        print("\n✗ Data does not appear to be encrypted")
else:
    print("\nNo credentials found in database")

conn.close()
