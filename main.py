import requests
from bs4 import BeautifulSoup
import time

# Função para salvar a página como um arquivo HTML
def salvar_pagina_html(url, titulo):
    response = requests.get(url)
    with open(f'{titulo}.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print(f"Página salva com sucesso: {titulo}.html")

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

    while paginas_coletadas < 5:
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

# Iniciar o crawler
url_inicial = "https://pt.wikipedia.org/wiki/Grammy_Awards"
crawler_wikipedia(url_inicial)
