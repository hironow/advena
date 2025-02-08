import os

from google.cloud import firestore  # type: ignore

from src.logger import logger

if os.getenv("CI") == "true":
    from mockfirestore import MockFirestore  # type: ignore

    db = MockFirestore()
else:
    if os.getenv("USE_FIREBASE_EMULATOR") == "true":
        logger.info("Using Firebase Emulator...")
        db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
    else:
        db = firestore.Client()  # firebase admin sdkは使わない
