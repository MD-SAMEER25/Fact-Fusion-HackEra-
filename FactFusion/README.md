# Research-Focused RAG Pipeline

A specialized Retrieval-Augmented Generation (RAG) pipeline designed exclusively for academic research and scholarly verification. This pipeline searches across multiple academic databases to provide comprehensive evidence for research claims and academic fact-checking.

## Features

- **Academic-Specific Search**:
  - Google Scholar - Access peer-reviewed papers and citation metrics
  - arXiv - Search for preprints and research papers
  - Semantic Scholar - Find papers with detailed metadata and citation networks
  - ResearchGate - Access research profiles and publications
  - Wikipedia - Background information and context

- **Research Analysis**:
  - Academic trust score based on scholarly evidence
  - Supporting and contradictory points from academic papers
  - Detailed explanations with references to specific research

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

The pipeline requires API keys for certain services:

- Gemini API Key (for analysis)
- Serper.dev API Key (for ResearchGate search)
- Semantic Scholar API Key (optional, for higher rate limits)

Update the API keys in the `Config` class in `rag_pipeline.py`.

## Usage

```python
from rag_pipeline import fact_check

# Example usage with a research claim
result = fact_check("Quantum computing has achieved quantum supremacy")

# Access results
print(f"Trust Score: {result.trust_score}")
print(f"Explanation: {result.explanation}")
print("\nSupporting Points from Academic Papers:")
for point in result.supporting_points:
    print(f"- {point}")
print("\nContradictory Points from Academic Papers:")
for point in result.contradictory_points:
    print(f"- {point}")

# Access raw academic sources
for source in result.academic_sources:
    print(f"\nSource: {source['source']}")
    print(f"Title: {source['title']}")
    print(f"Authors: {', '.join(source['authors'])}")
    print(f"URL: {source['url']}")
```

## How It Works

1. **Academic Evidence Retrieval**: The pipeline searches across multiple academic databases for relevant research papers and publications.
2. **Evidence Analysis**: The retrieved academic evidence is analyzed using Google's Gemini model.
3. **Result Generation**: A structured result is returned with a trust score, explanation, and supporting/contradictory points from academic sources.

## Academic Sources

The pipeline searches the following academic databases:

- **Google Scholar**: Peer-reviewed papers, theses, books, and conference proceedings
- **arXiv**: Preprints and research papers in physics, mathematics, computer science, and more
- **Semantic Scholar**: Papers with detailed metadata, citation networks, and research summaries
- **ResearchGate**: Research profiles and publications from academic researchers
- **Wikipedia**: Background information and context (for reference only)

## Limitations

- API rate limits may apply for some academic services
- ResearchGate search uses web search as a workaround since they don't provide an official API
- Some academic sources may require authentication for full access
- The quality of results depends on the availability of open-access papers

## License

MIT 