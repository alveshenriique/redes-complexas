# Análise de Redes e Conteúdo: O Debate sobre o Vídeo "Adultização Infantil"

Este repositório contém o desenvolvimento de um artigo científico para a disciplina de Redes Complexas (Mineração de Mídias Sociais). O projeto realiza uma análise multifacetada sobre a discussão gerada nos comentários do vídeo "A Adultização Infantil", publicado pelo YouTuber Felca.

O objetivo é combinar duas abordagens complementares:
1.  **Análise de Rede:** Mapear a estrutura das interações para identificar a formação de comunidades e o nível de polarização estrutural.
2.  **Análise de Conteúdo:** Utilizar Processamento de Linguagem Natural (PLN) para analisar o conteúdo textual, o sentimento e os temas do discurso.

---

## Estrutura do Repositório

O projeto é organizado na seguinte estrutura de pastas para garantir a reprodutibilidade e a clareza da análise:

-   **/data**: Contém todos os dados utilizados no projeto.
    -   `data/raw/`: Armazena os dados brutos coletados da API do YouTube (ex: `comentarios.csv`).
    -   `data/processed/`: Armazena dados processados e enriquecidos (ex: `comentarios_com_sentimento.csv`, `grafo_completo_gephi.gexf`).
-   **/notebooks**: Contém os Jupyter Notebooks com o passo a passo da análise e documentação do processo.
-   **/scripts**: Armazena os scripts em Python (`.py`), como o coletor de dados da API.
-   **/figures**: Armazena as saídas visuais da análise, como os grafos gerados pelo Gephi e os gráficos do Matplotlib/Seaborn.

---

## Metodologia

A análise foi conduzida em duas frentes principais:

### Análise de Rede (Análise Estrutural)
1.  **Coleta de Dados:** Extração da rede de respostas aos comentários via API do YouTube v3.
2.  **Análise da Rede Completa:** Construção do grafo principal para mapear a estrutura geral do debate e quantificar a polarização pela métrica de modularidade (algoritmo Louvain).
3.  **Análise do Núcleo Denso (K-Core):** Aplicação de um filtro k-core para isolar o subgrupo de usuários mais engajados e investigar se a polarização se intensifica neste núcleo.
4.  **Visualização:** Uso do software Gephi para a renderização e exploração visual dos grafos.

### Análise de Conteúdo (Processamento de Linguagem Natural)
1.  **Pré-processamento:** Limpeza e normalização do texto dos comentários (remoção de stopwords, pontuação, etc.).
2.  **Análise Descritiva:** Geração de métricas sobre a dinâmica da discussão, incluindo volume de comentários ao longo do tempo, distribuição de engajamento (likes) e frequência de palavras.
3.  **Análise de Sentimento:** Aplicação de um modelo Transformer pré-treinado (`XLM-RoBERTa`) para classificar cada comentário como positivo, negativo ou neutro.
4.  **Análise Cruzada:** Investigação da relação entre a estrutura da rede e o sentimento, analisando a distribuição de sentimentos dentro de cada comunidade do grafo.

---

## Ferramentas Utilizadas

-   **Linguagem:** Python 3.10+
-   **Bibliotecas Principais:**
    -   `pandas`: Manipulação de dados.
    -   `networkx`: Análise de grafos.
    -   `matplotlib` & `seaborn`: Visualização de dados.
    -   `nltk`, `wordcloud`: Pré-processamento e visualização de texto.
    -   `transformers` & `torch`: Análise de sentimento com modelos de deep learning.
    -   `google-api-python-client`: Interação com a API do YouTube.
    -   `python-dotenv`: Gerenciamento de chaves de API.
-   **Software de Visualização:** Gephi 0.10.1
-   **Ambiente de Análise:** Jupyter Notebook

---

## Como Executar o Projeto

Para replicar esta análise, siga os passos abaixo:

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/alveshenriique/redes-complexas.git](https://github.com/alveshenriique/redes-complexas.git)
    cd redes-complexas
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    Crie um arquivo `requirements.txt` com as bibliotecas listadas na seção "Ferramentas" e instale-o.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as Chaves da API:**
    -   Crie um arquivo chamado `.env` na raiz do projeto.
    -   Dentro deste arquivo, adicione suas chaves da API do YouTube no seguinte formato, em ordem numérica:
        ```env
        YOUTUBE_API_KEY_1="SUA_CHAVE_DE_API_1"
        YOUTUBE_API_KEY_2="SUA_CHAVE_DE_API_2"
        ```

5.  **Execute a Coleta e a Análise:**
    -   Primeiro, execute o script de coleta para obter os dados mais recentes: `python3 scripts/coletor.py`.
    -   Abra os Jupyter Notebooks na pasta `/notebooks` (começando pelo `01_...` e depois o `02_...`).
    -   Execute as células em ordem sequencial para reproduzir a análise.

---

## Principais Achados

A análise combinada revela uma discussão altamente polarizada. A estrutura da rede de interações mostra uma clara separação em comunidades, com poucas pontes entre elas. Essa divisão estrutural é corroborada pela análise de sentimento, que indica um discurso predominantemente negativo. A análise cruzada demonstra que a polarização da rede corresponde a uma polarização de sentimento, com comunidades específicas exibindo perfis afetivos marcadamente distintos, validando a hipótese de que a discussão ocorreu em "bolhas" tanto de interação quanto de opinião.
