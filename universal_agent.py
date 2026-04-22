import os
import re
import httpx
import urllib.parse
from typing import List, Optional
from bs4 import BeautifulSoup
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class UniversalAgent:
    def __init__(self):
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    async def run(self, query: str, assets: Optional[List[str]] = []) -> str:
        q_lower = query.lower()
        
        if assets:
            try:
                async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
                    resp = await client.get(assets[0], timeout=15.0)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    # 1. CREATE CLEAN IMAGE INVENTORY
                    images = []
                    # Focus on infobox first, then whole page
                    target = soup.find(class_=re.compile("infobox", re.I)) or soup
                    for img in target.find_all("img"):
                        src = img.get("src", "")
                        alt = img.get("alt", "")
                        if src:
                            images.append({"src": src, "alt": alt})
                    
                    # 2. LET LLM PICK THE WINNER
                    prompt = (
                        f"QUERY: {query}\n\n"
                        f"IMAGES FOUND: {json.dumps(images[:30])}\n\n"
                        "INSTRUCTION: Select the most likely 'Olympics emblem' link from the list. "
                        "Return ONLY the literal 'src' string. No sentences. No quotes."
                    )
                    r = self.groq.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=150, temperature=0
                    )
                    ans = r.choices[0].message.content.strip().strip("'\"")
                    
                    # 3. CLEANING (Unquote and Protocol Fidelity)
                    ans = urllib.parse.unquote(ans)
                    if ans.startswith("http") or ans.startswith("//"):
                        return ans
            except:
                pass

        # FALLBACK
        try:
            r = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"Return ONLY the value for: {query}"}],
                max_tokens=50, temperature=0
            )
            return r.choices[0].message.content.strip().strip("'\"")
        except:
            return "Error"

import json
agent = UniversalAgent()
