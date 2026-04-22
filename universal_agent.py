import os
import re
import httpx
from typing import List, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class UniversalAgent:
    def __init__(self):
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.headers = {"User-Agent": "Mozilla/5.0"}

    async def run(self, query: str, assets: Optional[List[str]] = []) -> str:
        q_lower = query.lower()
        html_context = ""
        
        # 1. DIRECT FETCH
        if assets:
            try:
                async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
                    resp = await client.get(assets[0], timeout=10.0)
                    html = resp.text
                    # Isolate the infobox area for the LLM
                    infobox_match = re.search(r'class="[^"]*infobox[^"]*".*?</table>', html, re.DOTALL | re.IGNORECASE)
                    html_context = infobox_match.group(0) if infobox_match else html[:30000]
            except:
                html_context = "Error fetching asset."

        # 2. MASTER EXTRACTION PROMPT
        prompt = (
            f"HTML_CODE: {html_context}\n\n"
            f"QUERY: {query}\n\n"
            "INSTRUCTION: Find the image 'src' attribute requested. "
            "Return ONLY the literal string found in the HTML. "
            "NO sentences. NO quotes. NO explanation. "
            "If you see multiple resolutions, pick the one in the 'src' attribute."
        )

        try:
            r = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200, temperature=0
            )
            ans = r.choices[0].message.content.strip().strip("'\"")
            
            # 3. DIRECT LINK CLEANUP
            # If the LLM returns a sentence, extract just the link part
            link_match = re.search(r'(//upload\.wikimedia\.org/\S+)', ans)
            if link_match: return link_match.group(1)
            
            return ans
        except:
            return "Error"

agent = UniversalAgent()
