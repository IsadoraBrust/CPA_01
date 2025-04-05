## CPA - Exercício 1 - Coleta de Dados na Wikipedia

### Instruções

Para a execução da **Tarefa 1 - Webscraping**: 
- É necessário que o ambiente contenha a biblioteca Beautiful Soup.

O arquivo `main.py` realiza as chamadas para a execução das Tarefas 1 e 2, dentro do `main()`.

Após a execução do programa, os arquivos de saída ficam disponíveis nos diretórios:
- Tarefa 1:  `/saida_html` 
- Tarefa 2: `/saida_json`

Também é possível acompanhar o log do funcionamento do programa, disponível em:
- `/logs/main.log`

Durante a execução do crawler na Tarefa 1, usamos a biblioteca Pickle para salvar o progresso a cada 50 páginas coletadas com sucesso. Esses dados são armazenados na raíz do projeto em um arquivo `progresso.pkl`. Então, se existir este arquivo na raíz, o crawler extrai seus dados e continua daquele ponto que foi salvo previamente. Para começar um scraping do zero, devemos excluir o arquivo `progresso.pkl`, se ele existir.


