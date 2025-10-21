from pprint import pprint
from src.connector.manager import MetabaseAPIManager
from core.base_config import BaseConfig

config = BaseConfig()
api_token = config.api_token
base_url = config.base_url

manager = MetabaseAPIManager(api_token, base_url)

collection_url = manager.collection.get_self_url()
print(f'Collection URL: {collection_url}')
print(manager.collection._api_token)
pprint(manager.collection._get(collection_url).content)
