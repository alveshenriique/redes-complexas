import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from collections import Counter
# A importação da "tqdm" foi removida.

def coletar_dados_completos(video_id, api_key):
    # Coleta de forma integrada a rede de interações e o conteúdo textual dos comentários,
    # gerando três arquivos CSV como saída.
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        print("Conexão com a API do YouTube estabelecida.")

        nodes = {}
        edges = []
        all_comments = []

        # PARTE 1: COLETA DE COMENTÁRIOS E RESPOSTAS
        print("\nIniciando a coleta de dados")
        
        next_page_token_threads = None
        
        # O laço externo pagina através dos comentários principais.
        while True:
            request_threads = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                textFormat="plainText",
                maxResults=100,
                pageToken=next_page_token_threads
            )
            response_threads = request_threads.execute()

            # O wrapper tqdm(...) foi removido do laço for abaixo.
            # Itera sobre cada comentário principal da página.
            for item in response_threads["items"]:
                top_comment = item["snippet"]["topLevelComment"]
                
                author_parent = top_comment["snippet"]["authorDisplayName"]
                comment_id_parent = top_comment["id"]
                
                all_comments.append({
                    'comment_id': comment_id_parent,
                    'author': author_parent,
                    'text': top_comment["snippet"]["textOriginal"],
                    'likes': top_comment["snippet"]["likeCount"],
                    'timestamp': top_comment["snippet"]["publishedAt"],
                    'parent_id': None 
                })
                
                if author_parent not in nodes:
                    nodes[author_parent] = {'total_comments': 0, 'total_replies_received': 0}
                nodes[author_parent]['total_comments'] += 1

                if item["snippet"]["totalReplyCount"] > 0:
                    next_page_token_replies = None
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
                                
                                all_comments.append({
                                    'comment_id': reply_item["id"],
                                    'author': author_reply,
                                    'text': reply_item["snippet"]["textOriginal"],
                                    'likes': reply_item["snippet"]["likeCount"],
                                    'timestamp': reply_item["snippet"]["publishedAt"],
                                    'parent_id': comment_id_parent
                                })
                                
                                if author_reply not in nodes:
                                    nodes[author_reply] = {'total_comments': 0, 'total_replies_received': 0}
                                
                                edges.append({'source': author_reply, 'target': author_parent})
                                nodes[author_parent]['total_replies_received'] += 1

                            next_page_token_replies = response_replies.get("nextPageToken")
                            if not next_page_token_replies:
                                break
                        except HttpError:
                            break
            
            next_page_token_threads = response_threads.get("nextPageToken")
            if not next_page_token_threads:
                break
        
        print("\nColeta finalizada!")

        # PARTE 2: PROCESSAMENTO E SALVAMENTO DOS ARQUIVOS DA REDE
        if edges:
            edge_counts = Counter((e['source'], e['target']) for e in edges)
            df_arestas = pd.DataFrame([{'source': k[0], 'target': k[1], 'peso': v} for k, v in edge_counts.items()])
            df_nos = pd.DataFrame.from_dict(nodes, orient='index', columns=['total_comments', 'total_replies_received'])
            df_nos.index.name = 'id'
            df_nos.reset_index(inplace=True)
            
            df_arestas.to_csv('data/raw/rede_usuarios_arestas.csv', index=False, encoding='utf-8-sig')
            df_nos.to_csv('data/raw/rede_usuarios_nos.csv', index=False, encoding='utf-8-sig')
            print("Arquivos de rede gerados com sucesso.")
        
        # PARTE 3: PROCESSAMENTO E SALVAMENTO DO ARQUIVO DE COMENTÁRIOS
        if all_comments:
            df_comments = pd.DataFrame(all_comments)
            df_comments.to_csv('data/raw/comentarios.csv', index=False, encoding='utf-8-sig')
            print("Arquivo de comentários gerado com sucesso.")

    except HttpError as e:
        print(f"\nOcorreu um erro na chamada da API: {e}")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")

# PONTO DE ENTRADA DO SCRIPT
if __name__ == "__main__":
    load_dotenv()
    API_KEY = os.getenv("YOUTUBE_API_KEY")
    VIDEO_ID = "FpsCzFGL1LE" 
    
    if not API_KEY or API_KEY == "SUA_CHAVE_DE_API_VAI_AQUI":
        print("ERRO: A chave da API não foi configurada no arquivo .env")
    else:
        coletar_dados_completos(video_id=VIDEO_ID, api_key=API_KEY)