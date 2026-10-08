import logging
import os
import time

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from logs import Logger


WAIT_SPEED = 1.0


logger = Logger.get_logger(__name__)
logger.setLevel(logging.DEBUG)


def esperar(segundos: float) -> None:
    time.sleep(segundos / WAIT_SPEED)


load_dotenv()


def delete_cache(driver):
    driver.execute_script("window.open('');")
    esperar(1)
    driver.switch_to.window(driver.window_handles[-1])
    esperar(1)
    driver.get("chrome://settings/clearBrowserData")
    esperar(1)
    actions = ActionChains(driver)
    actions.send_keys(Keys.TAB * 3 + Keys.DOWN * 3)
    actions.perform()
    esperar(1)
    actions = ActionChains(driver)
    actions.send_keys(Keys.TAB * 4 + Keys.ENTER)
    actions.perform()
    esperar(2)
    driver.close()
    driver.switch_to.window(driver.window_handles[0])


def deletar_comentario_atual(driver, wait, artigo, overflow_menu):
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            artigo,
        )
        esperar(1)

        driver.execute_script(
            """
            const menu = arguments[0];
            const shadow = menu.shadowRoot;
            if (shadow) {
                const trigger = shadow.querySelector('#overflow-trigger') || shadow.querySelector('button');
                if (trigger) trigger.click();
            } else {
                menu.click();
            }
            """,
            overflow_menu,
        )
        logger.info("[1/3] Menu de opções aberto.")
        esperar(1)

        try:
            opcao_apagar = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "li.delete-comment-menu-button, faceplate-tracker[noun='delete']",
                    )
                )
            )
            opcao_apagar.click()
        except (TimeoutException, NoSuchElementException):
            opcao_deletar = driver.find_element(
                By.XPATH, "//span[contains(text(), 'Delete comment')]"
            )
            driver.execute_script("arguments[0].click();", opcao_deletar)

        logger.info("[2/3] Opção 'Delete comment' clicada.")

        btn_confirmar_delete = wait.until(
            EC.element_to_be_clickable((By.ID, "deleteBtn"))
        )
        btn_confirmar_delete.click()
        logger.info("[3/3] Confirmação efetuada: comentário deletado.")

        esperar(2)

    except Exception:
        logger.exception("Erro ao tentar deletar o comentário.")


def processar_artigos(driver):
    processados = set()

    while True:
        artigos = driver.find_elements(By.TAG_NAME, "article")
        novos_encontrados = False

        for artigo in artigos:
            artigo_id = artigo.get_attribute("id") or artigo.get_attribute("outerHTML")[:50]

            if artigo_id in processados:
                continue

            novos_encontrados = True

            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                artigo,
            )
            esperar(1)

            try:
                overflow_menu = artigo.find_element(
                    By.CSS_SELECTOR, "shreddit-overflow-menu"
                )

                deletar_comentario_atual(driver, wait, artigo, overflow_menu)

                driver.execute_script(
                    "arguments[0].style.border = '3px solid #00ff00';",
                    artigo,
                )
                processados.add(artigo_id)
                esperar(2)

            except Exception:
                logger.exception("Não foi possível clicar no menu deste artigo.")
                processados.add(artigo_id)

        driver.execute_script("window.scrollBy(0, 600);")
        esperar(3)

        if not novos_encontrados:
            logger.info("Nenhum novo artigo encontrado nesta rolagem.")
            break


usuario = os.getenv("USERNAME_REDDIT")
senha = os.getenv("PASSWORD_REDDIT")
logger.info("Usuário configurado: %s", usuario)

options = Options()
options.browser_version = "stable"
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_experimental_option("detach", True)
assert options.capabilities["browserVersion"] == "stable"
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

logger.info("Iniciando o processo de login no Reddit.")
delete_cache(driver)
try:
    logger.info("Acessando a página de login do Reddit.")
    driver.get("https://www.reddit.com")
    esperar(0.5)
    login_button = wait.until(
        EC.visibility_of_element_located((By.ID, "login-button"))
    )
    logger.info("Botão de login encontrado. Clicando no botão.")
    login_button.click()
    logger.info("Botão de login clicado. Aguardando o formulário de login.")
    esperar(0.5)
    input_usuario = wait.until(
        EC.visibility_of_element_located((By.NAME, "username"))
    )

    logger.info("Preenchendo nome de usuário.")
    esperar(0.5)
    input_usuario.send_keys(usuario)

    password_field = wait.until(
        EC.visibility_of_element_located((By.NAME, "password"))
    )
    logger.info("Preenchendo senha.")
    esperar(0.5)
    password_field.send_keys(senha)
    quantidade_de_scrolls = 20
    btn_login = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Log In')]"))
    )
    btn_login.click()
    logger.info("Enviando formulário.")
    esperar(4)
    logger.info("Login bem-sucedido. Aguardando a página carregar.")

    driver.get(f"https://www.reddit.com/user/{usuario}/comments/")
    esperar(0.5)

    processar_artigos(driver)

except Exception:
    logger.exception("Erro ao acessar a página de login.")
    raise
