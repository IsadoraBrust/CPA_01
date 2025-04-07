from config.logging import setup_logging

import logging
import requests
from bs4 import BeautifulSoup
import time
import os
import json
import random
import pickle
import re

# Configuração do logger
setup_logging()
logger = logging.getLogger(__name__)

HTML_DIR = "saida_html"
JSON_DIR = "saida_json"
MAX_PAGINAS = 5000 
URL_INICIAL = "https://pt.wikipedia.org/wiki/Grammy_Awards"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Funções auxiliares
def salvar_progresso(links_visitados, contador, lista_links, proximo_link):
    """
    Função para salvar o progresso do crawler em um arquivo pickle.
    A cada 50 páginas coletadas no crawler, esta função é chamada e o progresso é salvo.

    :param links_visitados: Conjunto de links já visitados
    :param contador: Contador de páginas coletadas
    :param lista_links: Lista de links extraídos
    :param proximo_link: Próximo link a ser visitado
    """
    progresso = {
            'visitados': links_visitados,
            'contador': contador,
            'lista_links': lista_links,
            'proximo_link': proximo_link
    }
    with open('progresso.pkl', 'wb') as arq:
        pickle.dump(progresso, arq)

def carregar_progresso():
    """
    Função para carregar o progresso do crawler a partir de um arquivo pickle.
    Se o arquivo existir, os dados são carregados e retornados.

    :return: Dicionário com o progresso salvo, ou None se o arquivo não existir
    """
    try:
        with open('progresso.pkl', 'rb') as arq:
            progresso = pickle.load(arq)
            progresso['visitados'] = set(progresso['visitados'])
            return progresso
    except FileNotFoundError:
        return None

def tratar_nome_arquivo(nome_arquivo):
    return re.sub(r'[<>:"/\\|?*]', '_', nome_arquivo)  # Substitui caracteres inválidos para nomes de arquivos

## FUNÇÕES TAREFA 1:
# Função para salvar a página como um arquivo HTML
def salvar_pagina_html(url, titulo):
    if not os.path.exists(HTML_DIR): # Cria o diretório de saída html, se ele não existir
        os.makedirs(HTML_DIR)

    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        logger.info(f"Erro ao acessar: {url}. Status code: {response.status_code}")
        return None

    nome_arquivo = tratar_nome_arquivo(titulo)  # Trata o nome do arquivo para evitar caracteres inválidos
    caminho_arquivo = os.path.join(HTML_DIR, f"{nome_arquivo}.html")

    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(response.text)
    logger.info(f"Página salva: {caminho_arquivo}")

# Função para extrair links de uma página
def extrair_links(soup):
    todos_links = soup.find(id="bodyContent").find_all("a")
    links = []
    for link in todos_links:
        if 'href' in link.attrs and link['href'].startswith("/wiki/"):
            if ':' not in link['href']:  # Filtra links que não são verbetes
                links.append(link['href'])
    return links

# Função para escolher o próximo link não visitado
def escolher_proximo_link(links, visitados):
    for link in links:
        if link not in visitados:
            visitados.add(link)
            return link
    return None  # Retorna None se todos os links já foram visitados

def crawler_wikipedia(url_inicial):
    progresso = carregar_progresso() # Tenta carregar o progresso anterior
    if progresso:
        links_visitados = progresso['visitados']
        paginas_coletadas = progresso['contador']
        links = progresso['lista_links']
        proximo_link = progresso['proximo_link']
        logger.info(f"Retomando de {paginas_coletadas} páginas coletadas")
    else:
        links_visitados = set()
        paginas_coletadas = 0
        links = []
        proximo_link = url_inicial  # Começa pela página inicial

    
    while paginas_coletadas < MAX_PAGINAS:
        try:
            # 1. Obter a página
            response = requests.get(proximo_link, headers=HEADERS)

            if response.status_code == 429:  # Se receber erro 429 (Too Many Requests), aguarda e tenta novamente
                logger.info("Muitas requisições. Aguardando 10 segundos...")
                time.sleep(10)
                continue

            elif response.status_code != 200:
                logger.info(f"Erro ao acessar: {proximo_link}. Status code: {response.status_code}")
                links_visitados.add(proximo_link)  # Adiciona o link à lista de visitados
                proximo_link = escolher_proximo_link(links, links_visitados)
                if not proximo_link:
                    logger.info("Todos os links foram visitados.")
                    break
                continue # Tenta o próximo link


            soup = BeautifulSoup(response.content, "html.parser")

            # 2. Salvar a página como um arquivo HTML
            titulo = soup.select(".mw-page-title-main")
            nome_arquivo = titulo[0].text if titulo else f"pagina_{paginas_coletadas}" # Se não encontrar título, usa um padrão
            salvar_pagina_html(proximo_link, nome_arquivo)

            # 3. Marcar a página como visitada
            links_visitados.add(proximo_link) # Adiciona o link à lista de visitados
            paginas_coletadas += 1 
            logger.info(f"Páginas coletadas: {paginas_coletadas}")

            # 4. Extrair todos os links da página, sem sobrescrever links coletados anteriormente
            novos_links = extrair_links(soup)
            links.extend([link for link in novos_links if link not in links and link not in links_visitados]) # Adiciona apenas links novos, sem repetições

            if len(links) > 1000: # Limita o tamanho da lista para evitar sobrecarga de memória
                links = links[-1000:] # Mantém apenas os 1000 links mais recentes

            logger.info(f"Lista de próximos links: {len(links)}")            

            # 5. Escolher o próximo link não visitado
            proximo_link = escolher_proximo_link(links, links_visitados)
            if not proximo_link:
                logger.info("Todos os links foram visitados.")
                break
            
            logger.info(f"Próximo link: {proximo_link}")

            # 6. Atualizar o próximo link para a URL completa
            proximo_link = "https://pt.wikipedia.org" + proximo_link

            # 7. Salva o progresso a cada 50 páginas coletadas
            if paginas_coletadas % 50 == 0: 
                salvar_progresso(list(links_visitados), paginas_coletadas, links, proximo_link)
                logger.info(f"Progresso salvo: {paginas_coletadas} páginas coletadas.")
            
            # 8. Esperar um tempo aleatório para não sobrecarregar o servidor
            espera = random.uniform(5, 8)  # Escolhe um valor entre 5 e 8 segundos
            time.sleep(espera)


        except Exception as e:
            logger.info(f"Erro ao processar a página: {proximo_link}")
            logger.info(f"Detalhes do erro: {str(e)}")
            links_visitados.add(proximo_link)  # Adiciona o link com erro à lista de visitados
            proximo_link = escolher_proximo_link(links, links_visitados)
            if not proximo_link:
                break  # Para o loop se não houver mais links
            proximo_link = "https://pt.wikipedia.org" + proximo_link
            continue # Tenta o próximo link
            

    logger.info(f"Coleta concluída. Total de páginas coletadas: {paginas_coletadas}")


## FUNÇÕES TAREFA 2: 
def save_json(dados, output_dir, nome_arquivo):
    if not os.path.exists(output_dir): # Cria o diretório de saída JSON, se ele não existir
        os.makedirs(output_dir)
    
    caminho_arquivo = os.path.join(output_dir, f"{nome_arquivo}.json")
    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as arq:
            json.dump(dados, arq, ensure_ascii=False, indent=2)
        return caminho_arquivo
    except Exception as e:
        print(f"Erro ao salvar {nome_arquivo}: {str(e)}")
        return None

def get_infobox(pagina):
    # Devemos procurar por diferentes composições do nome da classe de "infobox"
    # Exemplo: 
        # Na página 'Alan Turing': aparece como "infobox infobox_v2"
        # Na página 'Ford Motor Company': aparece como "infobox infobox infobox_v2"
    box = pagina.find_all(attrs={"class": lambda x: x and 'infobox' in x}) 

    if not box:
        return None, None

    # 1. Extrair o título da Infobox
    # Exemplo da Wikipedia: //*[@id="mw-content-text"]/div[1]/table[1]/tbody/tr[1]/th/span
    title_th = box[0].find('th')
    if title_th:
        title_span = title_th.find('span')
        if title_span:
            title = title_span.get_text(strip=True)
        else:
            # Se não encontrar span, pega o texto direto do th
            title = title_th.get_text(strip=True)
    else:
        return None, None
    
    # 2. Processar conteúdo da Infobox
    infobox_data = {} # Dicionário de valores 
    
    for tag in box[0].find_all("tr"):
        if tag.find(attrs={"scope":"row"}):
            td_tags = tag.find_all("td")
            
            if len(td_tags) >= 2: # Se encontrar elemento {chave: valor}
                # Obter a primeira td (chave)
                # Tentativa 1:
                # filhos_chave = [filho for filho in td_tags[0].children if filho.name is not None or filho.strip()]
                # chave = ' '.join(filho.get_text(strip=True) for filho in filhos_chave if filho.get_text(strip=True))
                # Tentativa 2:
                chave = ' '.join(td_tags[0].stripped_strings)
                
                # Verifica se o valor é uma lista
                lista_valores = []
                if td_tags[1].find(['ul', 'ol']):
                    lista_valores = [li.get_text(strip=True) for li in td_tags[1].find_all('li')]
                
                # Se encontrou itens de lista
                if lista_valores:
                    infobox_data[chave] = lista_valores
                else:
                    # Para a segunda td (valor simples), se não for uma lista
                    # Tentativa 1:
                    # filhos_valor = [filho for filho in td_tags[1].children if filho.name is not None or filho.strip()]
                    # valor = ' '.join(filho.get_text(strip=True) for filho in filhos_valor if filho.get_text(strip=True))

                    # Tentativa 2:
                    valor = ' '.join(td_tags[1].stripped_strings)
                    if chave:
                        infobox_data[chave] = valor
    
    if not infobox_data: # Se não encontrou dados válidos na infobox, desconsidera esta infobox 
        return None, None

    return title, infobox_data

def file_reader(diretorio):
    resultados = {}
    
    for arquivo in os.listdir(diretorio):
        if arquivo.endswith(".html"):
            caminho_arquivo = os.path.join(diretorio, arquivo)

            try:
                with open(caminho_arquivo, 'r', encoding='utf-8') as arq:
                    soup = BeautifulSoup(arq.read(), "html.parser")
                    titulo, infobox = get_infobox(soup)
                    
                    resultados[arquivo] = {
                        'titulo_infobox': titulo if titulo is not None else None,
                        'tem_infobox': infobox is not None,
                        'conteudo_infobox': infobox
                    }
            
            except Exception as e:
                resultados[arquivo] = {
                    'erro': str(e),
                    'tem_infobox': False
                }
    
    return resultados
            
def process_infoboxes(diretorio, output_dir=JSON_DIR):
    count = 0
    # 1. Processa os arquivos html
    resultados = file_reader(diretorio)
    # 2. Salva os resultados em JSON
    for arquivo, info in resultados.items():
        if info["tem_infobox"] and info["conteudo_infobox"]:
            save_json(
                dados = info["conteudo_infobox"],
                output_dir = output_dir,
                nome_arquivo = info["titulo_infobox"]
            )
            count += 1
    
    print(f"Processamento concluído.\n {count} arquivo(s) com infoboxes.")
    
    return resultados


### EXECUÇÃO DAS TAREFAS ###

def main():
    # TAREFA 1: Iniciar o crawler com a URL inicial
    crawler_wikipedia(URL_INICIAL)

    # TAREFA 2: Extrair Infoboxes e exportar para JSON
    process_infoboxes(HTML_DIR)


if __name__ == "__main__":
    main()

