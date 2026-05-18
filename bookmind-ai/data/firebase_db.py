# firebase_db.py bu proje için Firebase bağlantısını yöneten merkezi sınıfı içerir. RTDB ve Firestore işlemleri burada toplanır.
import firebase_admin
from firebase_admin import credentials, firestore, db
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class FirebaseManager:
    """
    Tüm Firebase (RTDB & Firestore) trafiğini yöneten merkezi sınıf.
    """
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._setup_connection()
            self._initialized = True

    def _setup_connection(self):
        # Scriptin bulundugu klasorden kok dizine cik
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, ".."))
        
        key_path = os.path.join(project_root, "firebase-key.json")
        db_url = "https://hackatonproject-b067e-default-rtdb.firebaseio.com"

        if not os.path.exists(key_path):
            raise FileNotFoundError(f"HATA: {key_path} dosyasi bulunamadi!")

        try:
            # Singleton kontrolü
            if not firebase_admin._apps:
                cred = credentials.Certificate(key_path)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': db_url
                })
            
            self.firestore_db = firestore.client()
            self.rtd_ref = db.reference("/")
            logger.info("Firebase (RTDB & Firestore) bağlantısı başarıyla kuruldu. [OK]")
        except Exception as e:
            logger.error(f"Firebase bağlantı hatası: {e}")
            raise

    def get_user_context(self, user_id: str) -> Dict:
        """
        Kullanicinin kütüphane ve sepet bilgilerini RTDB'den ceker.
        """
        try:
            # 1. Sepet verisi
            cart = self.rtd_ref.child(f"carts/{user_id}").get() or []
            
            # 2. Kütüphane verisi
            library = self.rtd_ref.child(f"libraries/{user_id}").get() or {}
            
            # Kitap isimlerini bir listeye topla (Özet metin için)
            lib_titles = []
            if isinstance(library, dict):
                for key, item in library.items():
                    if isinstance(item, dict) and 'title' in item:
                        lib_titles.append(item['title'])
            
            cart_titles = []
            if isinstance(cart, list):
                for item in cart:
                    if isinstance(item, dict) and 'title' in item:
                        cart_titles.append(item['title'])

            return {
                "user_id": user_id,
                "library_list": lib_titles,
                "cart_list": cart_titles,
                "history_text": f"Kütüphane: {', '.join(lib_titles) if lib_titles else 'Boş'}. Sepet: {', '.join(cart_titles) if cart_titles else 'Boş'}."
            }
        except Exception as e:
            logger.error(f"Kullanici verisi cekilemedi: {e}")
            return {"user_id": user_id, "library_list": [], "cart_list": [], "history_text": ""}

# Global erişim için hazır nesne
fb_manager = FirebaseManager()
