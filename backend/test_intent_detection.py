#!/usr/bin/env python3
"""Quick test script to verify intent detection functionality."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.rag.engine import RAGEngine

def test_intent_detection():
    """Test the intent detection system."""
    engine = RAGEngine()
    
    test_cases = [
        ("Hello", "greeting", "en"),
        ("Habari", "greeting", "sw"),
        ("Hi there!", "greeting", "en"),
        ("Mambo", "greeting", "sw"),
        ("Good morning", "greeting", "en"),
        ("Shikamoo", "greeting", "sw"),
        ("Bye", "farewell", "en"),
        ("Kwaheri", "farewell", "sw"),
        ("Goodbye!", "farewell", "en"),
        ("See you later", "farewell", "en"),
        ("Thank you", "appreciation", "en"),
        ("Thanks!", "appreciation", "en"),
        ("Asante", "appreciation", "sw"),
        ("Nashukuru", "appreciation", "sw"),
        ("Can you help me?", "help_request", "en"),
        ("I need assistance", "help_request", "en"),
        ("Msaada", "help_request", "sw"),
        ("Saidia", "help_request", "sw"),
        ("What causes infertility?", "knowledge_question", "en"),
        ("Is IVF effective?", "knowledge_question", "en"),
    ]
    
    print("Testing Intent Detection System")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for query, expected_intent, expected_lang in test_cases:
        detected_intent = engine.detect_intent(query)
        detected_lang = engine.detect_language(query)
        
        intent_match = detected_intent == expected_intent
        lang_match = detected_lang == expected_lang
        
        status = "✓" if (intent_match and lang_match) else "✗"
        
        if intent_match and lang_match:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} Query: '{query}'")
        if not intent_match:
            print(f"  Expected intent: {expected_intent}, Got: {detected_intent}")
        if not lang_match:
            print(f"  Expected lang: {expected_lang}, Got: {detected_lang}")
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    
    # Test response generation
    print("\nTesting Response Generation")
    print("=" * 60)
    
    response_tests = [
        ("Hello", "en"),
        ("Habari", "sw"),
        ("Thank you", "en"),
        ("Asante", "sw"),
        ("Bye", "en"),
        ("Kwaheri", "sw"),
    ]
    
    for query, lang in response_tests:
        intent = engine.detect_intent(query)
        if intent in ["greeting", "farewell", "appreciation", "help_request"]:
            response = engine.generate_intent_response(intent, lang)
            print(f"Query: '{query}' ({lang})")
            print(f"Response: {response[:100]}...")
            print()
    
    return failed == 0

if __name__ == "__main__":
    try:
        success = test_intent_detection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)