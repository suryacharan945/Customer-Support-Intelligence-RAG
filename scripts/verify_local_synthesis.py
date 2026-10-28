"""
Verification script for Local Grounded Synthesizer and Auto Provider Fallback.
"""

import asyncio
from app.generation.local_synthesizer import LocalGroundedSynthesizer
from app.generation.llm_client import LLMClient

async def main():
    print("Testing LocalGroundedSynthesizer directly...")
    mcp_prompt = """================ MULTI-CONTEXT EVIDENCE BLOCKS ================
[Category: warranty]
[Source: prox400_warranty.pdf, Page: 1, Chunk: chunk_w1]
The ApexPrint ProX-400 includes a 1-year standard limited warranty covering defective parts and manufacturing defects.

[Category: troubleshooting]
[Source: prox400_troubleshooting.pdf, Page: 4, Chunk: chunk_t2]
For Error E-101, power cycle the printer: switch off, unplug for 60 seconds, reconnect power cord, and turn on.

================ CUSTOMER SUPPORT INQUIRY ================
What is the warranty coverage for ProX-400 and how to fix error E-101?

Response Format:
1. Executive Summary / Direct Answer
2. Step-by-Step Resolution / Technical Specifications
3. Warranty & Policy Cross-Reference (if applicable)
4. Verified Source Citations"""

    res = LocalGroundedSynthesizer().synthesize(
        prompt_text=mcp_prompt,
    )
    print("MCP Local Synthesis Result:\n", res["text"])
    assert "[Source: prox400_warranty.pdf, Page: 1, Chunk: chunk_w1]" in res["text"]
    assert "[Source: prox400_troubleshooting.pdf, Page: 4, Chunk: chunk_t2]" in res["text"]
    print("\nDirect Synthesizer Test Passed!")

    print("\nTesting LLMClient with provider='local'...")
    client = LLMClient(allow_mock=True, allow_fallback=True)
    resp = await client.generate_response(
        system_prompt="System Prompt",
        user_prompt=mcp_prompt,
        provider="local",
    )
    print("Provider:", resp.get("provider"))
    print("Is Mock:", resp.get("is_mock"))
    assert resp.get("provider") == "local_grounded"
    print("\nLLMClient Local Provider Test Passed!")

    print("\nTesting LLMClient with provider='auto' when endpoint is down...")
    resp_auto = await client.generate_response(
        system_prompt="System Prompt",
        user_prompt=mcp_prompt,
        provider="auto",
    )
    print("Auto Provider returned:", resp_auto.get("provider"))
    assert resp_auto.get("provider") == "local_grounded_fallback"
    print("\nLLMClient Auto Fallback Test Passed Successfully!")

if __name__ == "__main__":
    asyncio.run(main())
