#!/usr/bin/env python3
"""
MM Number Extractor - Validates regex patterns against test samples.

This script tests the MM number extraction regex against the 20 sample emails
to ensure accurate extraction while ignoring PO numbers, dates, and other distractors.
"""

import re
import json
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    """Result of MM number extraction attempt."""
    sample_id: int | str
    expected: str
    extracted: Optional[str]
    success: bool
    full_match: Optional[str]


# Primary regex pattern for MM number extraction
# Matches: mm 1234567, MM1234567, mm#1234567, MM: 1234567, mm-1234567, mm:1234567
MM_PATTERN = re.compile(
    r'\b[Mm]{2}[\s:#-]?\s*(\d{7})\b',
    re.IGNORECASE
)

# Alternative pattern including "material" prefix
MM_PATTERN_WITH_MATERIAL = re.compile(
    r'\b(?:material\s+)?[Mm]{2}[\s:#-]?\s*(\d{7})\b',
    re.IGNORECASE
)


def extract_mm_number(text: str) -> Optional[str]:
    """
    Extract MM number from text.
    
    Args:
        text: Email body or combined subject+body text
        
    Returns:
        7-digit MM number as string, or None if not found
    """
    match = MM_PATTERN.search(text)
    if match:
        return match.group(1)
    return None


def extract_all_mm_numbers(text: str) -> List[str]:
    """
    Extract all MM numbers from text.
    
    Args:
        text: Email body or combined subject+body text
        
    Returns:
        List of 7-digit MM numbers found
    """
    matches = MM_PATTERN.findall(text)
    return matches


def validate_sample(sample: dict, expected_mm: str) -> ExtractionResult:
    """
    Validate extraction against a single sample.
    
    Args:
        sample: Sample dict with 'id', 'subject', 'body' keys
        expected_mm: Expected MM number to extract
        
    Returns:
        ExtractionResult with validation details
    """
    combined_text = f"{sample['subject']} {sample['body']}"
    extracted = extract_mm_number(combined_text)
    
    # Get full match for debugging
    match = MM_PATTERN.search(combined_text)
    full_match = match.group(0) if match else None
    
    return ExtractionResult(
        sample_id=sample['id'],
        expected=expected_mm,
        extracted=extracted,
        success=extracted == expected_mm,
        full_match=full_match
    )


def run_tests(samples_file: str = 'test_samples.json') -> None:
    """
    Run extraction tests on all samples and print results.
    
    Args:
        samples_file: Path to JSON file with test samples
    """
    with open(samples_file, 'r') as f:
        data = json.load(f)
    
    expected_mm = data['expected_mm_number']
    samples = data['samples']
    negative_cases = data.get('negative_test_cases', [])
    
    print("=" * 60)
    print("MM Number Extraction Test Results")
    print("=" * 60)
    print(f"\nExpected MM Number: {expected_mm}")
    print(f"Regex Pattern: {MM_PATTERN.pattern}")
    print("\n" + "-" * 60)
    print("POSITIVE TEST CASES (should find MM number)")
    print("-" * 60)
    
    passed = 0
    failed = 0
    
    for sample in samples:
        result = validate_sample(sample, expected_mm)
        status = "PASS" if result.success else "FAIL"
        
        if result.success:
            passed += 1
        else:
            failed += 1
        
        print(f"\nSample {result.sample_id}: [{status}]")
        print(f"  Format: {sample.get('mm_format', 'N/A')}")
        print(f"  Extracted: {result.extracted}")
        print(f"  Full Match: {result.full_match}")
        
        if not result.success:
            print(f"  Expected: {result.expected}")
            print(f"  Body: {sample['body'][:50]}...")
    
    print("\n" + "-" * 60)
    print("NEGATIVE TEST CASES (should NOT find MM number)")
    print("-" * 60)
    
    neg_passed = 0
    neg_failed = 0
    
    for sample in negative_cases:
        combined_text = f"{sample['subject']} {sample['body']}"
        extracted = extract_mm_number(combined_text)
        expected_none = sample['expected_result'] == 'NO_MM_FOUND'
        
        if expected_none and extracted is None:
            status = "PASS"
            neg_passed += 1
        elif not expected_none and extracted is not None:
            status = "PASS"
            neg_passed += 1
        else:
            status = "FAIL"
            neg_failed += 1
        
        print(f"\nSample {sample['id']}: [{status}]")
        print(f"  Reason: {sample['reason']}")
        print(f"  Extracted: {extracted if extracted else 'None (correct)'}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Positive Tests: {passed}/{len(samples)} passed")
    print(f"Negative Tests: {neg_passed}/{len(negative_cases)} passed")
    total_passed = passed + neg_passed
    total_tests = len(samples) + len(negative_cases)
    print(f"Overall: {total_passed}/{total_tests} ({100*total_passed/total_tests:.1f}%)")
    
    if failed == 0 and neg_failed == 0:
        print("\nAll tests passed!")
    else:
        print(f"\n{failed + neg_failed} test(s) failed - review regex pattern")


def demo_extraction():
    """Demonstrate extraction on sample texts."""
    test_texts = [
        "Can you confirm whether mm 1234567 has shipped yet?",
        "Following up on material MM1234567 from last week.",
        "This is regarding item mm#1234567 tied to the order.",
        "Vendor asked about MM: 1234567",
        "We are still waiting on mm-1234567",
        "Only following up on mm:1234567",
        "Just touching base on mm1234567",
        "PO 4900999999 was submitted on 01/15/2026",  # No MM
        "Call me at 555-123-4567",  # Phone number, not MM
    ]
    
    print("\nDemo Extraction Results:")
    print("-" * 40)
    
    for text in test_texts:
        result = extract_mm_number(text)
        print(f"Input: {text[:50]}...")
        print(f"  -> MM: {result if result else 'NO_MM_FOUND'}")
        print()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        demo_extraction()
    else:
        run_tests()
