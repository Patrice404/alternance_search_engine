from selenium.webdriver.common.by import By
import time
import urllib.parse

def get_full_description_wttj(driver, url):
    """Deep Scan spécifique pour Welcome to the Jungle."""
    try:
        driver.get(url)
        time.sleep(3) 
        
        try:
            close_btn = driver.find_element(By.CSS_SELECTOR, "button[data-testid='login-modal-close-button']")
            driver.execute_script("arguments[0].click();", close_btn)
            time.sleep(1)
        except:
            pass

        try:
            main_content = driver.find_element(By.TAG_NAME, "main")
            return main_content.get_attribute("innerText")
        except:
            return driver.find_element(By.TAG_NAME, "body").get_attribute("innerText")

    except Exception as e:
        print("      [Erreur] Impossible de lire l'offre WTTJ.")
        return ""

def search_wttj(driver, query="Cybersécurité", max_pages=2):
    safe_query = urllib.parse.quote(query)
    offers = []
    
    print("   └── 🌐 Scan de Welcome to the Jungle (Alternance & France)...")

    # Boucle de pagination grâce à ton URL !
    for page in range(1, max_pages + 1):
        # L'URL exacte que tu as trouvée, avec l'injection du numéro de page
        url = f"https://www.welcometothejungle.com/fr/jobs?query={safe_query}&sortBy=mostRecent&refinementList%5Boffices.country_code%5D%5B%5D=FR&refinementList%5Bcontract_type%5D%5B%5D=apprenticeship&page={page}"
        print(f"      └── Page {page} : {url}")

        try:
            driver.get(url)
            time.sleep(5) # WTTJ est très lourd à charger

            # Gérer les cookies uniquement sur la première page
            if page == 1:
                try:
                    cookie_btn = driver.find_element(By.ID, "axeptio_btn_acceptAll")
                    driver.execute_script("arguments[0].click();", cookie_btn)
                    time.sleep(1)
                except:
                    pass

            list_items = driver.find_elements(By.TAG_NAME, "li")
            job_cards = []
            
            for li in list_items:
                try:
                    a_tag = li.find_element(By.TAG_NAME, "a")
                    href = a_tag.get_attribute("href")
                    if href and "/companies/" in href and "/jobs/" in href:
                        job_cards.append((li, href))
                except:
                    continue
            
            # Si on ne trouve plus d'offres, on arrête de scroller les pages
            if not job_cards:
                print(f"      └── 🛑 Fin des résultats atteinte à la page {page}.")
                break

            print(f"      └── 📦 {len(job_cards)} offres détectées sur cette page.")

            for card_elem, link in job_cards:
                try:
                    card_text = card_elem.get_attribute("innerText").split('\n')
                    clean_text = [t.strip() for t in card_text if t.strip()]
                    
                    if not clean_text:
                        continue
                    
                    try:
                        company_slug = link.split('/companies/')[1].split('/')[0]
                        company = company_slug.replace('-', ' ').title() 
                    except:
                        company = "Entreprise Tech"

                    title = clean_text[0]
                    if title.lower() in ["recrute activement !", "sponsorisé", "nouveau"]:
                        title = clean_text[1] if len(clean_text) > 1 else "Titre inconnu"
                    
                    full_text_for_matching = " ".join(clean_text)

                    offers.append({
                        "title": title,
                        "company": company,
                        "description": full_text_for_matching,
                        "link": link,
                        "location": "Voir sur l'offre", 
                        "date": "Récent",
                        "source": "WTTJ"
                    })
                    
                except Exception as e:
                    continue

        except Exception as e:
            print(f"⚠️ Erreur lors du scraping WTTJ (Page {page}) : {e}")
            break

    return offers