import os
import requests
import wikipedia
import google.generativeai as genai
from typing import Dict, List, Optional
from dataclasses import dataclass
import time
import re
import json

# Configuration class with your API keys
@dataclass
class Config:
    GEMINI_API_KEY: str = "AIzaSyCsqkr_INXR9HWviIQDUVhVYOlJaMzv2NY"
    SERPER_API_KEY: str = "1590cbf576e9b2f119a7c9eed4ba0c5fc17f1aa6"
    # Add Semantic Scholar API key if available
    SEMANTIC_SCHOLAR_API_KEY: str = ""

config = Config()

# Response structure
@dataclass
class FactCheckResult:
    trust_score: float
    explanation: str
    supporting_points: List[str]
    contradictory_points: List[str]
    raw_evidence: str
    academic_sources: List[Dict]

def configure():
    """Configure API connections with model verification"""
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # Verify model availability
        available_models = [m.name for m in genai.list_models()]
        if 'models/gemini-1.5-flash-latest' not in available_models:
            raise ValueError("Required Gemini model not available")
            
        # Test Wikipedia connection
        wikipedia.set_lang("en")
        wikipedia.search("test")
        
        return True
    except Exception as e:
        print(f"Configuration error: {e}")
        return False

def search_wikipedia(query: str, max_results: int = 3) -> str:
    """Search Wikipedia with query length management"""
    try:
        # Truncate query to 300 characters
        truncated_query = (query[:280] + "...") if len(query) > 300 else query
        search_results = wikipedia.search(truncated_query)[:max_results]
        
        evidence = []
        for title in search_results:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                evidence.append(
                    f"Title: {page.title}\n"
                    f"URL: https://en.wikipedia.org/wiki/{page.title.replace(' ', '_')}\n"
                    f"Content: {page.content[:1500]}..."
                )
            except:
                continue
        
        return "\n\n".join(evidence) if evidence else "No Wikipedia results found"
    except Exception as e:
        return f"Wikipedia search error: {str(e)}"

def search_semantic_scholar(query: str, max_results: int = 15) -> List[Dict]:
    """Search Semantic Scholar for academic papers"""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,authors,year,abstract,url,citationCount,venue,openAccessPdf,publicationTypes"
    }
    headers = {}
    
    if config.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = config.SEMANTIC_SCHOLAR_API_KEY
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for paper in data.get("data", []):
            paper_info = {
                "title": paper.get("title", "N/A"),
                "authors": [author.get("name", "N/A") for author in paper.get("authors", [])],
                "year": paper.get("year", "N/A"),
                "abstract": paper.get("abstract", "N/A"),
                "citations": paper.get("citationCount", 0),
                "url": paper.get("url", "N/A"),
                "venue": paper.get("venue", "N/A"),
                "pdf_url": paper.get("openAccessPdf", {}).get("url", "N/A"),
                "publication_types": paper.get("publicationTypes", []),
                "source": "Semantic Scholar"
            }
            results.append(paper_info)
        
        return results
    except Exception as e:
        print(f"Semantic Scholar search error: {str(e)}")
        return []

def search_serper(query: str, max_results: int = 5) -> List[Dict]:
    """Search academic sources using Serper.dev"""
    url = "https://google.serper.dev/search"
    payload = {
        "q": f"{query} site:arxiv.org OR site:researchgate.net OR site:academia.edu",
        "gl": "us",
        "hl": "en",
        "num": max_results
    }
    headers = {
        "X-API-KEY": config.SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for res in data.get("organic", []):
            # Extract domain from URL
            url = res.get("link", "")
            domain = url.split("/")[2] if len(url.split("/")) > 2 else ""
            
            paper_info = {
                "title": res.get("title", "N/A"),
                "url": url,
                "snippet": res.get("snippet", "N/A"),
                "source": domain
            }
            results.append(paper_info)
        
        return results
    except Exception as e:
        print(f"Serper search error: {str(e)}")
        return []

def format_academic_results(results: List[Dict]) -> str:
    """Format academic search results into a readable string"""
    if not results:
        return "No results found"
    
    formatted = []
    for i, result in enumerate(results, 1):
        source = result.get("source", "Unknown")
        title = result.get("title", "N/A")
        authors = result.get("authors", ["N/A"])
        authors_str = ", ".join(authors) if isinstance(authors, list) else authors
        
        formatted.append(f"Result {i} ({source}):")
        formatted.append(f"Title: {title}")
        
        if authors_str != "N/A":
            formatted.append(f"Authors: {authors_str}")
        
        if "year" in result and result["year"] != "N/A":
            formatted.append(f"Year: {result['year']}")
        
        if "abstract" in result and result["abstract"] != "N/A":
            formatted.append(f"Abstract: {result['abstract'][:500]}...")
        
        if "citations" in result:
            formatted.append(f"Citations: {result['citations']}")
        
        if "url" in result and result["url"] != "N/A":
            formatted.append(f"URL: {result['url']}")
        
        if "pdf_url" in result and result["pdf_url"] != "N/A":
            formatted.append(f"PDF URL: {result['pdf_url']}")
        
        if "venue" in result and result["venue"] != "N/A":
            formatted.append(f"Venue: {result['venue']}")
        
        if "publication_types" in result and result["publication_types"]:
            formatted.append(f"Publication Types: {', '.join(result['publication_types'])}")
        
        if "snippet" in result and result["snippet"] != "N/A":
            formatted.append(f"Snippet: {result['snippet']}")
        
        formatted.append("")
    
    return "\n".join(formatted)

def retrieve_evidence(claim: str) -> tuple:
    """Retrieve and combine evidence from multiple academic sources"""
    # Collect results from academic sources
    semantic_results = search_semantic_scholar(claim)
    serper_results = search_serper(claim)
    
    # Combine all results
    all_results = semantic_results + serper_results
    
    # Format results for display
    formatted_evidence = format_academic_results(all_results)
    
    return formatted_evidence, all_results

def analyze_with_gemini(claim: str, evidence: str, academic_sources: List[Dict]) -> FactCheckResult:
    """Verify claim against evidence using Gemini 1.5 Flash"""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""Analyze this research claim against the provided academic evidence. Return:
        1. Trust score (0-100) - how well the academic evidence supports the claim
        2. Concise explanation of verification based on academic sources
        3. List of supporting points from academic papers (if any)
        4. List of contradictory points from academic papers (if any)

        Claim: {claim}

        Evidence:
        {evidence[:30000]}  # Truncate to stay within model limits

        Respond in this exact format:
        Trust Score: [number between 0-100]
        Explanation: [text]
        Supporting Points:
        - [point 1]
        - [point 2]
        Contradictory Points:
        - [point 1]
        - [point 2]
        """

        response = model.generate_content(prompt)
        return parse_gemini_response(response.text, evidence, academic_sources)
    except Exception as e:
        return FactCheckResult(
            trust_score=0,
            explanation=f"Analysis error: {str(e)}",
            supporting_points=[],
            contradictory_points=[],
            raw_evidence=evidence,
            academic_sources=academic_sources
        )

def parse_gemini_response(response: str, raw_evidence: str, academic_sources: List[Dict]) -> FactCheckResult:
    """Parse Gemini's response into structured format"""
    result = FactCheckResult(
        trust_score=0,
        explanation="",
        supporting_points=[],
        contradictory_points=[],
        raw_evidence=raw_evidence,
        academic_sources=academic_sources
    )
    
    current_section = None
    
    for line in response.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        if line.startswith("Trust Score:"):
            try:
                result.trust_score = float(line.split(":")[1].strip())
            except:
                pass
        elif line.startswith("Explanation:"):
            result.explanation = line.split(":", 1)[1].strip()
        elif line.startswith("Supporting Points:"):
            current_section = "supporting"
        elif line.startswith("Contradictory Points:"):
            current_section = "contradictory"
        elif line.startswith("- "):
            point = line[2:].strip()
            if current_section == "supporting":
                result.supporting_points.append(point)
            elif current_section == "contradictory":
                result.contradictory_points.append(point)
    
    return result

def fact_check(claim: str) -> FactCheckResult:
    """Complete research-focused fact-checking pipeline"""
    evidence, academic_sources = retrieve_evidence(claim)
    return analyze_with_gemini(claim, evidence, academic_sources)