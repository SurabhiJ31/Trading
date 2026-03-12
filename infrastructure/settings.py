
from infrastructure.secret_manager import get_secret


class Settings:
    def __init__(self):
        self.SUPABASE_URL = get_secret("SUPABASE_URL")
        self.SUPABASE_KEY = get_secret("SUPABASE_KEY")
        self.ENV = "prod"
