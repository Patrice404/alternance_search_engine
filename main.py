import json
import os
from scrapers.hellowork import init_browser, search_hellowork, get_full_description
from scrapers.lba import search_lba
from scrapers.linkedin import search_linkedin, get_full_description_linkedin
from scrapers.wttj import search_wttj, get_full_description_wttj
from utils.notifier import send_discord_alert
# from utils.notifier import send_discord_alert  # Décommente quand tu seras prêt pour Discord

DISCORD_WEBHOOK = "https://discordapp.com/api/webhooks/1474470385847242823/XJhFAhTXFE2VfrQQWeIDdOIKoO3-cbnIUKLuDgkTgwBRu7gCDkUq05LEb8OKGmPG7SFw" 

def load_seen_jobs(filepath='data/seen_jobs.txt'):
    """Charge la liste des offres déjà vues."""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return set(f.read().splitlines())
    return set()

def save_seen_job(url, filepath='data/seen_jobs.txt'):
    """Sauvegarde une URL pour ne plus la traiter la prochaine fois."""
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(f"{url}\n")
        
def extract_pure_keywords(profile):
    """Extrait des mots-clés simples et pertinents à partir des chaînes complexes du JSON."""
    keywords = []
    for category in profile['competences'].values():
        for skill in category:
            # 1. Garder la partie avant la parenthèse (ex: "Active Directory" depuis "Active Directory (AD DS)")
            main_part = skill.split('(')[0].strip().lower()
            
            # Si le mot principal contient un slash (ex: "Bash/Shell")
            if '/' in main_part:
                parts = main_part.split('/')
                for p in parts:
                    keywords.append(p.strip())
            else:
                keywords.append(main_part)
            
            # 2. Extraire ce qu'il y a dans la parenthèse (ex: "Debian/Ubuntu")
            if '(' in skill and ')' in skill:
                inner_part = skill.split('(')[1].split(')')[0]
                # Diviser par slash ou esperluette
                inner_words = inner_part.replace('/', '&').split('&')
                for w in inner_words:
                    keywords.append(w.strip().lower())
                    
    # On supprime les doublons et les chaînes vides
    return list(set([k for k in keywords if k]))


def calculate_match_score(job_data, pure_keywords):
    score = 0
    keywords_found = []
    
    content_to_analyze = (job_data['title'] + " " + job_data['description']).lower()
    
    # 1. Check des compétences nettoyées
    for skill in pure_keywords:
        # On ajoute des espaces pour chercher le mot exact (éviter que 'c' match avec 'avec')
        # Sauf pour les mots composés comme "active directory"
        search_term = f" {skill} " if len(skill) <= 2 else skill
        
        if search_term in content_to_analyze:
            score += 5
            keywords_found.append(skill)
            
    # 2. Bonus pour le titre du poste
    target_titles = ["cybersécurité", "soc", "analyste", "pentest", "système"]
    for t in target_titles:
        if t in job_data['title'].lower():
            score += 20
            break 

    return score, list(set(keywords_found))


def main():
    path_profil = 'data/profile.json'
    if not os.path.exists(path_profil):
        path_profil = 'profil.json'
        
    with open(path_profil, 'r', encoding='utf-8') as f:
        profile = json.load(f)

    pure_keywords = extract_pure_keywords(profile)
    matches_count = 0
    
    # NOUVEAU : On charge la mémoire du bot
    seen_jobs = load_seen_jobs()
    print(f"🧠 Mémoire chargée : {len(seen_jobs)} offres déjà connues.")

    print("==================================================")
    print("🔎 DÉMARRAGE DU MOTEUR DE RECHERCHE D'ALTERNANCE")
    print("==================================================")
    
    driver = init_browser()
    
    try:

        # ------------------------------------------------
        # 1. SCAN DE HELLOWORK (Avec Deep Scan)
        # ------------------------------------------------
        print("\n▶️ PLATEFORME 1 : HELLOWORK")
        hw_offers = search_hellowork(driver, "Alternance Cybersécurité")
        
        for offer in hw_offers:
            if offer['link'] in seen_jobs:
                continue  # Ignorer les offres déjà vues
            score, _ = calculate_match_score(offer, pure_keywords)
            if score >= 20: 
                print(f"   [Deep Scan] Analyse de : {offer['title'][:40]}...")
                full_text = get_full_description(driver, offer['link'])
                offer['description'] = full_text
                
                final_score, final_keywords = calculate_match_score(offer, pure_keywords)
                
                if final_score >= 30: 
                    matches_count += 1
                    print(f"\n🔥 SUPER MATCH HELLOWORK ({final_score} pts) : {offer['title']}")
                    print(f"   🏢 {offer['company']} | 📍 {offer['location']} | 🕒 {offer.get('date', 'Récent')}")
                    print(f"   🔑 Mots-clés : {', '.join(final_keywords).title()}")
                    print(f"   🔗 {offer['link']}\n")
                    send_discord_alert(DISCORD_WEBHOOK, offer['title'], offer['company'], offer['location'], offer.get('date', 'Récent'), final_score, final_keywords, offer['link'])
            save_seen_job(offer['link'])
            seen_jobs.add(offer['link'])
        # ------------------------------------------------
        # 2. SCAN DE LA BONNE ALTERNANCE (API Rapide)
        # ------------------------------------------------
        print("\n▶️ PLATEFORME 2 : LA BONNE ALTERNANCE")
        lba_offers = search_lba()
        
        for offer in lba_offers:
            if offer['link'] in seen_jobs:
                continue  # Ignorer les offres déjà vues
            # Pas besoin de Deep Scan ici, la description est déjà dans l'offre !
            final_score, final_keywords = calculate_match_score(offer, pure_keywords)
            
            if final_score >= 30:
                matches_count += 1
                print(f"\n🔥 SUPER MATCH LBA ({final_score} pts) : {offer['title']}")
                print(f"   🏢 {offer['company']} | 📍 {offer['location']} | 🕒 {offer.get('date', 'Récent')}")
                print(f"   🔑 Mots-clés : {', '.join(final_keywords).title()}")
                print(f"   🔗 {offer['link']}\n")
                send_discord_alert(DISCORD_WEBHOOK, offer['title'], offer['company'], offer['location'], offer.get('date', 'Récent'), final_score, final_keywords, offer['link'])
            save_seen_job(offer['link'])
            seen_jobs.add(offer['link'])
            
        # ------------------------------------------------
        # 3. SCAN DE LINKEDIN
        # ------------------------------------------------
        print("\n▶️ PLATEFORME 3 : LINKEDIN")
        # On peut rajouter "Alternance" et "Cybersécurité" séparés pour que le moteur interne de LinkedIn soit plus précis
        linkedin_offers = search_linkedin(driver, "Alternance Cybersécurité")
        
        for offer in linkedin_offers:
            if offer['link'] in seen_jobs:
                continue  # Ignorer les offres déjà vues
            # 1er check de base
            score, _ = calculate_match_score(offer, pure_keywords)
            
            if score >= 20: 
                print(f"   [Deep Scan] Analyse de : {offer['title'][:40]}... chez {offer['company']}")
                
                # Deep Scan spécifique à LinkedIn
                full_text = get_full_description_linkedin(driver, offer['link'])
                offer['description'] = full_text
                
                final_score, final_keywords = calculate_match_score(offer, pure_keywords)
                #print(f"   └── Résultat : {final_score} pts | {len(final_keywords)} compétences trouvées.")
                print(f"   └── Résultat : {final_score} pts | {len(final_keywords)} compétences trouvées (Texte lu : {len(full_text)} caractères).")
                
                if final_score >= 30: 
                    matches_count += 1
                    print(f"\n🔥 SUPER MATCH LINKEDIN ({final_score} pts) : {offer['title']}")
                    print(f"   🏢 {offer['company']} | 📍 {offer['location']} | 🕒 {offer.get('date', 'Récent')}")
                    print(f"   🔑 Mots-clés : {', '.join(final_keywords).title()}")
                    print(f"   🔗 {offer['link']}\n")
                    send_discord_alert(DISCORD_WEBHOOK, offer['title'], offer['company'], offer['location'], offer.get('date', 'Récent'), final_score, final_keywords, offer['link'])
            save_seen_job(offer['link'])
            seen_jobs.add(offer['link'])  
        # ------------------------------------------------
        # 4. SCAN DE WELCOME TO THE JUNGLE
        # ------------------------------------------------
        print("\n▶️ PLATEFORME 4 : WELCOME TO THE JUNGLE")
        wttj_offers = search_wttj(driver) # Pas besoin d'ajouter "Alternance", l'URL le filtre
        
        for offer in wttj_offers:
            # Vérification Anti-Doublon
            if offer['link'] in seen_jobs:
                continue
                
            score, _ = calculate_match_score(offer, pure_keywords)
            
            if score >= 20: 
                print(f"   [Deep Scan] Analyse de : {offer['title'][:40]}... chez {offer['company']}")
                
                # Deep Scan spécifique à WTTJ
                full_text = get_full_description_wttj(driver, offer['link'])
                offer['description'] = full_text
                
                final_score, final_keywords = calculate_match_score(offer, pure_keywords)
                print(f"   └── Résultat : {final_score} pts | {len(final_keywords)} compétences (Texte lu : {len(full_text)} car.)")
                
                if final_score >= 30: 
                    matches_count += 1
                    print(f"\n🔥 SUPER MATCH WTTJ ({final_score} pts) : {offer['title']}")
                    print(f"   🏢 {offer['company']} | 📍 {offer['location']} | 🕒 {offer.get('date', 'Récent')}")
                    print(f"   🔑 Mots-clés : {', '.join(final_keywords).title()}")
                    print(f"   🔗 {offer['link']}\n")
                    send_discord_alert(DISCORD_WEBHOOK, offer['title'], offer['company'], offer['location'], offer.get('date', 'Récent'), final_score, final_keywords, offer['link'])
            
            # On sauvegarde le lien
            save_seen_job(offer['link'])
            seen_jobs.add(offer['link'])
    finally:
        print("\n   └── 🛑 Fermeture de l'instance Chrome.")
        driver.quit()

    print("==================================================")
    print(f"🏁 TERMINÉ. {matches_count} offres hautement pertinentes trouvées au total.")
    print("==================================================")

if __name__ == "__main__":
    main()