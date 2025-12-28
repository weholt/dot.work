import argparse

from .pipeline import build_graph, discover_topics, extract_topic_context


def main():
    parser = argparse.ArgumentParser(
        description="Knowledge Graph Tool: Build, discover topics, and extract context."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # discover-topics
    disc = subparsers.add_parser(
        "discover-topics",
        help="Discover topics from a document using unsupervised clustering.",
    )
    disc.add_argument("--input", required=True, help="Input markdown file")
    disc.add_argument("--output", required=True, help="Output JSON file for topic terms")
    disc.add_argument("--num-topics", type=int, default=5, help="Number of topics")
    disc.add_argument("--terms-per-topic", type=int, default=10, help="Terms per topic")

    # build
    build = subparsers.add_parser("build", help="Build knowledge graph from document.")
    build.add_argument("--input", required=True, help="Input markdown file")
    build.add_argument("--output", required=True, help="Output directory for graph/nodes")
    build.add_argument("--min-sim", type=float, default=0.3, help="Min similarity for edges")
    build.add_argument("--top-keywords", type=int, default=5, help="Top TF-IDF keywords")
    build.add_argument("--top-keyphrases", type=int, default=5, help="Top YAKE keyphrases")
    build.add_argument("--topics", default=None, help="Path to topic_terms.json")

    # extract
    extract = subparsers.add_parser("extract", help="Extract topic-based context from graph.")
    extract.add_argument("--topic", required=True, help="Topic to extract")
    extract.add_argument("--graph", required=True, help="Path to graph.json")
    extract.add_argument("--output", required=True, help="Output markdown file")
    extract.add_argument(
        "--include-neighbors",
        action="store_true",
        help="Include neighbors of matching nodes",
    )

    args = parser.parse_args()

    if args.command == "discover-topics":
        discover_topics(
            input_file=args.input,
            output_file=args.output,
            num_topics=args.num_topics,
            terms_per_topic=args.terms_per_topic,
        )
    elif args.command == "build":
        build_graph(
            input_file=args.input,
            output_dir=args.output,
            min_similarity=args.min_sim,
            top_keywords=args.top_keywords,
            top_keyphrases=args.top_keyphrases,
            topic_terms_path=args.topics,
        )
    elif args.command == "extract":
        extract_topic_context(
            topic=args.topic,
            graph_path=args.graph,
            output_file=args.output,
            include_neighbors=args.include_neighbors,
        )


if __name__ == "__main__":
    main()
