import requests
from bs4 import BeautifulSoup



import requests

def send_discord_alert(webhook_url, title, company, location, date, score, keywords, link):
    if not webhook_url:
        return
        
    embed = {
        "title": f"🔥 {title}",
        "url": link,
        "color": 5763719,  # Vert cyber
        "fields": [
            {"name": "🏢 Entreprise", "value": company, "inline": True},
            {"name": "📍 Localisation", "value": location, "inline": True},
            {"name": "🕒 Publié", "value": date, "inline": True},
            {"name": "⭐ Score", "value": f"{score} pts", "inline": True},
            {"name": "🔑 Compétences", "value": ", ".join(keywords).title(), "inline": False}
        ],
        "footer": {
            "text": "CyberBot Job Search - Patrice"
        }
    }
    
    payload = {
        "content": "🚀 **Nouvelle offre d'alternance hautement pertinente !**",
        "embeds": [embed]
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print("   [Notifier] 🔔 Alerte Discord envoyée avec succès !")
    except Exception as e:
        print(f"   [Notifier] ❌ Erreur lors de l'envoi Discord : {e}")