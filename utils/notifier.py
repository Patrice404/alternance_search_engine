import requests
from bs4 import BeautifulSoup
import requests

import requests

def send_discord_report(webhook_url, image_path, total_scannees, total_pertinentes):
    """Envoie l'image des statistiques sur Discord avec un petit message."""
    
    message = f"📊 **FIN DU SCAN**\n🔍 Offres analysées : **{total_scannees}**\n🔥 Offres super pertinentes : **{total_pertinentes}**\nVoici le graphique des performances :"
    
    try:
        # On ouvre l'image en mode lecture binaire ("rb")
        with open(image_path, "rb") as image_file:
            # Discord s'attend à recevoir un dictionnaire de fichiers
            files = {
                "file": (image_path, image_file, "image/png")
            }
            # Et le texte classique va dans 'data'
            payload = {
                "content": message
            }
            
            response = requests.post(webhook_url, data=payload, files=files)
            
            if response.status_code in [200, 204]:
                print("   [Notifier] 📊 Rapport stats envoyé sur Discord avec succès !")
            else:
                print(f"   [Erreur] Échec de l'envoi du rapport Discord : {response.status_code}")
                
    except Exception as e:
        print(f"   [Erreur] Impossible d'envoyer l'image sur Discord : {e}")
        
def send_discord_alert(webhook_url, title, company, location, date, score, keywords, link, duration):
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
            {"name": "⏳ Durée estimée", "value": duration, "inline": True},
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