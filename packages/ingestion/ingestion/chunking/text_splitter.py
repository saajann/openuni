import re
from typing import List

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Splits text into chunks of roughly `chunk_size` words, 
    with an overlap of `overlap` words.
    For v0, we use a simple word-based splitting approach which is fast and requires no extra dependencies.
    """
    words = re.findall(r'\S+', text)
    chunks = []
    
    if not words:
        return []
        
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
        
        # Avoid infinite loop if overlap >= chunk_size
        if chunk_size - overlap <= 0:
            break
            
    return chunks
