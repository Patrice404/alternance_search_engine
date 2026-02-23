from selenium.webdriver.common.by import By
import time
import urllib.parse
import re
from settings import APEC_QUERIES, ALTERNANCE_KEYWORDS, MAX_PAGES
from settings import ALTERNANCE_KEYWORDS



def get_full_description_apec(driver, url):
    """Deep Scan spécifique pour l'APEC."""
    try:
        driver.get(url)
        time.sleep(3) # On laisse Angular afficher la page
        
        # Fermeture des cookies OneTrust (très commun sur les sites FR)
        try:
            cookie_btn = driver.find_element(By.ID, "onetrust-reject-all-handler")
            driver.execute_script("arguments[0].click();", cookie_btn)
        except:
            pass

        # L'APEC a un code HTML assez propre, on vise le container principal
        try:
            main_content = driver.find_element(By.CSS_SELECTOR, "main, div.container-detail")
            return main_content.get_attribute("innerText")
        except:
            return driver.find_element(By.TAG_NAME, "body").get_attribute("innerText")

    except Exception as e:
        print("      [Erreur] Impossible de lire l'offre APEC.")
        return ""

def search_apec(driver, query="Cybersécurité", max_pages=MAX_PAGES):
    safe_query = urllib.parse.quote(query)
    offers = []
    
    print("   └── 🌐 Scan de l'APEC (Filtre Alternance activé)...")

    # L'APEC commence sa pagination à la page 0 !
    for page in range(max_pages):
        # Ajout du tri par date (sortsType=DATE) et de la récence (anciennetePublication=101850 dernières 24h, 101851 dernière semaine, 101852 dernier mois)
        url = f"https://www.apec.fr/candidat/recherche-emploi.html/emploi?typesContrat=20053&motsCles={safe_query}&sortsType=DATE&anciennetePublication=101851&page={page}"
        print(f"      └── Page {page + 1} : {url}")

        try:
            driver.get(url)
            time.sleep(5) 

            if page == 0:
                try:
                    cookie_btn = driver.find_element(By.ID, "onetrust-reject-all-handler")
                    driver.execute_script("arguments[0].click();", cookie_btn)
                    time.sleep(1)
                except:
                    pass

            job_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/detail-offre/']")
            
            if not job_links:
                print(f"      └── 🛑 Fin des résultats atteinte.")
                break
                
            seen_links_on_page = set()
            valid_cards = []
            
            for a_tag in job_links:
                href = a_tag.get_attribute("href")
                # On nettoie l'URL pour la mémoire, mais on garde la vraie pour cliquer
                base_href = href.split('?')[0] if href else ""
                
                if not base_href or base_href in seen_links_on_page:
                    continue
                seen_links_on_page.add(base_href)
                
                try:
                    # 🧗 L'algorithme grimpeur : on remonte les parents jusqu'à avoir la carte exacte
                    card_elem = a_tag
                    for _ in range(4): # On remonte de 4 niveaux maximum
                        parent = driver.execute_script("return arguments[0].parentElement;", card_elem)
                        if parent:
                            # Si le parent contient plus de 1000 caractères, c'est qu'on a touché la liste globale. On stoppe.
                            if len(parent.get_attribute("innerText")) > 1000:
                                break
                            card_elem = parent
                            
                    card_text = card_elem.get_attribute("innerText")
                    lines = [line.strip() for line in card_text.split('\n') if line.strip()]
                    
                    if len(lines) < 2:
                        continue
                        
                    # On ignore les premières lignes si ce sont des badges ("Nouveau", Dates...)
                    idx = 0
                    while idx < len(lines) and (lines[idx].lower() in ["nouveau", "urgent"] or "/" in lines[idx] or "publié" in lines[idx].lower() or "il y a" in lines[idx].lower()):
                        idx += 1
                        
                    if idx + 1 < len(lines):
                        company = lines[idx][:40]
                        title = lines[idx+1][:80]
                    else:
                        title = lines[0][:80]
                        company = "Confidentiel"

                    # Nettoyage d'affichage basique
                    company = company.replace("Entreprise", "").strip()

                    full_text_for_matching = " ".join(lines)
                    valid_cards.append((title, company, full_text_for_matching, href))
                except:
                    continue

            print(f"      └── 📦 {len(valid_cards)} offres détectées sur cette page.")

            for title, company, full_text, link in valid_cards:
                offers.append({
                    "title": title, 
                    "company": company, 
                    "description": full_text,
                    "link": link,
                    "location": "France", 
                    "date": "Récent",
                    "source": "APEC"
                })

        except Exception as e:
            print(f"⚠️ Erreur lors du scraping APEC (Page {page + 1}) : {e}")
            break

    return offers