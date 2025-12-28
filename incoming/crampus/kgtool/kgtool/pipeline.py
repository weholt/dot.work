import json
import os
import pathlib
import re

import networkx as nx
import yake
from networkx.readwrite import json_graph
from rapidfuzz import fuzz
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ----------------------------------------------------------
# Chunking
# ----------------------------------------------------------


def extract_chunks(text: str) -> list[tuple[str, str]]:
    """
    Split markdown text by headings (##) into (title, content) pairs.
    Returns a list of (section_title, section_body).
    """
    # Pattern: heading line starting with one or more #
    pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))

    if not matches:
        raise ValueError("No headings found in document. Cannot chunk.")

    chunks = []
    for i, match in enumerate(matches):
        title = match.group(2).strip()
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start_pos:end_pos].strip()
        chunks.append((title, body))

    return chunks


# ----------------------------------------------------------
# Keyword extraction from TF-IDF
# ----------------------------------------------------------


def tfidf_keywords_for_row(row, feature_names: list[str], top_n: int) -> list[str]:
    if row.nnz == 0:
        return []
    scores = row.toarray().flatten()
    top_indices = scores.argsort()[-top_n:][::-1]
    return [feature_names[i] for i in top_indices]


# ----------------------------------------------------------
# Topic classification
# ----------------------------------------------------------


def load_topic_terms(path: str | None) -> dict[str, list[str]] | None:
    if not path:
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_topic_vectors(
    topic_terms: dict[str, list[str]],
    vectorizer: TfidfVectorizer,
):
    """
    Build TF-IDF vectors for each topic based on its terms.
    Returns dict: topic_name -> vector
    """
    topic_vecs = {}
    for topic_name, terms in topic_terms.items():
        # Create a pseudo-document from the topic terms
        pseudo_doc = " ".join(terms)
        vec = vectorizer.transform([pseudo_doc])
        topic_vecs[topic_name] = vec
    return topic_vecs


def classify_node_topics(
    node_vector,
    topic_terms: dict[str, list[str]],
    topic_vecs,
    vectorizer: TfidfVectorizer,
) -> list[str]:
    """
    Classify node into topics based on cosine similarity with topic vectors.
    Returns list of topic names with similarity > threshold.
    """
    threshold = 0.15
    assigned = []

    for topic_name, topic_vec in topic_vecs.items():
        sim = cosine_similarity(node_vector, topic_vec)[0][0]
        if sim > threshold:
            assigned.append(topic_name)

    # Fallback: fuzzy match node keywords against topic terms
    if not assigned:
        node_vec_array = node_vector.toarray().flatten()
        node_top_indices = node_vec_array.argsort()[-10:][::-1]
        node_top_terms = [vectorizer.get_feature_names_out()[i] for i in node_top_indices]

        best_topic = None
        best_score = 0
        for topic_name, terms in topic_terms.items():
            score = sum(max(fuzz.ratio(nt, tt) for tt in terms) for nt in node_top_terms)
            if score > best_score:
                best_score = score
                best_topic = topic_name

        if best_topic and best_score > 200:
            assigned.append(best_topic)

    return assigned


# ----------------------------------------------------------
# Topic discovery
# ----------------------------------------------------------


def discover_topics(
    input_file: str,
    output_file: str,
    num_topics: int = 5,
    terms_per_topic: int = 10,
) -> None:
    """
    Discover topics from document using KMeans clustering on TF-IDF vectors.
    Writes topic_terms.json with topic_0, topic_1, etc.
    """
    text = pathlib.Path(input_file).read_text(encoding="utf-8")
    chunks = extract_chunks(text)

    docs = [body for _, body in chunks]
    vectorizer = TfidfVectorizer(max_features=200, stop_words="english", ngram_range=(1, 2))
    X = vectorizer.fit_transform(docs)

    if len(docs) < num_topics:
        raise ValueError(
            f"Requested num_topics={num_topics} but only {len(docs)} chunks were found. "
            "Reduce num_topics or add more sections."
        )

    kmeans = KMeans(n_clusters=num_topics, random_state=42, n_init=10)
    kmeans.fit(X)

    feature_names = vectorizer.get_feature_names_out()
    topic_terms = {}

    for i in range(num_topics):
        center = kmeans.cluster_centers_[i]
        top_indices = center.argsort()[-terms_per_topic:][::-1]
        terms = [feature_names[idx] for idx in top_indices]
        topic_terms[f"topic_{i}"] = terms

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(topic_terms, f, indent=2, ensure_ascii=False)

    print(f"Topic discovery complete: {output_file}")
    print("Edit the topic names manually (e.g., topic_0 -> 'frontend').")
    print("Then pass this file to 'kgtool build --topics topic_terms.json'.")


# ----------------------------------------------------------
# Graph building
# ----------------------------------------------------------


def build_graph(
    input_file: str,
    output_dir: str,
    min_similarity: float = 0.3,
    top_keywords: int = 5,
    top_keyphrases: int = 5,
    topic_terms_path: str | None = None,
) -> None:
    """
    Build knowledge graph from document.
    Each heading becomes a node.
    Edges connect nodes with similarity > min_similarity.
    Nodes are tagged with topics if topic_terms_path is provided.
    """
    text = pathlib.Path(input_file).read_text(encoding="utf-8")
    chunks = extract_chunks(text)

    os.makedirs(output_dir, exist_ok=True)
    nodes_dir = os.path.join(output_dir, "nodes")
    os.makedirs(nodes_dir, exist_ok=True)

    # TF-IDF vectorization
    docs = [body for _, body in chunks]
    vectorizer = TfidfVectorizer(max_features=500, stop_words="english", ngram_range=(1, 2))
    X = vectorizer.fit_transform(docs)
    feature_names = vectorizer.get_feature_names_out()

    # YAKE keyphrase extraction
    kw_extractor = yake.KeywordExtractor(top=top_keyphrases, stopwords=None)

    # Load topic terms if provided
    topic_terms = load_topic_terms(topic_terms_path)
    topic_vecs = None
    if topic_terms:
        topic_vecs = build_topic_vectors(topic_terms, vectorizer)

    # Build graph
    G = nx.Graph()

    for i, (title, body) in enumerate(chunks):
        # Extract keywords
        keywords = tfidf_keywords_for_row(X[i], feature_names, top_keywords)
        keyphrases = [kw for kw, _ in kw_extractor.extract_keywords(body)]

        # Classify topics
        tags = []
        if topic_terms and topic_vecs:
            node_vec = X[i]
            tags = classify_node_topics(node_vec, topic_terms, topic_vecs, vectorizer)

        # Fallback: use title + keywords as tags
        if not tags:
            tags = [title.lower().replace(" ", "_")]

        G.add_node(
            i,
            title=title,
            body=body,
            keywords=keywords,
            keyphrases=keyphrases,
            tags=tags,
        )

    # Add edges based on similarity
    similarity_matrix = cosine_similarity(X)
    for i in range(len(chunks)):
        for j in range(i + 1, len(chunks)):
            sim = similarity_matrix[i, j]
            if sim >= min_similarity:
                G.add_edge(i, j, weight=float(sim))

    # Save graph
    graph_path = os.path.join(output_dir, "graph.json")
    graph_data = json_graph.node_link_data(G)
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2, ensure_ascii=False)

    print(f"Graph saved: {graph_path}")
    print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

    # Save individual node markdown files
    for node_id, data in G.nodes(data=True):
        node_file = os.path.join(nodes_dir, f"node_{node_id}.md")
        with open(node_file, "w", encoding="utf-8") as f:
            f.write(f"# {data['title']}\n\n")
            f.write(f"**Tags:** {', '.join(data['tags'])}\n\n")
            f.write(f"**Keywords:** {', '.join(data['keywords'])}\n\n")
            f.write(f"**Keyphrases:** {', '.join(data['keyphrases'])}\n\n")
            f.write("---\n\n")
            f.write(data["body"] + "\n")

    print(f"Markdown nodes written to: {nodes_dir}/")


# ----------------------------------------------------------
# Topic-based context extraction
# ----------------------------------------------------------


def extract_topic_context(
    topic: str,
    graph_path: str,
    output_file: str,
    include_neighbors: bool = True,
) -> None:
    """
    Extract nodes related to a specific topic from the graph.
    If include_neighbors is True, also include connected nodes.
    """
    with open(graph_path, encoding="utf-8") as f:
        graph_data = json.load(f)

    G = json_graph.node_link_graph(graph_data)

    # Find nodes matching topic
    matching_nodes = []
    for node_id, data in G.nodes(data=True):
        tags = data.get("tags", [])
        if any(topic.lower() in tag.lower() for tag in tags):
            matching_nodes.append(node_id)

    if not matching_nodes:
        print(f"No nodes found for topic '{topic}'")
        return

    # Optionally include neighbors
    expanded = set(matching_nodes)
    if include_neighbors:
        for node_id in matching_nodes:
            expanded.update(G.neighbors(node_id))

    # Sort by node_id for consistent output
    selected_nodes = sorted(expanded)

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# Topic Context: {topic}\n\n")
        f.write(f"Extracted {len(selected_nodes)} nodes.\n\n")
        f.write("---\n\n")

        for node_id in selected_nodes:
            data = G.nodes[node_id]
            f.write(f"## [{node_id}] {data['title']}\n\n")
            f.write(f"**Tags:** {', '.join(data['tags'])}\n\n")
            f.write(f"**Keywords:** {', '.join(data['keywords'])}\n\n")
            f.write(f"**Keyphrases:** {', '.join(data['keyphrases'])}\n\n")
            f.write("---\n\n")
            f.write(data["body"])
            f.write("\n\n")

    print(f"Topic context for '{topic}' written to: {output_file}")
