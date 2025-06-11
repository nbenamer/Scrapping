import json
from pymongo import MongoClient

# Connexion à MongoDB local
client = MongoClient("mongodb://localhost:27017/")
db = client["blog"]
collection = db["articles"]

# Charger le fichier JSON
with open("articles.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Insertion avec upsert (mise à jour si url déjà existante)
inserted = 0
for article in data:
    article.pop("_id", None)  # Supprime tout champ _id si présent
    if article.get("url"):
        result = collection.update_one(
            {"url": article["url"]},  # critère d’unicité
            {"$set": article},
            upsert=True
        )
        inserted += 1

print(f"✅ {inserted} articles insérés ou mis à jour.")
