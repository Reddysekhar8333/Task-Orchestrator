
import os
from storages.backends.azure_storage import AzureStorage

class _BaseAzureStorage(AzureStorage):
    account_name = os.getenv('AZURE_ACCOUNT_NAME')
    account_key = os.getenv('AZURE_ACCOUNT_KEY')
    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    expiration_secs = None
    overwrite_files = False

class AzureMediaStorage(_BaseAzureStorage):
    azure_container = os.getenv('AZURE_MEDIA_CONTAINER', 'media')


class AzureStaticStorage(_BaseAzureStorage):
    azure_container = os.getenv('AZURE_STATIC_CONTAINER', 'static')