"""
Data protection module.
This module provides functions to protect user data and implement secure storage.
"""

import os
import time
import uuid
import logging
import shutil
import threading
from cryptography.fernet import Fernet
from flask import current_app

# Configure logging
logger = logging.getLogger(__name__)

# Default retention period (10 minutes)
DEFAULT_RETENTION_PERIOD = 600

class SecureStorage:
    """Class for handling secure file storage with encryption and automatic deletion."""
    
    def __init__(self, base_dir, key=None, retention_period=DEFAULT_RETENTION_PERIOD):
        """
        Initialize the secure storage.
        
        Args:
            base_dir: Base directory for file storage.
            key: Encryption key. If None, a new key will be generated.
            retention_period: Time in seconds before files are automatically deleted.
        """
        self.base_dir = base_dir
        self.retention_period = retention_period
        
        # Create the base directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)
        
        # Initialize encryption
        if key is None:
            self.key = Fernet.generate_key()
        else:
            self.key = key
        
        self.cipher = Fernet(self.key)
        
        # Start the cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_thread, daemon=True)
        self.cleanup_thread.start()
    
    def store_file(self, file_stream, filename):
        """
        Store a file securely with encryption.
        
        Args:
            file_stream: The file stream to store.
            filename: The filename.
            
        Returns:
            str: The secure file ID.
        """
        # Generate a unique ID for the file
        file_id = str(uuid.uuid4())
        
        # Create a directory for this file
        file_dir = os.path.join(self.base_dir, file_id)
        os.makedirs(file_dir, exist_ok=True)
        
        # Save metadata
        metadata = {
            'original_filename': filename,
            'timestamp': time.time(),
            'encrypted': True
        }
        
        with open(os.path.join(file_dir, 'metadata.txt'), 'w') as f:
            for key, value in metadata.items():
                f.write(f"{key}={value}\n")
        
        # Save the encrypted file
        file_stream.seek(0)
        file_data = file_stream.read()
        encrypted_data = self.cipher.encrypt(file_data)
        
        with open(os.path.join(file_dir, 'data.enc'), 'wb') as f:
            f.write(encrypted_data)
        
        logger.info(f"File stored securely with ID {file_id}")
        return file_id
    
    def retrieve_file(self, file_id):
        """
        Retrieve a file by its ID.
        
        Args:
            file_id: The file ID.
            
        Returns:
            tuple: (file_data, original_filename) or (None, None) if the file doesn't exist.
        """
        file_dir = os.path.join(self.base_dir, file_id)
        
        if not os.path.exists(file_dir):
            logger.warning(f"File with ID {file_id} not found")
            return None, None
        
        # Read metadata
        metadata = {}
        try:
            with open(os.path.join(file_dir, 'metadata.txt'), 'r') as f:
                for line in f:
                    key, value = line.strip().split('=', 1)
                    metadata[key] = value
        except Exception as e:
            logger.error(f"Error reading metadata for file {file_id}: {str(e)}")
            return None, None
        
        # Read and decrypt the file
        try:
            with open(os.path.join(file_dir, 'data.enc'), 'rb') as f:
                encrypted_data = f.read()
            
            file_data = self.cipher.decrypt(encrypted_data)
            original_filename = metadata.get('original_filename', f"file_{file_id}")
            
            return file_data, original_filename
        except Exception as e:
            logger.error(f"Error retrieving file {file_id}: {str(e)}")
            return None, None
    
    def delete_file(self, file_id):
        """
        Delete a file by its ID.
        
        Args:
            file_id: The file ID.
            
        Returns:
            bool: True if the file was deleted, False otherwise.
        """
        file_dir = os.path.join(self.base_dir, file_id)
        
        if not os.path.exists(file_dir):
            logger.warning(f"File with ID {file_id} not found")
            return False
        
        try:
            shutil.rmtree(file_dir)
            logger.info(f"File with ID {file_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            return False
    
    def _cleanup_thread(self):
        """Background thread to clean up expired files."""
        while True:
            try:
                self._cleanup_expired_files()
            except Exception as e:
                logger.error(f"Error in cleanup thread: {str(e)}")
            
            # Sleep for a while before the next cleanup
            time.sleep(60)
    
    def _cleanup_expired_files(self):
        """Clean up expired files."""
        current_time = time.time()
        
        for file_id in os.listdir(self.base_dir):
            file_dir = os.path.join(self.base_dir, file_id)
            
            if not os.path.isdir(file_dir):
                continue
            
            # Read metadata
            try:
                metadata = {}
                metadata_path = os.path.join(file_dir, 'metadata.txt')
                
                if not os.path.exists(metadata_path):
                    continue
                
                with open(metadata_path, 'r') as f:
                    for line in f:
                        key, value = line.strip().split('=', 1)
                        metadata[key] = value
                
                # Check if the file has expired
                timestamp = float(metadata.get('timestamp', 0))
                if current_time - timestamp > self.retention_period:
                    logger.info(f"Deleting expired file with ID {file_id}")
                    shutil.rmtree(file_dir)
            except Exception as e:
                logger.error(f"Error cleaning up file {file_id}: {str(e)}")

def initialize_secure_storage(app):
    """
    Initialize secure storage for the application.
    
    Args:
        app: The Flask application.
        
    Returns:
        SecureStorage: The secure storage instance.
    """
    # Get the base directory from the app config
    base_dir = app.config.get('SECURE_STORAGE_DIR', os.path.join(app.instance_path, 'secure_storage'))
    
    # Get the encryption key from the app config or generate a new one
    key = app.config.get('SECURE_STORAGE_KEY')
    if key is None:
        key = Fernet.generate_key()
        app.config['SECURE_STORAGE_KEY'] = key
    
    # Get the retention period from the app config
    retention_period = app.config.get('SECURE_STORAGE_RETENTION', DEFAULT_RETENTION_PERIOD)
    
    # Create the secure storage
    storage = SecureStorage(base_dir, key, retention_period)
    
    # Store the secure storage in the app
    app.secure_storage = storage
    
    return storage
