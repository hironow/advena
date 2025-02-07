import os

from google.cloud import firestore  # type: ignore

if os.getenv("CI") == "true":
    from mockfirestore import MockFirestore  # type: ignore

    db = MockFirestore()
else:
    if os.getenv("USE_FIREBASE_EMULATOR") == "true":
        db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
    else:
        db = firestore.Client()  # firebase admin sdkは使わない
