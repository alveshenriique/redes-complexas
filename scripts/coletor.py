import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from collections import Counter
from tqdm import tqdm

def coletar_dados_completos(video_id, api_keys):
    # Coleta de forma integrada a rede e o conteúdo textual dos comentários,
    # trocando de chave de API automaticamente quando a cota se esgota.
    
    if not api_keys:
        print("ERRO: Nenhuma chave de API foi encontrada.")
        return

    current_key_index = 0
    api_key = api_keys[current_key_index]
    youtube = build("youtube", "v3", developerKey=api_key)
    print(f"Conexão com a API estabelecida usando a Chave #{current_key_index + 1}.")

    nodes = {}
    edges = []
    all_comments = []

    # PARTE 1: COLETA DE COMENTÁRIOS E RESPOSTAS
    print("\nIniciando a coleta de dados completos...")
    
    # <-- MUDANÇA AQUI: Adicionado 'bar_format' para simplificar a saída.
    progress_bar = tqdm(desc="Comentários Principais Processados", unit=" cmt", bar_format="{desc}: {n_fmt} {unit}")
    
    next_page_token_threads = None
    
    while True:
        try:
            request_threads = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                textFormat="plainText",
                maxResults=100,
                pageToken=next_page_token_threads
            )
            response_threads = request_threads.execute()

            for item in response_threads["items"]:
                top_comment = item["snippet"]["topLevelComment"]
                author_parent = top_comment["snippet"]["authorDisplayName"]
                comment_id_parent = top_comment["id"]
                all_comments.append({'comment_id': comment_id_parent, 'author': author_parent, 'text': top_comment["snippet"]["textOriginal"], 'likes': top_comment["snippet"]["likeCount"], 'timestamp': top_comment["snippet"]["publishedAt"], 'parent_id': None})
                if author_parent not in nodes:
                    nodes[author_parent] = {'total_comments': 0, 'total_replies_received': 0}
                nodes[author_parent]['total_comments'] += 1
                if item["snippet"]["totalReplyCount"] > 0:
                    next_page_token_replies = None
                    while True:
                        try:
                            request_replies = youtube.comments().list(part="snippet", parentId=comment_id_parent, maxResults=100, pageToken=next_page_token_replies)
                            response_replies = request_replies.execute()
                            for reply_item in response_replies["items"]:
                                author_reply = reply_item["snippet"]["authorDisplayName"]
                                all_comments.append({'comment_id': reply_item["id"],'author': author_reply,'text': reply_item["snippet"]["textOriginal"],'likes': reply_item["snippet"]["likeCount"],'timestamp': reply_item["snippet"]["publishedAt"],'parent_id': comment_id_parent})
                                if author_reply not in nodes:
                                    nodes[author_reply] = {'total_comments': 0, 'total_replies_received': 0}
                                edges.append({'source': author_reply, 'target': author_parent})
                                nodes[author_parent]['total_replies_received'] += 1
                            next_page_token_replies = response_replies.get("nextPageToken")
                            if not next_page_token_replies:
                                break
                        except HttpError:
                            break
            
            progress_bar.update(len(response_threads["items"]))
            next_page_token_threads = response_threads.get("nextPageToken")
            if not next_page_token_threads:
                break
        
        except HttpError as e:
            if 'quotaExceeded' in str(e):
                current_key_index += 1
                if current_key_index < len(api_keys):
                    api_key = api_keys[current_key_index]
                    print(f"\nCOTA ESGOTADA. Trocando para a Chave de API #{current_key_index + 1}...")
                    youtube = build("youtube", "v3", developerKey=api_key)
                    continue
                else:
                    print("\nTODAS AS COTAS DE API FORAM ESGOTADAS PARA HOJE.")
                    break
            else:
                print(f"\nOcorreu um erro na chamada da API: {e}")
                raise e
    
    progress_bar.close()
    print("\nColeta finalizada ou interrompida por falta de cotas.")
    
    if edges:
        print("\nProcessando e salvando os arquivos da rede...")
        df_arestas = pd.DataFrame([{'source': k[0], 'target': k[1], 'peso': v} for k, v in Counter((e['source'], e['target']) for e in edges).items()])
        df_nos = pd.DataFrame.from_dict(nodes, orient='index', columns=['total_comments', 'total_replies_received'])
        df_nos.index.name = 'id'
        df_nos.reset_index(inplace=True)
        df_arestas.to_csv('data/raw/rede_usuarios_arestas.csv', index=False, encoding='utf-8-sig')
        df_nos.to_csv('data/raw/rede_usuarios_nos.csv', index=False, encoding='utf-8-sig')
        print("Arquivos de rede gerados com sucesso.")
    if all_comments:
        print("\nProcessando e salvando o arquivo de comentários com texto...")
        df_comments = pd.DataFrame(all_comments)
        df_comments.to_csv('data/raw/comentarios.csv', index=False, encoding='utf-8-sig')
        print("Arquivo de comentários gerado com sucesso.")

# PONTO DE ENTRADA DO SCRIPT
if __name__ == "__main__":
    load_dotenv()
    
    api_keys_list = []
    i = 1
    while True:
        key = os.getenv(f"YOUTUBE_API_KEY_{i}")
        if key:
            api_keys_list.append(key)
            i += 1
        else:
            break
            
    VIDEO_ID = "FpsCzFGL1LE" 
    
    if not api_keys_list:
        print("ERRO: Nenhuma chave de API foi encontrada no arquivo .env (ex: YOUTUBE_API_KEY_1, YOUTUBE_API_KEY_2)")
    else:
        coletar_dados_completos(video_id=VIDEO_ID, api_keys=api_keys_list)