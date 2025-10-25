#!/usr/bin/env python3
"""
Test with ULTRA OPTIMIZED prompt
"""

import requests

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

# ULTRA STRICT SYSTEM MESSAGE
system_message = """You are a grammar checker. Find grammar mistakes and list them.

OUTPUT FORMAT (STRICT):

**Found X mistakes:**

1. ❌ "wrong phrase" → ✅ "correct phrase"
2. ❌ "wrong phrase" → ✅ "correct phrase"

If no mistakes: Say "No grammar mistakes found."

RULES:
- Only list actual grammar mistakes
- Ignore technical terms (AWS, S3, Bedrock, Google)
- Be brief
- No long explanations"""

# Test transcript with known errors
transcript = """Hi everyone. Last week I learned something interesting topic about AWS, Bedrock and Google Vision. Both are Cloud Flood Farm for Dexter extraction from PDF images and any Bedrock model."""

# ULTRA DIRECT PROMPT
prompt = f"""List grammar mistakes in this text:

"{transcript}"

Find:
- Missing "a/an/the"
- Wrong prepositions ("learned something topic" needs "about")
- Wrong verb forms

Technical words (AWS, Bedrock, S3, Google) are CORRECT - ignore them.

Format:
1. ❌ "wrong" → ✅ "correct"
2. ❌ "wrong" → ✅ "correct"

Be brief. Only list mistakes."""

print("=" * 70)
print("TESTING ULTRA-OPTIMIZED PROMPT")
print("=" * 70)
print(f"\nTranscript:\n{transcript}\n")
print("-" * 70)

try:
    response = requests.post(
        LM_STUDIO_URL,
        json={
            "model": "deepseek-coder-v2-lite-instruct",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,  # Very strict
            "max_tokens": 300    # Short response
        },
        timeout=30
    )
    
    if response.ok:
        result = response.json()
        feedback = result['choices'][0]['message']['content']
        
        print("AI FEEDBACK:")
        print("=" * 70)
        print(feedback)
        print("=" * 70)
        
        # Expected errors to find
        print("\nEXPECTED ERRORS:")
        print("1. 'learned something interesting topic' → 'learned about an interesting topic'")
        print("   (missing 'about' and 'an')")
        print("\n2. 'Cloud Flood Farm' → should be 'Cloud Platform'")
        print("   (transcription/pronunciation error)")
        
    else:
        print(f"❌ FAILED - Status: {response.status_code}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")