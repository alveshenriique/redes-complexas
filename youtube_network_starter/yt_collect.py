#!/usr/bin/env python3
"""
YouTube Data Collector & Network Builder (no relatedToVideoId)
- Seeds videos via search queries
- Collects video metadata
- (Optional) collects top-level comments (commentThreads.list)
- Builds two kinds of networks:
    1) User→Video (comment edges)
    2) Video↔Video similarity (TF-IDF of title+description)

Outputs:
  outdir/
    nodes_videos.csv
    nodes_users.csv                  (if comments collected)
    edges_comments_user_video.csv    (if comments collected)
    edges_similarity_video_video.csv (if built)
    graph_comment_bipartite.graphml  (if comments collected)
    graph_similarity.graphml         (if built)
    raw/ (json dumps per API page for reproducibility)

Usage examples:
  python yt_collect.py --query "inteligência artificial" --max-seeds 50 --depth 0 --outdir data/ai --build-similarity
  python yt_collect.py --query "luta greco romana" --max-seeds 30 --collect-comments --comments-per-video 200 --outdir data/luta

Notes:
- This script uses only API-key (no OAuth) and public endpoints.
- It does NOT rely on relatedToVideoId, which was deprecated on Aug 7, 2023.
"""

import os
import sys
import time
import json
import math
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set

from dotenv import load_dotenv
import pandas as pd
import networkx as nx
from tqdm import tqdm

# sklearn for similarity graph
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Google API client
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ------------------------ Helpers ------------------------

def chunked(iterable, size):
    buf = []
    for x in iterable:
        buf.append(x)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf

def safe_get(d: dict, path: List[str], default=None):
    cur = d
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur

def ensure_outdirs(outdir: Path):
    (outdir / "raw").mkdir(parents=True, exist_ok=True)

# ------------------------ YouTube API ------------------------

class YouTubeClient:
    def __init__(self, api_key: str, region_code: Optional[str]=None, relevance_language: Optional[str]=None):
        self.api_key = api_key
        self.service = build("youtube", "v3", developerKey=api_key)
        self.region_code = region_code
        self.relevance_language = relevance_language

    def _call(self, request, raw_path: Path, kind: str):
        """
        Execute a request with error handling and store the raw response page-by-page.
        """
        page_idx = 0
        while True:
            try:
                response = request.execute()
            except HttpError as e:
                code = getattr(e, 'status_code', None) or getattr(e, 'resp', {}).status if hasattr(e, 'resp') else None
                print(f"[WARN] HttpError on {kind} page {page_idx}: {e}", file=sys.stderr)
                # Simple backoff
                time.sleep(2.0)
                # Re-raise after a couple attempts is omitted; keep trying modestly
                # In academic runs, you may prefer to stop here:
                # raise
                try:
                    response = request.execute()
                except Exception:
                    raise

            # Save raw page
            raw_file = raw_path / f"{kind}_page{page_idx:04d}.json"
            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(response, f, ensure_ascii=False, indent=2)

            yield response

            page_token = response.get("nextPageToken")
            if not page_token:
                break
            request = request.list_next(request, response)
            page_idx += 1

    def search_videos(self, query: str, max_results: int = 50) -> List[str]:
        """
        Return up to max_results video IDs for a query via search.list (type=video).
        """
        ids: List[str] = []
        req = self.service.search().list(
            part="id",
            q=query,
            type="video",
            maxResults=50,
            regionCode=self.region_code,
            relevanceLanguage=self.relevance_language,
            safeSearch="none"
        )
        # raw path for search pages
        # (call sites pass raw_path; we adjust here by returning pages)
        raise NotImplementedError("Use search_videos_to_file for raw saving.")

    def search_videos_to_file(self, query: str, max_results: int, raw_path: Path) -> List[str]:
        ids: List[str] = []
        req = self.service.search().list(
            part="id",
            q=query,
            type="video",
            maxResults=50,
            regionCode=self.region_code,
            relevanceLanguage=self.relevance_language,
            safeSearch="none"
        )
        for page in self._call(req, raw_path, kind=f"search_{slugify(query)}"):
            for item in page.get("items", []):
                vid = safe_get(item, ["id", "videoId"])
                if vid:
                    ids.append(vid)
                if len(ids) >= max_results:
                    return ids
        return ids

    def videos_list(self, ids: List[str], raw_path: Path) -> List[Dict[str, Any]]:
        out = []
        for batch in chunked(list(dict.fromkeys(ids)), 50):
            req = self.service.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(batch),
                maxResults=50,
            )
            for page in self._call(req, raw_path, kind="videos_list"):
                out.extend(page.get("items", []))
        return out

    def get_top_level_comments(self, video_id: str, max_items: int, raw_path: Path) -> List[Dict[str, Any]]:
        """
        Uses commentThreads.list to fetch top-level comments (no replies here).
        """
        items = []
        req = self.service.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText",
            order="relevance"  # or 'time'
        )
        count = 0
        for page in self._call(req, raw_path, kind=f"comments_{video_id}"):
            for item in page.get("items", []):
                items.append(item)
                count += 1
                if count >= max_items:
                    return items
        return items

# ------------------------ Core pipeline ------------------------

def slugify(s: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in s).strip("_")

def collect_videos_by_query(yt: YouTubeClient, query: str, max_seeds: int, outdir: Path) -> List[str]:
    print(f"[INFO] Searching for up to {max_seeds} videos for query: {query!r}")
    ids = yt.search_videos_to_file(query, max_seeds, outdir / "raw")
    uniq = list(dict.fromkeys(ids))
    print(f"[INFO] Found {len(uniq)} unique seed video IDs")
    return uniq

def fetch_video_metadata(yt: YouTubeClient, video_ids: List[str], outdir: Path) -> pd.DataFrame:
    print(f"[INFO] Fetching metadata for {len(video_ids)} videos")
    items = yt.videos_list(video_ids, outdir / "raw")
    rows = []
    for it in items:
        vid = it.get("id")
        snip = it.get("snippet", {})
        stats = it.get("statistics", {})
        rows.append({
            "videoId": vid,
            "title": snip.get("title"),
            "description": snip.get("description"),
            "channelId": snip.get("channelId"),
            "channelTitle": snip.get("channelTitle"),
            "publishedAt": snip.get("publishedAt"),
            "viewCount": int(stats.get("viewCount", 0)) if stats.get("viewCount") else None,
            "likeCount": int(stats.get("likeCount", 0)) if stats.get("likeCount") else None,
            "commentCount": int(stats.get("commentCount", 0)) if stats.get("commentCount") else None,
            "duration": it.get("contentDetails", {}).get("duration"),
        })
    df = pd.DataFrame(rows).drop_duplicates(subset=["videoId"])
    df.to_csv(outdir / "nodes_videos.csv", index=False)
    return df

def collect_comments_bipartite(yt: YouTubeClient, video_ids: List[str], comments_per_video: int, outdir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns (users_df, edges_user_video_df)
    """
    all_edges = []
    users = {}
    for vid in tqdm(video_ids, desc="Comments"):
        try:
            items = yt.get_top_level_comments(vid, comments_per_video, outdir / "raw")
        except HttpError as e:
            print(f"[WARN] Skipping comments for {vid} due to HttpError: {e}", file=sys.stderr)
            continue
        for it in items:
            top = it.get("snippet", {}).get("topLevelComment", {})
            sn = top.get("snippet", {})
            author_channel_id = safe_get(sn, ["authorChannelId", "value"])
            author_display_name = sn.get("authorDisplayName")
            comment_id = top.get("id")
            like_count = sn.get("likeCount")
            published_at = sn.get("publishedAt")
            text = sn.get("textDisplay") or sn.get("textOriginal") or sn.get("text")

            if author_channel_id:
                users.setdefault(author_channel_id, {"userId": author_channel_id, "displayName": author_display_name})
                all_edges.append({
                    "sourceUserId": author_channel_id,
                    "targetVideoId": vid,
                    "edge": "commented",
                    "commentId": comment_id,
                    "likeCount": like_count,
                    "publishedAt": published_at,
                    "text": text.replace("\n", " ") if isinstance(text, str) else text
                })

    users_df = pd.DataFrame(list(users.values()))
    edges_df = pd.DataFrame(all_edges)
    if not users_df.empty:
        users_df.to_csv(outdir / "nodes_users.csv", index=False)
    if not edges_df.empty:
        edges_df.to_csv(outdir / "edges_comments_user_video.csv", index=False)

    # Build bipartite graph and save GraphML
    if not users_df.empty and not edges_df.empty:
        B = nx.Graph()
        # add users with bipartite=0, videos with bipartite=1
        B.add_nodes_from(users_df["userId"].tolist(), bipartite=0, kind="user")
        # For video nodes we need their ids; from edges
        video_ids_in_edges = edges_df["targetVideoId"].unique().tolist()
        B.add_nodes_from(video_ids_in_edges, bipartite=1, kind="video")
        # add edges
        for _, row in edges_df.iterrows():
            B.add_edge(row["sourceUserId"], row["targetVideoId"], edge=row["edge"], commentId=row["commentId"])
        nx.write_graphml(B, outdir / "graph_comment_bipartite.graphml")
    return users_df, edges_df

def build_similarity_graph(videos_df: pd.DataFrame, outdir: Path, top_k: int = 5, min_sim: float = 0.25) -> pd.DataFrame:
    """
    Build a similarity graph using TF-IDF of title + description.
    Each video connects to up to top_k most similar others above min_sim.
    """
    if videos_df.empty:
        return pd.DataFrame()

    texts = ((videos_df["title"].fillna("") + " " + videos_df["description"].fillna("")).astype(str)).tolist()
    vectorizer = TfidfVectorizer(max_features=20000, ngram_range=(1,2), min_df=2)
    X = vectorizer.fit_transform(texts)
    # Compute cosine similarity in chunks to control memory
    ids = videos_df["videoId"].tolist()
    edges = []
    # Chunked approach for large sets
    # For typical class projects (<5k videos), full matrix is feasible; here we do chunked to be safe
    step = 1000 if X.shape[0] > 3000 else X.shape[0]
    for start in range(0, X.shape[0], step):
        end = min(start + step, X.shape[0])
        sim_block = cosine_similarity(X[start:end], X)  # (end-start) x N
        for i, row in enumerate(sim_block):
            src_idx = start + i
            # sort by similarity, skip self
            ranked = sorted(((j, s) for j, s in enumerate(row) if j != src_idx), key=lambda t: t[1], reverse=True)
            kept = 0
            for j, s in ranked:
                if s < min_sim:
                    break  # since sorted desc, we can break once below threshold
                edges.append({"source": ids[src_idx], "target": ids[j], "weight": float(s), "edge": "similar"})
                kept += 1
                if kept >= top_k:
                    break

    edges_df = pd.DataFrame(edges).drop_duplicates(subset=["source", "target"])
    if not edges_df.empty:
        edges_df.to_csv(outdir / "edges_similarity_video_video.csv", index=False)
        # Save as weighted graph
        G = nx.Graph()
        for _, row in videos_df.iterrows():
            G.add_node(row["videoId"], **row.to_dict())
        for _, row in edges_df.iterrows():
            G.add_edge(row["source"], row["target"], weight=row["weight"], edge=row["edge"])
        nx.write_graphml(G, outdir / "graph_similarity.graphml")
    return edges_df

# ------------------------ CLI ------------------------

def main():
    parser = argparse.ArgumentParser(description="Collect YouTube data for complex networks (without deprecated relatedToVideoId).")
    parser.add_argument("--query", type=str, required=True, help="Search query to seed videos (Portuguese or any language).")
    parser.add_argument("--max-seeds", type=int, default=50, help="How many seed videos to collect from search.")
    parser.add_argument("--collect-comments", action="store_true", help="Collect top-level comments and build a user→video bipartite network.")
    parser.add_argument("--comments-per-video", type=int, default=200, help="Max top-level comments per video.")
    parser.add_argument("--build-similarity", action="store_true", help="Build a similarity network between videos using TF-IDF (title+description).")
    parser.add_argument("--top-k", type=int, default=5, help="Top-k most similar neighbors per video (for similarity graph).")
    parser.add_argument("--min-sim", type=float, default=0.25, help="Minimum cosine similarity to create an edge (0-1).")
    parser.add_argument("--outdir", type=str, required=True, help="Output directory.")
    parser.add_argument("--api-key", type=str, default=None, help="YouTube API key (fallback if .env not used).")
    parser.add_argument("--region-code", type=str, default=None, help="Bias search results to a specific country (e.g., BR). Overrides .env.")
    parser.add_argument("--relevance-language", type=str, default=None, help="Bias search results to a language (e.g., pt). Overrides .env.")

    args = parser.parse_args()

    outdir = Path(args.outdir)
    ensure_outdirs(outdir)

    # Load env
    load_dotenv()
    api_key = args.api_key or os.getenv("YT_API_KEY")
    if not api_key:
        print("ERROR: Missing API key. Pass --api-key or set YT_API_KEY in environment/.env", file=sys.stderr)
        sys.exit(1)

    region_code = args.region_code or os.getenv("REGION_CODE") or None
    relevance_language = args.relevance_language or os.getenv("RELEVANCE_LANGUAGE") or None

    yt = YouTubeClient(api_key, region_code=region_code, relevance_language=relevance_language)

    # 1) Seed videos
    seeds = collect_videos_by_query(yt, args.query, args.max_seeds, outdir)

    # 2) Video metadata
    videos_df = fetch_video_metadata(yt, seeds, outdir)

    # 3) Optional: comments bipartite
    if args.collect-comments if False else args.collect_comments:  # avoid hyphen var name
        users_df, edges_comments_df = collect_comments_bipartite(
            yt, videos_df["videoId"].tolist(), args.comments_per_video, outdir
        )
        print(f"[INFO] Users collected: {0 if users_df is None else len(users_df)}")
        print(f"[INFO] Comment edges: {0 if edges_comments_df is None else len(edges_comments_df)}")

    # 4) Optional: similarity network
    if args.build_similarity:
        edges_sim_df = build_similarity_graph(videos_df, outdir, top_k=args.top_k, min_sim=args.min_sim)
        print(f"[INFO] Similarity edges: {0 if edges_sim_df is None else len(edges_sim_df)}")

    print(f"[DONE] Outputs saved under: {outdir.resolve()}")

if __name__ == "__main__":
    main()
