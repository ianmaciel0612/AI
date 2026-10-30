import pandas as pd
import time
import urllib.parse
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configurações
NOME_ARQUIVO_CSV = "leads_barbearia_tatuape_sao_paulo.csv" # Verifique se o nome do CSV está correto
LIMITE_POR_SESSAO = 10

try:
    df = pd.read_csv(NOME_ARQUIVO_CSV)
except FileNotFoundError:
    print(f"Erro: O arquivo '{NOME_ARQUIVO_CSV}' não foi encontrado na pasta.")
    exit()

print("Iniciando o navegador...")
options = webdriver.ChromeOptions()

pasta_perfil = os.path.join(os.getcwd(), "sessao_whatsapp")
options.add_argument(f"--user-data-dir={pasta_perfil}")
options.add_argument("--remote-allow-origins=*")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.maximize_window()

driver.get("https://web.whatsapp.com")
print("\nAguardando carregamento do WhatsApp Web...")

time.sleep(5)
input("\n>>> Se o WhatsApp Web já estiver carregado, pressione ENTER no terminal para iniciar os disparos... ")

envios_realizados = 0

for index, row in df.iterrows():
    if envios_realizados >= LIMITE_POR_SESSAO:
        print(f"\n--- Limite de {LIMITE_POR_SESSAO} envios atingido para esta sessão! ---")
        break

    nome_loja = str(row['Nome'])
    telefone = str(row['Telefone_Limpo'])
    
    if telefone.endswith('.0'):
        telefone = telefone[:-2]
        
    status = str(row.get('Status', 'Pendente'))
    
    if status == 'Enviado':
        continue
        
    if not telefone.startswith("55"):
        telefone = "55" + telefone
        
    mensagem = (
        f"Olá! Tudo bem? Passando por aqui porque vi o perfil da *{nome_loja}* no Google Maps. "
        f"Notei que vocês têm ótimas avaliações, mas ainda não possuem um site oficial cadastrado.\n\n"
        f"Hoje em dia, ter um site ajuda muito a passar mais credibilidade e a mostrar seus serviços/preços para quem pesquisa na sua região.\n\n"
        f"Eu desenvolvo sites otimizados para negócios locais. Se fizer sentido para você, posso te mandar 2 exemplos rápidos de como ficaria um site para a *{nome_loja}*?"
    )

    texto_url = urllib.parse.quote(mensagem)
    link_whatsapp = f"https://web.whatsapp.com/send?phone={telefone}&text={texto_url}"
    
    print(f"\n[{envios_realizados + 1}/{LIMITE_POR_SESSAO}] Enviando para: {nome_loja} ({telefone})...")
    
    try:
        driver.get(link_whatsapp)
        
        # Espera até 15 segundos para a caixa de texto do WhatsApp estar visível e clicável
        wait = WebDriverWait(driver, 15)
        caixa_texto = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//footer//div[@contenteditable="true"]'))
        )
        
        time.sleep(1)
        caixa_texto.send_keys(Keys.ENTER)
        time.sleep(2)
        
        envios_realizados += 1
        print(f"[SUCESSO {envios_realizados}/{LIMITE_POR_SESSAO}] Mensagem enviada para {nome_loja}!")
        
        df.at[index, 'Status'] = 'Enviado'
        df.to_csv(NOME_ARQUIVO_CSV, index=False, encoding='utf-8-sig')
        
        tempo_espera = random.randint(4, 8)
        print(f"Aguardando {tempo_espera} segundos...")
        time.sleep(tempo_espera)
        
    except Exception as e:
        print(f"[ERRO] Não foi possível enviar para {nome_loja}. O chat não carregou ou o número é inválido.")
        df.at[index, 'Status'] = 'Erro/Sem WhatsApp'
        df.to_csv(NOME_ARQUIVO_CSV, index=False, encoding='utf-8-sig')
        time.sleep(2)

print(f"\nSessão finalizada! Total de mensagens enviadas nesta rodada: {envios_realizados}")
driver.quit()