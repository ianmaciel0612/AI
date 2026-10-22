import pandas as pd
import time
import urllib.parse
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configurações
# 1. Carregar a lista de leads gerada pelo scraper
NOME_ARQUIVO_CSV = "leads_barbearia_tatuape_sao_paulo.csv"  # <--- Coloque o nome do seu arquivo aqui entre as aspas
LIMITE_POR_SESSAO = 10  # Limite máximo de disparos por execução

try:
    df = pd.read_csv(NOME_ARQUIVO_CSV)
except FileNotFoundError:
    print(f"Erro: O arquivo '{NOME_ARQUIVO_CSV}' não foi encontrado na pasta.")
    exit()

print("Iniciando o navegador...")
options = webdriver.ChromeOptions()

# SALVA A SESSÃO DO WHATSAPP NUMA PASTA LOCAL (Não pede QR Code depois de logar 1x)
pasta_perfil = os.path.join(os.getcwd(), "sessao_whatsapp")
options.add_argument(f"--user-data-dir={pasta_perfil}")

options.add_argument("--remote-allow-origins=*")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.maximize_window()

# Abre o WhatsApp Web
driver.get("https://web.whatsapp.com")
print("\nAguardando carregamento do WhatsApp Web...")

# Verifica se precisa escaneamento de QR Code ou se já está logado
time.sleep(5)
input("\n>>> Se for a PRIMEIRA vez, escaneie o QR Code. Se JÁ ESTIVER LOGADO, apenas aguarde carregar e aperte ENTER no terminal: ")

envios_realizados = 0

# Iterar sobre a lista de leads
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
        
    # Mensagem personalizada
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
        time.sleep(5)  # Espera rápida para carregar o chat
        
        caixa_texto = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@aria-placeholder="Digite uma mensagem"]')
        caixa_texto.send_keys(Keys.ENTER)
        time.sleep(1)
        
        envios_realizados += 1
        print(f"[SUCESSO {envios_realizados}/{LIMITE_POR_SESSAO}] Mensagem enviada para {nome_loja}!")
        
        df.at[index, 'Status'] = 'Enviado'
        df.to_csv(NOME_ARQUIVO_CSV, index=False, encoding='utf-8-sig')
        
        # Intervalo rápido (~5 segundos)
        tempo_espera = random.randint(3, 7)
        print(f"Aguardando {tempo_espera} segundos...")
        time.sleep(tempo_espera)
        
    except Exception as e:
        print(f"[ERRO] Não foi possível enviar para {nome_loja}. Verifique se o número é válido no WhatsApp.")
        df.at[index, 'Status'] = 'Erro/Sem WhatsApp'
        df.to_csv(NOME_ARQUIVO_CSV, index=False, encoding='utf-8-sig')
        time.sleep(2)

print(f"\nSessão finalizada! Total de mensagens enviadas nesta rodada: {envios_realizados}")
driver.quit()