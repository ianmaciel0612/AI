import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configurações da Busca (Você pode mudar o nicho e o bairro/cidade aqui)
NICHO = "Barbearia"
CIDADE = "Tatuape Sao Paulo" # Mudar a região ajuda a achar novas lojas
BUSCA = f"{NICHO} em {CIDADE}"

print("Iniciando o navegador...")
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.maximize_window()

# Acessar o Google Maps
url = f"https://www.google.com/maps/search/{BUSCA.replace(' ', '+')}"
driver.get(url)
time.sleep(5)

print("Carregando lista ampliada de estabelecimentos no Maps...")

# Rolagem para carregar MAIS resultados (Aumentado para 10 rolagens)
try:
    painel = driver.find_element(By.XPATH, '//div[contains(@aria-label, "Resultados para")]')
    for _ in range(10):  # Rola mais vezes para pegar até 60-100 locais
        driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', painel)
        time.sleep(2)
except Exception:
    pass

# Pegar os links dos locais
elementos = driver.find_elements(By.XPATH, '//a[contains(@href, "https://www.google.com/maps/place")]')
links = list(set([elem.get_attribute('href') for elem in elementos if elem.get_attribute('href')]))

print(f"Total de locais encontrados para analisar: {len(links)}")
prospects = []

# Varredura refinada
for index, link in enumerate(links):
    driver.get(link)
    time.sleep(2) # Tempo para garantir carregamento
    
    # 1. Nome
    try:
        nome = driver.find_element(By.XPATH, '//h1').text
    except:
        nome = "N/A"
        
    # 2. Telefone
    try:
        botao_tel = driver.find_element(By.XPATH, '//button[contains(@data-item-id, "phone")]')
        telefone = botao_tel.text
    except:
        telefone = None
        
    # 3. Verificação de Site e Redes Sociais
    tem_site = False
    
    botoes_site = driver.find_elements(By.XPATH, '//a[contains(@data-item-id, "authority")]')
    if len(botoes_site) > 0:
        tem_site = True
    
    links_gerais = driver.find_elements(By.XPATH, '//a[contains(@href, "http")]')
    for l in links_gerais:
        href = l.get_attribute('href') or ""
        if any(dominio in href for dominio in ["instagram.com", "facebook.com", "linktr.ee", "ifood.com.br", "wa.me"]):
            tem_site = True
            break

    # FILTRO: Apenas se NÃO tiver site/redes E tiver telefone
    if not tem_site and telefone:
        prospects.append({
            'Nome': nome,
            'Telefone': telefone,
            'Link_Maps': link,
            'Status': 'Pendente'
        })
        print(f"[{index+1}/{len(links)}] [LEAD ENCONTRADO!] {nome} | Tel: {telefone}")
    else:
        razao = "Possui site/redes" if tem_site else "Sem telefone"
        print(f"[{index+1}/{len(links)}] [Ignorado - {razao}] {nome}")

driver.quit()

# Salvar arquivo CSV
if prospects:
    df = pd.DataFrame(prospects)
    df['Telefone_Limpo'] = df['Telefone'].str.replace(r'\D', '', regex=True)
    
    nome_arquivo = f"leads_{NICHO.lower()}_{CIDADE.lower().replace(' ', '_')}.csv"
    df.to_csv(nome_arquivo, index=False, encoding='utf-8-sig')
    print(f"\n--- Concluído! ---")
    print(f"Total de leads sem site salvos: {len(df)}")
    print(f"Salvo em: {nome_arquivo}")
else:
    print("\nNenhum lead sem site foi encontrado nessa busca.")