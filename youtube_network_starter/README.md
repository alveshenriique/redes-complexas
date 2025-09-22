# YouTube Network Starter (Sem `relatedToVideoId`)

Este kit coleta dados públicos do YouTube usando **YouTube Data API v3** (apenas **API key**) e constrói dois tipos de redes para análise em **redes complexas**:

1. **Bipartida Usuário→Vídeo** (a partir de **comentários**).
2. **Vídeo↔Vídeo por similaridade** (TF‑IDF de título+descrição).

> Observação: o parâmetro `relatedToVideoId` do endpoint `search.list` foi **descontinuado pelo YouTube em 07/08/2023**. Por isso, este projeto **não** usa a antiga rede de “vídeos relacionados”.

---

## ✅ O que você precisa

- Python 3.10+
- Uma **API key** do YouTube Data API v3
- (opcional) `venv` para isolar dependências

### Como obter a API key (resumo)
1. Crie um projeto no **Google Cloud Console**.
2. Habilite a **YouTube Data API v3** no projeto.
3. Em *APIs & Services → Credentials*, crie uma **API Key**.
4. Copie a chave e coloque no arquivo `.env` como `YT_API_KEY=...`

> Dica: consulte a documentação oficial para etapas atualizadas.

---

## 🚀 Instalação

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edite o arquivo .env e preencha YT_API_KEY
```

---

## 🧭 Uso básico

### 1) Coletar vídeos por busca (sementes) + metadados
```bash
python yt_collect.py \  --query "inteligência artificial" \  --max-seeds 50 \  --outdir data/ai
```

Saídas:
- `nodes_videos.csv` — nós (vídeos) com metadados.
- `raw/` — respostas cruas por página da API (para reprodutibilidade).

### 2) Adicionar rede **Usuário→Vídeo** via comentários
```bash
python yt_collect.py \  --query "inteligência artificial" \  --max-seeds 30 \  --collect-comments \  --comments-per-video 200 \  --outdir data/ai_comments
```
Saídas extras:
- `nodes_users.csv`
- `edges_comments_user_video.csv`
- `graph_comment_bipartite.graphml`

> Observação: o endpoint usado é `commentThreads.list` (apenas comentários de nível superior).

### 3) Adicionar rede **Vídeo↔Vídeo** por similaridade
```bash
python yt_collect.py \  --query "inteligência artificial" \  --max-seeds 80 \  --build-similarity \  --top-k 5 \  --min-sim 0.25 \  --outdir data/ai_sim
```
Saídas extras:
- `edges_similarity_video_video.csv`
- `graph_similarity.graphml`

---

## 📦 Estrutura de saída

```
outdir/
  nodes_videos.csv
  nodes_users.csv                  (se coletar comentários)
  edges_comments_user_video.csv    (se coletar comentários)
  edges_similarity_video_video.csv (se construir similaridade)
  graph_comment_bipartite.graphml  (se coletar comentários)
  graph_similarity.graphml         (se construir similaridade)
  raw/
    *.json                         (páginas completas da API)
```

---

## 🧪 Dicas de análise (NetworkX / Gephi)

- **Grau, betweenness, closeness** para destacar vídeos/usuários centrais.
- **Projeção** da rede bipartida para **Usuário↔Usuário** (co-comentário no mesmo vídeo).
- **Comunidades** (Louvain/Leiden) no grafo de similaridade.
- **Visualização** no **Gephi** importando `.graphml`.

---

## ⚠️ Boas práticas e limites

- Respeite políticas e limites de uso da API.
- Armazene apenas dados **públicos** e evite publicar informações sensíveis de usuários.
- Documente suas consultas (query, data, parâmetros) no relatório para **reprodutibilidade**.

---

## 📚 Referências úteis
- API Reference (YouTube Data API v3)
- `videos.list` (metadados de vídeos)
- `commentThreads.list` (comentários de nível superior)
- Histórico de Revisões (descontinuações e mudanças)

---

Bom trabalho! ✨
