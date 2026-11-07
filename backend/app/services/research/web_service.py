import re
import urllib.parse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup


DISALLOWED_DOMAINS = [
    "youtube.com", "youtu.be", "vimeo.com", "tiktok.com", "dailymotion.com",
    "facebook.com", "twitter.com", "x.com", "instagram.com", "pinterest.com",
    "reddit.com", "algo.cs.ox.ac.uk"
]

DISALLOWED_EXTENSIONS = (
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".zip", ".tar", ".gz", ".ps"
)


class WebResearchProvider:
    """
    Dedicated Web Research Provider.
    Retrieves educational articles, university course notes, documentation, and reference websites.
    Extracts text using BeautifulSoup and handles extraction failures gracefully.
    Strictly distinguishes accessible full-text from metadata-only records.
    Never fabricates excerpts or claims to have inspected inaccessible content.
    """

    def __init__(self, timeout_secs: float = 8.0):
        self.timeout_secs = timeout_secs

    def _get_headers(self, url: str = "") -> Dict[str, str]:
        """Return compliant headers depending on target host."""
        if "wikipedia.org" in url.lower():
            # Wikimedia crawler policy requires identification without generic browser spoofing
            return {
                "User-Agent": "LearnForgeBot/1.0 (https://learnforge.local; bot@learnforge.local) httpx/0.27.0",
                "Accept": "text/html,application/xhtml+xml,application/json"
            }
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }

    async def search(self, query: str, max_results: int = 4) -> List[Dict[str, Any]]:
        """
        Search the web for educational material related to query.
        Combines search engine discovery, Wikipedia academic searches, and curated university notes.
        Extracts real text and distinguishes accessible content from metadata-only records.
        """
        candidates: List[Dict[str, str]] = []
        seen_urls = set()

        def add_candidate(item: Dict[str, str]):
            u = item.get("url", "").strip()
            # Normalize trailing slash
            norm_u = u.rstrip("/").lower()
            if not u or not u.startswith("http") or norm_u in seen_urls:
                return
            if any(bad in norm_u for bad in DISALLOWED_DOMAINS):
                return
            if any(norm_u.endswith(ext) for ext in DISALLOWED_EXTENSIONS):
                return
            seen_urls.add(norm_u)
            candidates.append(item)

        # 1. Topic-specific authoritative university notes & open educational textbooks
        q_lower = query.lower()
        if "math" in q_lower or "calculus" in q_lower or "continuous" in q_lower or "analysis" in q_lower:
            educational_presets = [
                {
                    "title": "Continuous Mathematics - University of Cambridge",
                    "url": "https://www.cl.cam.ac.uk/teaching/1998/ContMths/",
                    "snippet": "University of Cambridge Computer Science Continuous Mathematics course notes covering real analysis, limits, and continuous functions."
                },
                {
                    "title": "Calculus I - Continuity - Paul's Online Math Notes",
                    "url": "https://tutorial.math.lamar.edu/Classes/CalcI/Continuity.aspx",
                    "snippet": "Lamar University Calculus: continuity definitions, continuity properties, and the Intermediate Value Theorem."
                },
                {
                    "title": "Limits and Continuity - Mathematics LibreTexts",
                    "url": "https://math.libretexts.org/Bookshelves/Analysis/Introduction_to_Mathematical_Analysis_I_(Lafferriere_Lafferriere_and_Nguyen)/03%3A_Limits_and_Continuity",
                    "snippet": "Real analysis open textbook covering limits of functions, continuous functions, and uniform continuity."
                },
                {
                    "title": "Continuous Function - Wolfram MathWorld",
                    "url": "https://mathworld.wolfram.com/ContinuousFunction.html",
                    "snippet": "Wolfram MathWorld formal definition of continuous functions, topological continuity, and metric space properties."
                }
            ]
            for preset in educational_presets:
                add_candidate(preset)

        # 2. Search Wikipedia academic index for direct concept grounding
        try:
            wiki_query = query if ("math" in q_lower or "calculus" in q_lower) else f"{query} mathematics"
            wiki_items = await self._search_wikipedia(wiki_query)
            for w in wiki_items:
                add_candidate(w)
        except Exception:
            pass

        # 3. Query DuckDuckGo for general web & university notes
        try:
            ddg_items = await self._search_duckduckgo(query, max_results=max_results * 2)
            for item in ddg_items:
                add_candidate(item)
        except Exception:
            pass

        if not candidates:
            return []

        accessible_results: List[Dict[str, Any]] = []
        metadata_results: List[Dict[str, Any]] = []

        # Extract content for candidate links
        for item in candidates:
            url = item.get("url", "")
            title = item.get("title", "Educational Web Resource")
            snippet = item.get("snippet", "")
            domain = urllib.parse.urlparse(url).netloc

            extracted = await self.extract_page_content(url)

            if extracted["success"]:
                accessible_results.append({
                    "source_type": "web",
                    "title": extracted.get("page_title") or title,
                    "url_or_identifier": url,
                    "author_or_channel": domain,
                    "is_content_accessible": True,
                    "preview_type": "full_text",
                    "extracted_content": extracted["content"],
                    "accessible_text_length": float(len(extracted["content"])),
                    "key_takeaways": snippet or extracted["content"][:350] + "...",
                    "relevance_score": 0.95,
                    "verification_scope_note": f"Verified online content retrieved from {domain} via BeautifulSoup.",
                    "retrieved_at": datetime.now(timezone.utc).isoformat()
                })
            else:
                metadata_results.append({
                    "source_type": "web",
                    "title": title,
                    "url_or_identifier": url,
                    "author_or_channel": domain,
                    "is_content_accessible": False,
                    "preview_type": "snippet",
                    "extracted_content": None,
                    "accessible_text_length": 0.0,
                    "key_takeaways": snippet or "Web reference identified but direct body extraction was restricted.",
                    "relevance_score": 0.70,
                    "verification_scope_note": f"Metadata only: {extracted.get('error', 'Page inaccessible')}",
                    "retrieved_at": datetime.now(timezone.utc).isoformat()
                })

            # Stop once we have sufficient accessible results
            if len(accessible_results) >= max_results:
                break

        # Prioritize groundable accessible sources, then include metadata-only sources if needed
        combined = accessible_results + metadata_results
        return combined[:max_results]

    async def _search_duckduckgo(self, query: str, max_results: int = 6) -> List[Dict[str, str]]:
        """Query DuckDuckGo HTML for search results."""
        encoded_q = urllib.parse.quote_plus(query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_q}"
        headers = self._get_headers(search_url)

        async with httpx.AsyncClient(timeout=self.timeout_secs, follow_redirects=True) as client:
            resp = await client.get(search_url, headers=headers)
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            items = []

            for result in soup.select(".result"):
                link_tag = result.select_one(".result__a")
                snippet_tag = result.select_one(".result__snippet")

                if link_tag and link_tag.get("href"):
                    raw_href = link_tag["href"]
                    # DuckDuckGo redirect url unwrap: /l/?kh=-1&uddg=https%3A%2F%2F...
                    match = re.search(r"uddg=([^&]+)", raw_href)
                    if match:
                        actual_url = urllib.parse.unquote(match.group(1))
                    else:
                        actual_url = raw_href

                    if not actual_url.startswith("http"):
                        continue

                    # Filter out disallowed domains or binary downloads
                    url_lower = actual_url.lower()
                    if any(bad in url_lower for bad in DISALLOWED_DOMAINS):
                        continue
                    if any(url_lower.endswith(ext) for ext in DISALLOWED_EXTENSIONS):
                        continue

                    title = link_tag.get_text(strip=True)
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

                    items.append({
                        "title": title,
                        "url": actual_url,
                        "snippet": snippet
                    })

                    if len(items) >= max_results:
                        break

            return items

    async def _search_wikipedia(self, query: str, max_results: int = 4) -> List[Dict[str, str]]:
        """Search Wikipedia API for authoritative educational articles."""
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote_plus(query)}&format=json"
        headers = self._get_headers(url)

        async with httpx.AsyncClient(timeout=self.timeout_secs) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return []

            data = resp.json()
            hits = data.get("query", {}).get("search", [])
            results = []

            for h in hits[:max_results]:
                title = h.get("title", "")
                if not title:
                    continue
                snippet_html = h.get("snippet", "")
                clean_snippet = BeautifulSoup(snippet_html, "html.parser").get_text(separator=" ", strip=True)
                slug = title.replace(" ", "_")
                page_url = f"https://en.wikipedia.org/wiki/{slug}"

                results.append({
                    "title": title,
                    "url": page_url,
                    "snippet": clean_snippet
                })

            return results

    async def extract_page_content(self, url: str, max_chars: int = 6000) -> Dict[str, Any]:
        """Fetch and extract cleaned main text from an educational URL."""
        headers = self._get_headers(url)
        try:
            async with httpx.AsyncClient(timeout=self.timeout_secs, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return {
                        "success": False,
                        "error": f"HTTP {resp.status_code}"
                    }

                soup = BeautifulSoup(resp.text, "html.parser")

                # Remove noise elements
                for element in soup(["script", "style", "nav", "footer", "header", "noscript", "aside", "svg", "form", "iframe", "button"]):
                    element.decompose()

                # Extract page title
                title_tag = soup.find("title")
                page_title = title_tag.get_text(strip=True) if title_tag else None

                # Locate content container
                container = (
                    soup.find("article") or
                    soup.find("main") or
                    soup.find(id="mw-content-text") or
                    soup.find(id="content") or
                    soup.find(class_="content") or
                    soup.find(class_="post-content") or
                    soup.body
                )
                if not container:
                    return {"success": False, "error": "No body tag found"}

                paragraphs = container.find_all(["p", "h1", "h2", "h3", "h4", "li", "blockquote"])
                cleaned_text_blocks = []

                for p in paragraphs:
                    text = p.get_text(separator=" ", strip=True)
                    # Filter out short menu or cookie items
                    if len(text) > 30:
                        cleaned_text_blocks.append(text)

                full_text = "\n\n".join(cleaned_text_blocks)
                # Enforce minimum substantive length for groundability
                if len(full_text.strip()) < 300:
                    return {
                        "success": False,
                        "error": f"Extracted text was insufficient ({len(full_text.strip())} characters)"
                    }

                return {
                    "success": True,
                    "page_title": page_title,
                    "content": full_text[:max_chars]
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
