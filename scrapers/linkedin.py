from selenium.webdriver.common.by import By
import time
import urllib.parse

def get_full_description_linkedin(driver, url):
    """Deep Scan spécifique pour LinkedIn - Version "Force Brute"."""
    try:
        driver.get(url)
        time.sleep(3) # On laisse le temps à la page et aux pop-ups de s'afficher
        
        # 1. Tenter de fermer le pop-up de connexion "Rejoignez LinkedIn" s'il apparaît
        try:
            close_btn = driver.find_element(By.CSS_SELECTOR, "button.modal__dismiss")
            driver.execute_script("arguments[0].click();", close_btn)
            time.sleep(1)
        except:
            pass

        # 2. Tenter de cliquer sur "En voir plus" pour dérouler tout le texte
        try:
            show_more_btn = driver.find_element(By.CSS_SELECTOR, "button.show-more-less-html__button")
            driver.execute_script("arguments[0].click();", show_more_btn)
            time.sleep(1)
        except:
            pass 

        # 3. Extraction par force brute : on prend tout le texte de la balise <main>
        try:
            main_content = driver.find_element(By.TAG_NAME, "main")
            extracted_text = main_content.get_attribute("innerText")
            
            # Petit log de debug invisible pour vérifier si on récupère bien du texte
            if len(extracted_text) < 100:
                print("      [Debug] ⚠️ Le texte extrait semble anormalement court ou vide.")
                
            return extracted_text
        except:
            # Fallback absolu si <main> n'existe pas
            body_content = driver.find_element(By.TAG_NAME, "body")
            return body_content.get_attribute("innerText")

    except Exception as e:
        return ""
    
def search_linkedin(driver, query="Alternance Cybersécurité", max_scrolls=2):
    # Encodage de la recherche
    safe_query = urllib.parse.quote(query)
    # f_TPR=r604800 -> Filtre : Moins d'une semaine (7 jours = 604800 secondes)
    url = f"https://www.linkedin.com/jobs/search/?keywords={safe_query}&location=France&f_TPR=r604800"
    
    offers = []
    print(f"   └── 🌐 Scan de LinkedIn (Filtre: < 1 semaine) : {url}")

    try:
        driver.get(url)
        time.sleep(5) # Laisser le temps de charger

        # Simulation de scroll pour charger plus d'offres
        print("   └── 📜 Scroll automatique pour charger les offres...")
        for _ in range(max_scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        # Les cartes d'offres en mode déconnecté ont généralement cette classe
        job_cards = driver.find_elements(By.CSS_SELECTOR, "div.base-card")
        print(f"   └── 📦 {len(job_cards)} offres détectées sur LinkedIn.")

        for card in job_cards:
            try:
                # Extraction du titre
                title_elem = card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title")
                title = title_elem.get_attribute("innerText").strip()
                
                # Si le titre est complètement vide, on passe
                if not title:
                    continue

                # NOUVEAU FILTRE STRICT : On vérifie que c'est bien une alternance
                title_lower = title.lower()
                alternance_keywords = ["alternant(e)","alternante","alternant","alternance", "apprenti", "apprentissage", "pro", "professionnalisation"]
                
                # Si AUCUN de ces mots n'est dans le titre, on jette l'offre directement
                if not any(word in title_lower for word in alternance_keywords):
                    print(f"   [Filtre] Écarté (Pas une alternance) : {title[:40]}...")
                    continue
                
                try:
                    # Utilisation de get_attribute("innerText") au lieu de .text
                    title_elem = card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title")
                    title = title_elem.get_attribute("innerText").strip()
                    
                    try:
                        link_elem = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link")
                        link = link_elem.get_attribute("href").split('?')[0]
                    except:
                        continue 

                    try:
                        company_elem = card.find_element(By.CSS_SELECTOR, "h4.base-search-card__subtitle")
                        company = company_elem.get_attribute("innerText").strip()
                    except:
                        company = "Confidentiel"

                    try:
                        location_elem = card.find_element(By.CSS_SELECTOR, "span.job-search-card__location")
                        location = location_elem.get_attribute("innerText").strip()
                    except:
                        location = "France"

                    try:
                        date_elem = card.find_element(By.CSS_SELECTOR, "time")
                        date_posted = date_elem.get_attribute("innerText").strip()
                    except:
                        date_posted = "Récent"

                    # Si le titre est complètement vide (parfois LinkedIn met des cartes pubs invisibles)
                    if not title:
                        continue

                    full_text_for_matching = f"{title} {company} {location}"
                    offers.append({
                        "title": title,
                        "company": company,
                        "description": full_text_for_matching,
                        "link": link,
                        "location": location,
                        "date": date_posted,
                        "source": "LinkedIn"
                    })
                except Exception as e:
                    continue   
            except Exception as e:
                continue
    except Exception as e:
        print(f"⚠️ Erreur lors du scraping LinkedIn : {e}")

    return offers