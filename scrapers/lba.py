import requests
from datetime import datetime

def search_lba(max_days_old=7):
    api_url = "https://labonnealternance.apprentissage.beta.gouv.fr/api/V1/jobs"
    
    params = {
        "romes": "M1806,M1803,M1805,M1802",
        "diploma": "7 (Master, titre ingénieur...)",
        "radius": 100,
        "caller": "bot_alternance_patrice"
    }
    
    print(f"   └── 🌐 Interrogation de l'API La Bonne Alternance (Filtre: < {max_days_old} jours)...")
    offers = []
    
    # On récupère la date du jour pour comparer
    today = datetime.now()
    
    try:
        response = requests.get(api_url, params=params)
        if response.status_code != 200:
            print(f"   [Erreur API LBA] Code {response.status_code}")
            return offers
            
        data = response.json()
        
        # Fonction interne pour vérifier si l'offre est récente
        def is_recent(date_str):
            if not date_str:
                return False
            try:
                # L'API renvoie souvent un format ISO comme "2023-10-25T14:30:00.000Z"
                # On ne garde que les 10 premiers caractères "YYYY-MM-DD"
                offer_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                difference = (today - offer_date).days
                return difference <= max_days_old
            except Exception:
                return False

        # 1. Les offres "Matcha" (Direct LBA)
        if 'matchas' in data and 'results' in data['matchas']:
            for job in data['matchas']['results']:
                creation_date = job.get('job', {}).get('creationDate', '')
                
                # Le filtre magique est appliqué ici !
                if is_recent(creation_date):
                    offers.append({
                        "title": job.get('title', 'Sans titre'),
                        "company": job.get('company', {}).get('name', 'Confidentiel'),
                        "description": job.get('job', {}).get('description', ''),
                        "link": job.get('url', 'Lien non fourni'),
                        "location": job.get('place', {}).get('city', 'France'),
                        "date": f"Il y a {(today - datetime.strptime(creation_date[:10], '%Y-%m-%d')).days} jours",
                        "source": "LBA"
                    })
                
        # 2. Les offres "France Travail" (Pôle Emploi)
        if 'peJobs' in data and 'results' in data['peJobs']:
            for job in data['peJobs']['results']:
                creation_date = job.get('job', {}).get('creationDate', '')
                
                # Le même filtre ici
                if is_recent(creation_date):
                    offers.append({
                        "title": job.get('title', 'Sans titre'),
                        "company": job.get('company', {}).get('name', 'Confidentiel'),
                        "description": job.get('job', {}).get('description', ''),
                        "link": job.get('url', 'Lien non fourni'),
                        "location": job.get('place', {}).get('city', 'France'),
                        "date": f"Il y a {(today - datetime.strptime(creation_date[:10], '%Y-%m-%d')).days} jours",
                        "source": "France Travail"
                    })
                
        print(f"   └── 📦 {len(offers)} offres vraiment récentes récupérées.")
        
    except Exception as e:
        print(f"⚠️ Erreur lors du scraping LBA : {e}")
        
    return offers