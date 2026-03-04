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
        
    match_mois = re.search(r"(?i)\b(12|24|36)\s*mois\b", text)
    if match_mois:
        return match_mois.group(0).lower()
        
    match_ans = re.search(r"(?i)(?:durée|contrat|alternance).{0,30}\b([123]\s*an[s]?)\b", text)
    if match_ans:
        return match_ans.group(1).lower()
        
    return "Non précisée"


def load_seen_titles(filepath='data/seen_titles.json'):
    """Charge le dictionnaire associant les entreprises à leurs titres d'offres déjà vus."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_seen_title(company, title, seen_dict, filepath='data/seen_titles.json'):
    """Sauvegarde le titre pour cette entreprise afin d'éviter les spams."""
    comp_norm = company.strip().lower()
    title_norm = title.strip().lower()
    
    # On ignore les entreprises anonymes pour éviter de bloquer plusieurs vraies entreprises
    if not comp_norm or comp_norm in ["confidentiel", "anonyme"]:
        return

    if comp_norm not in seen_dict:
        seen_dict[comp_norm] = []
        
    if title_norm not in seen_dict[comp_norm]:
        seen_dict[comp_norm].append(title_norm)
        # On sauvegarde dans le fichier JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(seen_dict, f, ensure_ascii=False, indent=4)

# ==========================================

def valid_offer(offer, seen_jobs, seen_titles):
    """Vérifie si l'offre doit être traitée ou écartée d'office."""
    if offer['link'] in seen_jobs:
        return False  # Offre déjà vue via son URL
        
    company_name = offer.get('company', '').lower().strip()
    title_norm = offer.get('title', '').lower().strip()
    
    # 1. Vérification : Écoles de la liste noire
    if any(school.lower() in company_name for school in SCHOOL_NAME):
        print(f"   [Filtre] Écarté (École détectée) : {offer['title']} chez {offer['company']}")
        save_seen_job(offer['link'])
        seen_jobs.add(offer['link'])
        return False
        
    # 2. Vérification des spams (même titre par la même entreprise)
    if company_name and company_name not in ["confidentiel", "anonyme"]:
        if company_name in seen_titles and title_norm in seen_titles[company_name]:
            print(f"   [Filtre] Écarté (Spam Titre/Entreprise) : {offer['title']} chez {offer['company']}")
            save_seen_job(offer['link'])
            seen_jobs.add(offer['link'])
            return False
    
    return True

def load_seen_jobs(filepath='data/seen_jobs.txt'):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return set(f.read().splitlines())
    return set()

def save_seen_job(url, filepath='data/seen_jobs.txt'):
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(f"{url}\n")
        
def extract_pure_keywords(profile):
    keywords = []
    for category in profile['competences'].values():
        for skill in category:
            main_part = skill.split('(')[0].strip().lower()
            if '/' in main_part:
                parts = main_part.split('/')
                for p in parts:
                    keywords.append(p.strip())
            else:
                keywords.append(main_part)
            
            if '(' in skill and ')' in skill:
                inner_part = skill.split('(')[1].split(')')[0]
                inner_words = inner_part.replace('/', '&').split('&')
                for w in inner_words:
                    keywords.append(w.strip().lower())
    return list(set([k for k in keywords if k]))

def calculate_match_score(job_data, pure_keywords):
    score = 0
    keywords_found = []
    content_to_analyze = (job_data['title'] + " " + job_data['description']).lower()
    
    for skill in pure_keywords:
        search_term = f" {skill} " if len(skill) <= 2 else skill
        if search_term in content_to_analyze:
            score += 5
            keywords_found.append(skill)
            
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
    
    bot_stats = {
        "HelloWork": {"scannées": 0, "pertinentes": 0},
        "LaBonneAlternance": {"scannées": 0, "pertinentes": 0},
        "LinkedIn": {"scannées": 0, "pertinentes": 0},
        "WTTJ": {"scannées": 0, "pertinentes": 0},
        "APEC": {"scannées": 0, "pertinentes": 0}
    }
    
    seen_jobs = load_seen_jobs()
    seen_titles = load_seen_titles()
    
    print(f"🧠 Mémoire chargée : {len(seen_jobs)} liens et titres enregistrés pour {len(seen_titles)} entreprises.")

    print("==================================================")
    print("🔎 DÉMARRAGE DU MOTEUR DE RECHERCHE D'ALTERNANCE")
    print("==================================================")
    
    driver = init_browser()
    
    try:
        # ------------------------------------------------
        # 1. SCAN DE HELLOWORK
        # ------------------------------------------------
        print("\n▶️ PLATEFORME 1 : HELLOWORK")
        for query in HELLOWORK_QUERIES:
            print(f"   └── 🌐 Recherche HelloWork : {query}")
            hw_offers = search_hellowork(driver, query)
            bot_stats["HelloWork"]["scannées"] += len(hw_offers) 
            
            for offer in hw_offers:
                # 🎯 NOUVEAU : Ajout de seen_titles dans les paramètres
                if not valid_offer(offer, seen_jobs, seen_titles):
                    continue
                        
                score, _ = calculate_match_score(offer, pure_keywords)
                if score >= MATCH_TITLES_SCORE: 
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
                        send_discord_alert(DISCORD_WEBHOOK, offer['title'], offer['company'], offer['location'], offer.get('date', 'Récent'), final_score, final_keywords, offer['link'], duration)
                
                save_seen_job(offer['link'])
                seen_jobs.add(offer['link'])
                save_seen_title(offer['company'], offer['title'], seen_titles) 
       
        # ------------------------------------------------
        # 2. SCAN DE LA BONNE ALTERNANCE
        # ------------------------------------------------
        print("\n▶️ PLATEFORME 2 : LA BONNE ALTERNANCE")
        lba_offers = search_lba()
        bot_stats["LaBonneAlternance"]["scannées"] += len(lba_offers)
        
        for offer in lba_offers:
            if not valid_offer(offer, seen_jobs, seen_titles):
                continue
            
            final_score, final_keywords = calculate_match_score(offer, pure_keywords)
            
            if final_score >= SUPER_MATCH_THRESHOLD:
                matches_count += 1
                bot_stats["LaBonneAlternance"]["pertinentes"] += 1
                print(f"\n🔥 SUPER MATCH LBA ({final_score} pts) : {offer['title']}")
                print(f"   🏢 {offer['company']} | 📍 {offer['location']} | 🕒 {offer.get('date', 'Récent')}")
                print(f"   🔑 Mots-clés : {', '.join(final_keywords).title()}")
                print(f"   🔗 {offer['link']}\n")
                send_discord_alert(DISCORD_WEBHOOK, offer['title'], offer['company'], offer['location'], offer.get('date', 'Récent'), final_score, final_keywords, offer['link'], "Non précisée")
            
            save_seen_job(offer['link'])
            seen_jobs.add(offer['link'])
            save_seen_title(offer['company'], offer['title'], seen_titles) 
            
        # ------------------------------------------------
        # 3. SCAN DE LINKEDIN
        # ------------------------------------------------
        print("\n▶️ PLATEFORME 3 : LINKEDIN")
        for query in LINKEDIN_QUERIES:
            print(f"   └── 🌐 Recherche LinkedIn : {query}")
            linkedin_offers = search_linkedin(driver, query)
            bot_stats["LinkedIn"]["scannées"] += len(linkedin_offers)
            
            for offer in linkedin_offers:
                if not valid_offer(offer, seen_jobs, seen_titles):
                    continue
                    
                score, _ = calculate_match_score(offer, pure_keywords)
                if score >= MATCH_TITLES_SCORE: 
                    print(f"   [Deep Scan] Analyse de : {offer['title'][:60]}... chez {offer['company']}")
                    full_text = get_full_description_linkedin(driver, offer['link'])
                    offer['description'] = full_text
                    duration = extract_duration(full_text)
                    final_score, final_keywords = calculate_match_score(offer, pure_keywords)
                    print(f"   └── Résultat : {final_score} pts | {len(final_keywords)} compétences (Texte lu : {len(full_text)} car.)")
                    
                    if final_score >= SUPER_MATCH_THRESHOLD: 
                        matches_count += 1
                        bot_stats["LinkedIn"]["pertinentes"] += 1
                        print(f"\n🔥 SUPER MATCH LINKEDIN ({final_score} pts) : {offer['title']}")
                        print(f"   🏢 {offer['company']} | 📍 {offer['location']} | 🕒 {offer.get('date', 'Récent')}")
                        print(f"   ⏳ Durée estimée : {duration}")
                        print(f"   🔑 Mots-clés : {', '.join(final_keywords).title()}")
                        print(f"   🔗 {offer['link']}\n")
                        send_discord_alert(DISCORD_WEBHOOK, offer['title'], offer['company'], offer['location'], offer.get('date', 'Récent'), final_score, final_keywords, offer['link'], duration)
                
                save_seen_job(offer['link'])
                seen_jobs.add(offer['link'])  
                save_seen_title(offer['company'], offer['title'], seen_titles) 
        
        # ------------------------------------------------
        # 4. SCAN DE WELCOME TO THE JUNGLE
        # ------------------------------------------------
        print("\n▶️ PLATEFORME 4 : WELCOME TO THE JUNGLE")
        for query in WTTJ_QUERIES:
            print(f"   └── 🌐 Recherche WTTJ : {query}")
            wttj_offers = search_wttj(driver, query)
            bot_stats["WTTJ"]["scannées"] += len(wttj_offers)
            
            for offer in wttj_offers:
                if not valid_offer(offer, seen_jobs, seen_titles):
                    continue
                    
                score, _ = calculate_match_score(offer, pure_keywords)
                if score >= MATCH_TITLES_SCORE: 
                    print(f"   [Deep Scan] Analyse de : {offer['title'][:60]}... chez {offer['company']}")
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
                        send_discord_alert(DISCORD_WEBHOOK, offer['title'], offer['company'], offer['location'], offer.get('date', 'Récent'), final_score, final_keywords, offer['link'], duration)
                
                save_seen_job(offer['link'])
                seen_jobs.add(offer['link'])
                save_seen_title(offer['company'], offer['title'], seen_titles)
            
         # ------------------------------------------------
        # 5. SCAN DE L'APEC
        # ------------------------------------------------
        print("\n▶️ PLATEFORME 5 : APEC")
        for query in APEC_QUERIES:
            print(f"   └── 🌐 Recherche APEC : {query}")
            apec_offers = search_apec(driver, query) 
            bot_stats["APEC"]["scannées"] += len(apec_offers)
            
            for offer in apec_offers:
                if not valid_offer(offer, seen_jobs, seen_titles):
                    continue
                    
                score, _ = calculate_match_score(offer, pure_keywords)
                if score >= MATCH_TITLES_SCORE: 
                    print(f"   [Deep Scan] Analyse de : {offer['title']}...")
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
                        send_discord_alert(DISCORD_WEBHOOK, offer['title'], offer['company'], offer['location'], offer.get('date', 'Récent'), final_score, final_keywords, offer['link'], duration)
                else:
                    print(f"   [Filtre] Offre écartée (Score trop bas : {score} pts) : {offer['title'][:40]}...")

                save_seen_job(offer['link'])
                seen_jobs.add(offer['link'])
                save_seen_title(offer['company'], offer['title'], seen_titles) 
                
    except Exception as e:
        print(f"⚠️ Erreur lors du scraping : {e}")
            
    finally:
        if driver:
            print("   └── 🛑 Fermeture de l'instance Chrome.")
            driver.quit()
        
        print("="*80)
        print(f"🏁 TERMINÉ. {matches_count} offres hautement pertinentes trouvées au total.")
        print("="*80)
        
        image_filename = generate_stats_graph(bot_stats)
        total_scans = sum(plateforme["scannées"] for plateforme in bot_stats.values())
        
        if total_scans > 0:
            send_discord_report(DISCORD_WEBHOOK, image_filename, total_scans, matches_count)

if __name__ == "__main__":
    main()