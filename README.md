# Análise de Redes Sociais: O Debate sobre o Vídeo "Adultização Infantil" de Felca

Este repositório contém o desenvolvimento de um artigo científico para a disciplina de Redes Complexas (Mineração de Mídias Sociais). O projeto realiza uma análise estrutural sobre a rede de interações nos comentários do vídeo "A Adultização Infantil", publicado pelo YouTuber Felca.

O objetivo principal é mapear a topologia da discussão, identificar a formação de comunidades (clusters) e investigar o nível de polarização do debate, utilizando métricas e visualizações de redes complexas.

---

## 📂 Estrutura do Repositório

O projeto é organizado na seguinte estrutura de pastas para garantir a reprodutibilidade e a clareza da análise:

-   **/data**: Contém todos os dados utilizados no projeto.
    -   `data/raw/`: Armazena os dados brutos coletados diretamente da API do YouTube (ex: `rede_usuarios_arestas.csv`).
    -   `data/processed/`: Armazena os dados processados e preparados para visualização (ex: `grafo_completo_gephi.gexf`).
-   **/notebooks**: Contém os Jupyter Notebooks com o passo a passo da análise exploratória, cálculos e documentação do processo.
-   **/scripts**: Armazena os scripts em Python (`.py`) para tarefas específicas e reutilizáveis, como o coletor de dados da API.
-   **/figures**: Armazena as saídas visuais da análise, como os grafos gerados pelo Gephi (ex: `figura1_rede_completa.svg`).

---

## 🔬 Metodologia

A análise foi conduzida em múltiplas camadas para extrair insights tanto da estrutura geral da rede quanto de subgrupos específicos de interesse.

1.  **Coleta de Dados:** Utilização da API de Dados v3 do YouTube para extrair a rede de respostas aos comentários do vídeo, modelando usuários como nós e respostas como arestas.
2.  **Análise da Rede Completa:** Construção do grafo principal para mapear a estrutura geral da discussão. A detecção de comunidades foi realizada com o algoritmo Louvain e a polarização foi quantificada pela métrica de modularidade.
3.  **Análise do Núcleo Denso (K-Core):** Aplicação de um filtro k-core para isolar o subgrupo de usuários mais densamente e mutuamente conectados, investigando se a polarização se intensifica neste "núcleo duro" do debate.
4.  **Análise da Rede de Autoridades:** Criação de um subgrafo composto pelos usuários mais influentes (maior grau de entrada) para analisar a dinâmica de interação da "elite" da discussão.
5.  **Visualização:** Uso do software Gephi para a renderização e exploração visual dos grafos, permitindo uma análise qualitativa das estruturas encontradas.

---

## 🛠️ Ferramentas Utilizadas

-   **Linguagem:** Python 3.10+
-   **Bibliotecas Principais:**
    -   `pandas`: Manipulação e estruturação dos dados.
    -   `networkx`: Criação, manipulação e análise dos grafos.
    -   `google-api-python-client`: Interação com a API do YouTube.
    -   `python-dotenv`: Gerenciamento de chaves de API.
-   **Software de Visualização:** Gephi 0.10.1
-   **Ambiente de Análise:** Jupyter Notebook

---

## 🚀 Como Executar o Projeto

Para replicar esta análise, siga os passos abaixo:

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/analise-redes-sociais-felca.git](https://github.com/seu-usuario/analise-redes-sociais-felca.git)
    cd analise-redes-sociais-felca
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    # Criar o ambiente
    python3 -m venv venv
    # Ativar (Linux/macOS)
    source venv/bin/activate
    # Ativar (Windows PowerShell)
    .\venv\Scripts\Activate.ps1
    ```

3.  **Instale as dependências:**
    *Primeiro, crie um arquivo `requirements.txt` com as bibliotecas necessárias. Em seguida, instale-as.*
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure a Chave da API:**
    * Crie um arquivo chamado `.env` na raiz do projeto.
    * Dentro deste arquivo, adicione sua chave da API do YouTube no seguinte formato:
      `YOUTUBE_API_KEY="SUA_CHAVE_DE_API_VAI_AQUI"`

5.  **Execute a Análise:**
    * Abra o Jupyter Notebook localizado na pasta `/notebooks`.
    * Execute as células em ordem sequencial para reproduzir a análise.

---

## 📊 Resultados Preliminares

A análise inicial da rede completa revelou uma estrutura com alta modularidade (Q > 0.4), indicando uma forte divisão em comunidades com pouca interação entre si, o que caracteriza um debate polarizado. A investigação dos subgrafos (núcleo denso e autoridades) aprofunda essa observação, analisando como a polarização se manifesta em diferentes estratos de engajamento dos usuários. As visualizações finais podem ser encontradas na pasta `/figures`.
