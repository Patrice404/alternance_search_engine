import json
import os
import re
from scrapers.lba import search_lba
from utils.notifier import send_discord_alert, send_discord_report
from scrapers.hellowork import init_browser, search_hellowork, get_full_description
from scrapers.linkedin import search_linkedin, get_full_description_linkedin
from scrapers.wttj import search_wttj, get_full_description_wttj
from scrapers.apec import search_apec, get_full_description_apec
from utils.stats_generator import generate_stats_graph

from settings import DISCORD_WEBHOOK, SCHOOL_NAME, LINKEDIN_QUERIES, SUPER_MATCH_THRESHOLD, APEC_QUERIES, TARGET_TITLES, MATCH_TITLES_SCORE, WTTJ_QUERIES, HELLOWORK_QUERIES

def extract_duration(text):
    """Fouille le texte de l'offre pour deviner la durée de l'alternance."""
    if not text:
        return "Non précisée"
        
    # 1. On cherche en priorité les formats très clairs "12 mois", "24 mois", "36 mois"
    match_mois = re.search(r"(?i)\b(12|24|36)\s*mois\b", text)
    if match_mois:
        return match_mois.group(0).lower()
        
    # 2. On cherche "1 an", "2 ans", "3 ans" mais SEULEMENT s'ils sont près des mots "durée", "contrat" ou "alternance"
    # (Pour éviter de confondre avec "2 ans d'expérience requis")
    match_ans = re.search(r"(?i)(?:durée|contrat|alternance).{0,30}\b([123]\s*an[s]?)\b", text)
    if match_ans:
        return match_ans.group(1).lower()
        
    return "Non précisée"


def valid_offer(offer, seen_jobs):
        
    if offer['link'] in seen_jobs:
        return False  # Offre déjà vue
        
    # On passe le nom de l'entreprise en minuscules une seule fois
    company_name = offer.get('company', '').lower()
    
    # Vérification : si UNE des écoles de la liste se trouve DANS le nom de l'entreprise
    if any(school.lower() in company_name for school in SCHOOL_NAME):
        print(f"   [Filtre] Écarté (École détectée) : {offer['title']} chez {offer['company']}")
        save_seen_job(offer['link'])
        seen_jobs.add(offer['link'])
        return False
    
    return True

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
    for t in TARGET_TITLES:
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
    
    # Avant le début des scans
    bot_stats = {
        "HelloWork": {"scannées": 0, "pertinentes": 0},
        "LaBonneAlternance": {"scannées": 0, "pertinentes": 0},
        "LinkedIn": {"scannées": 0, "pertinentes": 0},
        "WTTJ": {"scannées": 0, "pertinentes": 0},
        "APEC": {"scannées": 0, "pertinentes": 0}
    }
    
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
        for query in HELLOWORK_QUERIES:
            print(f"   └── 🌐 Recherche HelloWork : {query}")
            hw_offers = search_hellowork(driver, query)
            bot_stats["HelloWork"]["scannées"] += len(hw_offers) 
            for offer in hw_offers:
                if not valid_offer(offer, seen_jobs):
                    continue
                        
                score, _ = calculate_match_score(offer, pure_keywords)
                if score >= MATCH_TITLES_SCORE: 
                    if offer['company'] in SCHOOL_NAME:
                            print(f"   [Filtre] Écarté (Entreprise écartée) : {offer['title']} chez {offer['company']}")
                            continue
                    print(f"   [Deep Scan] Analyse de : {offer['title'][:60]}...")
                    full_text = get_full_description(driver, offer['link'])
                    offer['description'] = full_text
                    duration = extract_duration(full_text)
                    
                    final_score, final_keywords = calculate_match_score(offer, pure_keywords)
                    
                    if final_score >= SUPER_MATCH_THRESHOLD: 
                        matches_count += 1
                        bot_stats["HelloWork"]["pertinentes"] += 1
                        
                        print(f"\n🔥 SUPER MATCH HELLOWORK ({final_score} pts) : {offer['title']}")
                        print(f"   🏢 {offer['company']} | 📍 {offer['location']} | 🕒 {offer.get('date', 'Récent')}")
                        print(f"   ⏳ Durée estimée : {duration}")
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
        bot_stats["LaBonneAlternance"]["scannées"] += len(lba_offers)
        
        for offer in lba_offers:
            if not valid_offer(offer, seen_jobs):
                continue
            
            # Pas besoin de Deep Scan ici, la description est déjà dans l'offre !
            final_score, final_keywords = calculate_match_score(offer, pure_keywords)
            
            if final_score >= SUPER_MATCH_THRESHOLD:
                matches_count += 1
                bot_stats["LaBonneAlternance"]["pertinentes"] += 1
                
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
        for query in LINKEDIN_QUERIES:
            print(f"   └── 🌐 Recherche LinkedIn : {query}")
            linkedin_offers = search_linkedin(driver, query)
            bot_stats["LinkedIn"]["scannées"] += len(linkedin_offers)
            
            for offer in linkedin_offers:
                if not valid_offer(offer, seen_jobs):
                    continue
                # 1er check de base
                score, _ = calculate_match_score(offer, pure_keywords)
                
                if score >= MATCH_TITLES_SCORE: 
                    
                    print(f"   [Deep Scan] Analyse de : {offer['title'][:60]}... chez {offer['company']}")
                    
                    # Deep Scan spécifique à LinkedIn
                    full_text = get_full_description_linkedin(driver, offer['link'])
                    offer['description'] = full_text
                    
                    duration = extract_duration(full_text)
                    
                    final_score, final_keywords = calculate_match_score(offer, pure_keywords)
                    #print(f"   └── Résultat : {final_score} pts | {len(final_keywords)} compétences trouvées.")
                    print(f"   └── Résultat : {final_score} pts | {len(final_keywords)} compétences trouvées (Texte lu : {len(full_text)} caractères).")
                    
                    if final_score >= SUPER_MATCH_THRESHOLD: 
                        matches_count += 1
                        bot_stats["LinkedIn"]["pertinentes"] += 1
                        
                        print(f"\n🔥 SUPER MATCH LINKEDIN ({final_score} pts) : {offer['title']}")
                        print(f"   🏢 {offer['company']} | 📍 {offer['location']} | 🕒 {offer.get('date', 'Récent')}")
                        print(f"   ⏳ Durée estimée : {duration}")
                        print(f"   🔑 Mots-clés : {', '.join(final_keywords).title()}")
                        print(f"   🔗 {offer['link']}\n")
                        send_discord_alert(DISCORD_WEBHOOK, offer['title'], offer['company'], offer['location'], offer.get('date', 'Récent'), final_score, final_keywords, offer['link'])
                
                save_seen_job(offer['link'])
                seen_jobs.add(offer['link'])  
        
        # ------------------------------------------------
        # 4. SCAN DE WELCOME TO THE JUNGLE
        # ------------------------------------------------
        print("\n▶️ PLATEFORME 4 : WELCOME TO THE JUNGLE")
        for query in WTTJ_QUERIES:
            print(f"   └── 🌐 Recherche WTTJ : {query}")
            wttj_offers = search_wttj(driver, query)
            bot_stats["WTTJ"]["scannées"] += len(wttj_offers)
            
            for offer in wttj_offers:
                if not valid_offer(offer, seen_jobs):
                    continue
                    
                score, _ = calculate_match_score(offer, pure_keywords)
                
                if score >= MATCH_TITLES_SCORE: 
                    
                    print(f"   [Deep Scan] Analyse de : {offer['title'][:60]}... chez {offer['company']}")
                    
                    # Deep Scan spécifique à WTTJ
                    full_text = get_full_description_wttj(driver, offer['link'])
                    offer['description'] = full_text
                    
                    duration = extract_duration(full_text)
                    
                    final_score, final_keywords = calculate_match_score(offer, pure_keywords)
                    print(f"   └── Résultat : {final_score} pts | {len(final_keywords)} compétences (Texte lu : {len(full_text)} car.)")
                    
                    if final_score >= SUPER_MATCH_THRESHOLD: 
                        matches_count += 1
                        bot_stats["WTTJ"]["pertinentes"] += 1
                        
                        print(f"\n🔥 SUPER MATCH WTTJ ({final_score} pts) : {offer['title']}")
                        print(f"   🏢 {offer['company']} | 📍 {offer['location']} | 🕒 {offer.get('date', 'Récent')}")
                        print(f"   ⏳ Durée estimée : {duration}")
                        print(f"   🔑 Mots-clés : {', '.join(final_keywords).title()}")
                        print(f"   🔗 {offer['link']}\n")
                        send_discord_alert(DISCORD_WEBHOOK, offer['title'], offer['company'], offer['location'], offer.get('date', 'Récent'), final_score, final_keywords, offer['link'])
                
                save_seen_job(offer['link'])
                seen_jobs.add(offer['link'])
            
         # ------------------------------------------------
        # 5. SCAN DE L'APEC
        # ------------------------------------------------
        print("\n▶️ PLATEFORME 5 : APEC")
        for query in APEC_QUERIES:
            print(f"   └── 🌐 Recherche APEC : {query}")
            apec_offers = search_apec(driver, query) 
            bot_stats["APEC"]["scannées"] += len(apec_offers)
            
            for offer in apec_offers:
                if not valid_offer(offer, seen_jobs):
                    continue
                    
                score, _ = calculate_match_score(offer, pure_keywords)
                
                if score >= MATCH_TITLES_SCORE: 
                    print(f"   [Deep Scan] Analyse de : {offer['title']}...")
                    
                    # Deep Scan APEC
                    full_text = get_full_description_apec(driver, offer['link'])
                    offer['description'] = full_text
                    
                    duration = extract_duration(full_text)
                    
                    final_score, final_keywords = calculate_match_score(offer, pure_keywords)
                    print(f"   └── Résultat : {final_score} pts | {len(final_keywords)} compétences (Texte lu : {len(full_text)} car.)")
                    
                    if final_score >= SUPER_MATCH_THRESHOLD: 
                        matches_count += 1
                        bot_stats["APEC"]["pertinentes"] += 1
                        
                        print(f"\n🔥 SUPER MATCH APEC ({final_score} pts) : {offer['title']}")
                        print(f"   🏢 {offer['company']} | 📍 {offer['location']} | 🕒 {offer.get('date', 'Récent')}")
                        print(f"   ⏳ Durée estimée : {duration}")
                        print(f"   🔑 Mots-clés : {', '.join(final_keywords).title()}")
                        print(f"   🔗 {offer['link']}\n")
                        send_discord_alert(DISCORD_WEBHOOK, offer['title'], offer['company'], offer['location'], duration, final_score, final_keywords, offer['link'])
                else:
                    print(f"   [Filtre] Offre écartée (Score trop bas : {score} pts) : {offer['title'][:40]}...")

                save_seen_job(offer['link'])
                seen_jobs.add(offer['link'])
    except Exception as e:
        print(f"⚠️ Erreur lors du scraping : {e}")
            
    finally:
        
        print("="*50)
        print(f"🏁 TERMINÉ. {matches_count} offres hautement pertinentes trouvées au total.")
        print("="*50)
        
        # Génération du graphique de stats
        # 1. On génère l'image et on récupère son nom
        image_filename = generate_stats_graph(bot_stats)
        
        # 2. On calcule le total pour le petit texte Discord
        total_scans = sum(plateforme["scannées"] for plateforme in bot_stats.values())
        
        # 3. On envoie sur Discord (vérifie que DISCORD_WEBHOOK contient bien ton URL)
        if total_scans > 0:
            send_discord_report(DISCORD_WEBHOOK, image_filename, total_scans, matches_count)
                    
        if driver:
            print("   └── 🛑 Fermeture de l'instance Chrome.")
            driver.quit()

   

if __name__ == "__main__":
    main()