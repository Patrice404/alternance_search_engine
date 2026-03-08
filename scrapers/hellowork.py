from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import urllib.parse
from settings import MAX_PAGES

def init_browser():
    """Initialise et retourne l'instance du navigateur."""
    print("   └── 🚀 Initialisation du navigateur Chrome...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    service = Service(executable_path='/usr/bin/chromedriver')
    return webdriver.Chrome(service=service, options=chrome_options)

def get_full_description(driver, url):
    """Va sur la page de l'offre et récupère tout le texte pour l'analyse."""
    try:
        driver.get(url)
        time.sleep(2) 
        body_text = driver.find_element(By.TAG_NAME, "body").text
        return body_text
    except Exception as e:
        print(f"   [Erreur de lecture de l'offre] {url}")
        return ""
    
def search_hellowork(driver, query="Alternance système réseau cybersécurité", date_filter="w", max_pages=MAX_PAGES):
    """
    Scrape les offres HelloWork.
    - date_filter : "w" (semaine), "d" (3 jours), "m" (mois)
    - max_pages : Limite de pages à explorer pour éviter un scan infini
    """
    # Encodage propre de la recherche (remplace les espaces par %20, etc.)
    safe_query = urllib.parse.quote(query)
    
    all_offers = []
    
    for page in range(1, max_pages + 1):
        url = f"https://www.hellowork.com/fr-fr/emploi/recherche.html?k={safe_query}&l=France&c=Alternance&cod=1-2y&d={date_filter}&p={page}"
        print(f"   └── 🌐 Scan HelloWork - Page {page} : {url}")

        try:
            driver.get(url)
            time.sleep(5) 
            
            # On ne clique sur la bannière cookie que sur la première page
            if page == 1:
                try:
                    cookie_btn = driver.find_element(By.ID, "hw-cc-notice-continue-without-accepting-btn")
                    driver.execute_script("arguments[0].click();", cookie_btn)
                    time.sleep(1)
                except:
                    pass

            job_cards = driver.find_elements(By.CSS_SELECTOR, "[data-cy='serpCard']")
            
            # SI LA PAGE EST VIDE : on a atteint la fin des résultats
            if len(job_cards) == 0:
                print(f"   └── 🛑 Fin des résultats atteinte. Aucune offre sur la page {page}.")
                break
                
            print(f"   └── 📦 {len(job_cards)} offres récentes détectées sur la page {page}.")

            for card in job_cards:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, "[data-cy='offerTitle']")
                    title = title_elem.text.strip()
                    link = title_elem.get_attribute("href")

                    try:
                        company = card.find_element(By.CSS_SELECTOR, "p.tw-typo-s.tw-inline").text.strip()
                    except:
                        company = "Confidentiel"

                    try:
                        location = card.find_element(By.CSS_SELECTOR, "[data-cy='localisationCard']").text.strip()
                    except:
                        location = "France"

                    try:
                        contract = card.find_element(By.CSS_SELECTOR, "[data-cy='contractCard']").text.strip()
                    except:
                        contract = "N/A"
                        
                    try:
                        date_posted = card.find_element(By.XPATH, ".//div[contains(text(), 'il y a') or contains(text(), 'heure') or contains(text(), 'jour')]").text.strip()
                    except:
                        date_posted = "Récent"

                    full_text_for_matching = f"{title} {company} {contract} {location}"

                    all_offers.append({
                        "title": title,
                        "company": company,
                        "description": full_text_for_matching,
                        "link": link,
                        "location": location,
                        "contract": contract,
                        "date": date_posted
                    })
                    
                except Exception as e:
                    continue

        except Exception as e:
            print(f"⚠️ Erreur lors du scraping de la page {page} : {e}")
            break 

    print(f"   └── ✅ Bilan HelloWork : {len(all_offers)} offres collectées au total.")
    return all_offers
