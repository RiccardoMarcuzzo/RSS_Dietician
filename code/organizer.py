import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

import numpy as np
import onnxruntime as ort
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from sklearn.cluster import HDBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer

from feed_reader import Article

logger = logging.getLogger(__name__)

tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-mpnet-base-v2')
session = ort.InferenceSession('model/model.onnx', providers=['CPUExecutionProvider'])

@dataclass
class Cluster:
    id: int
    articles: List[Article] = field(default_factory=list)

def _embed_titles_onnx(
    articles: List[Article], 
    tokenizer: AutoTokenizer, session:ort.InferenceSession, 
    batch_size: int = 32
) -> np.NDArray:
    titles = [a.title for a in articles]
    all_embeddings = []
    
    for i in range(0, len(titles), batch_size):
        batch = titles[i:i + batch_size]
        encoded = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors='np'
        )
     
        embeddings = session.run(
            ['sentence_embedding'],
            {'input_ids': encoded['input_ids'], 
             'attention_mask': encoded['attention_mask']}
        )[0]
        all_embeddings.append(embeddings)
    
    return np.vstack(all_embeddings)

def _cluster_articles(articles: List[Article]) -> List[Article]:
    if len(articles) <= 1:
        for i, a in enumerate(articles):
            a.cluster_id = i
        return articles

    try:
        embeddings = _embed_titles_onnx(articles, tokenizer, session)
        emb_sim = cosine_similarity(embeddings)

        dist_matrix = np.clip(1.0 - emb_sim, 0.0, 1.0)
        np.fill_diagonal(dist_matrix, 0.0)
        
        clustering = HDBSCAN(
            min_cluster_size=2,
            min_samples=1,
            metric='precomputed',
            cluster_selection_method='eom',
            n_jobs=-1,
            copy=True
        )
        labels = clustering.fit_predict(dist_matrix)

        # re-assign articles without a cluster
        outlier_indices = np.where(labels == -1)[0]
        for i in outlier_indices:
            distances_to_others = dist_matrix[i]
            clustered = np.where(labels != -1)[0]
            if len(clustered) == 0:
                continue    
            nearest = clustered[np.argmin(distances_to_others[clustered])]
            if dist_matrix[i][nearest] < 0.4:
                labels[i] = labels[nearest]

        next_id = labels.max() + 1
        for i in np.where(labels == -1)[0]:
            labels[i] = next_id
            next_id += 1
         
        for art, label in zip(articles, labels):
            art.cluster_id = int(label)

    except Exception as exc:
        logger.warning(f'Clustering fallback (errore: {exc}) – ogni articolo = cluster proprio')
        for i, a in enumerate(articles):
            a.cluster_id = i

    return articles

def organize(articles: List[Article]) -> List[Cluster]:
    logger.info(f'Clustering {len(articles)} articles')
    with Progress(
        SpinnerColumn(),
        TextColumn('[bold cyan]{task.description}'),
        BarColumn(),
        TaskProgressColumn(),
        transient=True,
    ) as progress:

        task = progress.add_task('Clustering articles...', total=3)

        clustered = _cluster_articles(articles)
        progress.advance(task)
        progress.update(task, description='Grouping cluster...')

        cluster_map: Dict[int, List[Article]] = defaultdict(list)
        for a in clustered:
            cluster_map[a.cluster_id].append(a)
        progress.advance(task)
        progress.update(task, description='Assigning articles...')

        clusters = []
        for cid, arts in cluster_map.items():
            c = Cluster(
            id=cid,
            articles=sorted(
                arts,
                key=lambda a: a.pub_date or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
                ),
            )
            clusters.append(c)
        progress.advance(task)

    return clusters
