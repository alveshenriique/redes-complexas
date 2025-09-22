import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm
from collections import Counter

def coletar_rede_de_interacoes(video_id, api_key):
    """
    Coleta de forma integrada os comentários e suas respostas de um vídeo,
    gerando diretamente os arquivos de nós e arestas para análise de redes.
    """
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        print("Conexão com a API do YouTube estabelecida.")

        nodes = {}  # Dicionário para armazenar nós (usuários) e evitar duplicatas
        edges = []  # Lista para armazenar as arestas (interações)

        # --- PARTE 1: Coleta de Comentários Principais e suas Respostas ---
        print("\nIniciando a coleta integrada de comentários e respostas...")
        
        next_page_token_threads = None
        
        # O laço externo pagina através dos comentários principais
        while True:
            request_threads = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                textFormat="plainText",
                maxResults=100,
                pageToken=next_page_token_threads
            )
            response_threads = request_threads.execute()

            # Itera sobre cada comentário principal da página
            for item in tqdm(response_threads["items"], desc="Processando comentários da página"):
                top_comment = item["snippet"]["topLevelComment"]
                author_parent = top_comment["snippet"]["authorDisplayName"]
                comment_id_parent = top_comment["id"]
                
                # Adiciona o autor do comentário principal à lista de nós
                if author_parent not in nodes:
                    nodes[author_parent] = {'total_comments': 0, 'total_replies_received': 0}
                nodes[author_parent]['total_comments'] += 1

                # Verifica se há respostas para coletar
                if item["snippet"]["totalReplyCount"] > 0:
                    next_page_token_replies = None
                    # O laço interno pagina através das respostas de UM comentário principal
                    while True:
                        try:
                            request_replies = youtube.comments().list(
                                part="snippet",
                                parentId=comment_id_parent,
                                maxResults=100,
                                pageToken=next_page_token_replies
                            )
                            response_replies = request_replies.execute()

                            for reply_item in response_replies["items"]:
                                author_reply = reply_item["snippet"]["authorDisplayName"]
                                
                                # Adiciona o autor da resposta à lista de nós
                                if author_reply not in nodes:
                                    nodes[author_reply] = {'total_comments': 0, 'total_replies_received': 0}
                                
                                # Adiciona a aresta
                                edges.append({'source': author_reply, 'target': author_parent})
                                nodes[author_parent]['total_replies_received'] += 1

                            next_page_token_replies = response_replies.get("nextPageToken")
                            if not next_page_token_replies:
                                break
                        except HttpError:
                            # Ignora erros em respostas de comentários individuais
                            break
            
            next_page_token_threads = response_threads.get("nextPageToken")
            if not next_page_token_threads:
                break
        
        print("\nColeta finalizada!")

        # --- PARTE 2: Processamento e Salvamento dos Arquivos da Rede ---
        if not edges:
            print("Nenhuma interação de resposta foi encontrada. Nenhum arquivo de rede foi gerado.")
            return

        print("Processando e salvando os arquivos da rede...")

        # Criando o DataFrame de arestas com pesos
        edge_counts = Counter((e['source'], e['target']) for e in edges)
        df_arestas = pd.DataFrame([{'source': k[0], 'target': k[1], 'peso': v} for k, v in edge_counts.items()])
        
        # Criando o DataFrame de nós
        df_nos = pd.DataFrame.from_dict(nodes, orient='index')
        df_nos.index.name = 'id' # O nome do autor será o ID do nó
        df_nos.reset_index(inplace=True)

        # Salvando os arquivos
        df_arestas.to_csv('rede_usuarios_arestas.csv', index=False, encoding='utf-8-sig')
        df_nos.to_csv('rede_usuarios_nos.csv', index=False, encoding='utf-8-sig')

        print("\nArquivos de rede gerados com sucesso:")
        print(f"- rede_usuarios_nos.csv ({len(df_nos)} usuários)")
        print(f"- rede_usuarios_arestas.csv ({len(df_arestas)} interações únicas)")

    except HttpError as e:
        print(f"\nOcorreu um erro na chamada da API: {e}")
        if "quotaExceeded" in str(e):
            print("ERRO: Sua cota diária da API do YouTube foi excedida.")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")

# --- PONTO DE ENTRADA DO SCRIPT ---
if __name__ == "__main__":
    load_dotenv()
    API_KEY = os.getenv("YOUTUBE_API_KEY")
    VIDEO_ID = "FpsCzFGL1LE"
    
    if not API_KEY or API_KEY == "SUA_CHAVE_DE_API_VAI_AQUI":
        print("ERRO: A chave da API não foi configurada no arquivo .env")
    else:
        coletar_rede_de_interacoes(video_id=VIDEO_ID, api_key=API_KEY)