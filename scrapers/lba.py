import requests
from datetime import datetime

def search_lba(max_days_old=7):
    api_url = "https://labonnealternance.apprentissage.beta.gouv.fr/api/V1/jobs"
    
    params = {
        "romes": "M1806,M1802,M1801,M1810,M1844,M1883",
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
                offer_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                difference = (today - offer_date).days
                return difference <= max_days_old
            except Exception:
                return False

        # 1. Les offres "Matcha" (Direct LBA)
        if 'matchas' in data and 'results' in data['matchas']:
            for job in data['matchas']['results']:
                try:
                    job_info = job.get('job') or {}
                    creation_date = str(job_info.get('creationDate') or "")
                    
                    if is_recent(creation_date):
                        # Sécurisation anti-NoneType absolue
                        title = str(job.get('title') or "Sans titre")
                        
                        company_info = job.get('company') or {}
                        company = str(company_info.get('name') or "Confidentiel")
                        
                        description_text = str(job_info.get('description') or "")
                        rome_details = str(job_info.get('romeDetails') or "")
                        
                        link = str(job.get('url') or "Lien non fourni")
                        
                        place_info = job.get('place') or {}
                        location = str(place_info.get('city') or "France")
                        
                        days_ago = (today - datetime.strptime(creation_date[:10], '%Y-%m-%d')).days
                        
                        # On fusionne tout en texte pour la recherche de mots-clés
                        full_text = f"{title} {company} {location} {description_text} {rome_details}"
                        
                        offers.append({
                            "title": title[:80],
                            "company": company[:40],
                            "description": full_text,
                            "link": link,
                            "location": location,
                            "date": f"Il y a {days_ago} jours",
                            "source": "LBA"
                        })
                except Exception as e:
                    print(f"      [Avertissement] Une offre Matcha ignorée suite à une erreur : {e}")
                    continue
                
        # 2. Les offres "France Travail" (Pôle Emploi)
        if 'peJobs' in data and 'results' in data['peJobs']:
            for job in data['peJobs']['results']:
                try:
                    job_info = job.get('job') or {}
                    creation_date = str(job_info.get('creationDate') or "")
                    
                    if is_recent(creation_date):
                        # Sécurisation anti-NoneType absolue
                        title = str(job.get('title') or "Sans titre")
                        
                        company_info = job.get('company') or {}
                        company = str(company_info.get('name') or "Confidentiel")
                        
                        description_text = str(job_info.get('description') or "")
                        
                        link = str(job.get('url') or "Lien non fourni")
                        
                        place_info = job.get('place') or {}
                        location = str(place_info.get('city') or "France")
                        
                        days_ago = (today - datetime.strptime(creation_date[:10], '%Y-%m-%d')).days
                        
                        # On fusionne tout en texte pour la recherche de mots-clés
                        full_text = f"{title} {company} {location} {description_text}"

                        offers.append({
                            "title": title[:80],
                            "company": company[:40],
                            "description": full_text,
                            "link": link,
                            "location": location,
                            "date": f"Il y a {days_ago} jours",
                            "source": "France Travail"
                        })
                except Exception as e:
                    print(f"      [Avertissement] Une offre France Travail ignorée suite à une erreur : {e}")
                    continue
                
        print(f"   └── 📦 {len(offers)} offres vraiment récentes récupérées.")
        
    except Exception as e:
        print(f"⚠️ Erreur lors du scraping LBA : {e}")
        
    return offers