import requests
from bs4 import BeautifulSoup
import time
import os
import json

HTML_DIR = "saida_html"
JSON_DIR = "saida_json"
MAX_PAGINAS = 5 # Valor de teste inicial 
URL_INICIAL = "https://pt.wikipedia.org/wiki/Grammy_Awards"

# Função para salvar a página como um arquivo HTML
def salvar_pagina_html(url, titulo):
    if not os.path.exists(HTML_DIR): # Cria o diretório de saída html, se ele não existir
        os.makedirs(HTML_DIR)

    response = requests.get(url)
    caminho_arquivo = os.path.join(HTML_DIR, f"{titulo}.html")

    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"Página salva: {caminho_arquivo}")

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
            return link
    return None  # Retorna None se todos os links já foram visitados

def crawler_wikipedia(url_inicial):
    links_visitados = set()  # Conjunto para armazenar links já visitados
    paginas_coletadas = 0    # Contador de páginas coletadas
    proximo_link = url_inicial  # Começa pela página inicial

    while paginas_coletadas < MAX_PAGINAS:
        try:
            # 1. Obter a página
            response = requests.get(proximo_link)
            soup = BeautifulSoup(response.content, "html.parser")

            # 2. Salvar a página como um arquivo HTML
            titulo = soup.select(".mw-page-title-main")
            nome_arquivo = titulo[0].text
            salvar_pagina_html(proximo_link, nome_arquivo)

            # 3. Extrair todos os links da página
            links = extrair_links(soup)

            # 4. Adicionar links à lista de visitados
            links_visitados.add(proximo_link)

            # 5. Escolher o próximo link não visitado
            proximo_link = escolher_proximo_link(links, links_visitados)
            if not proximo_link:
                print("Todos os links foram visitados.")
                break

            # 6. Atualizar o próximo link para a URL completa
            proximo_link = "https://pt.wikipedia.org" + proximo_link

            # 7. Incrementar o contador de páginas coletadas
            paginas_coletadas += 1
            print(f"Páginas coletadas: {paginas_coletadas}")

            # 8. Esperar um pouco para não sobrecarregar o servidor
            time.sleep(1)

        except Exception as e:
            print(f"Erro ao processar a página: {proximo_link}")
            print(f"Detalhes do erro: {e}")
            break

    print(f"Coleta concluída. Total de páginas coletadas: {paginas_coletadas}")

# TAREFA 1: Iniciar o crawler com a URL inicial
crawler_wikipedia(URL_INICIAL)


# TAREFA 2: Extrair Infoboxes e exportar para JSON

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
        if info["tem_infobox"]:
            save_json(
                dados = info["conteudo_infobox"],
                output_dir = output_dir,
                nome_arquivo = info["titulo_infobox"]
            )
            count += 1
    
    print(f"Processamento concluído.\n {count} arquivo(s) com infoboxes.")
    
    return resultados


# TAREFA 2: Executar
process_infoboxes(HTML_DIR)