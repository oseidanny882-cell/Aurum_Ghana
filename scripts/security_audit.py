#!/usr/bin/env python3
"""Comprehensive security audit of frontend files."""
import pathlib, re

base = pathlib.Path("c:/Users/Codewithme/jewelry-gh/frontend")

# Patterns to flag
DANGEROUS_PATTERNS = [
    (r'innerHTML\s*=\s*(?!["\']{3}|["\']?[a-zA-Z]+["\']?\s*\+|null|undefined|\s*["\'][^"\']*["\']\s*\+)',
     "innerHTML with dynamic content - check for XSS"),
    (r'insertAdjacentHTML', "insertAdjacentHTML - check for XSS"),
    (r'document\.write', "document.write - XSS risk"),
    (r'eval\s*\(', "eval() - code injection risk"),
    (r'new\s+Function\s*\(', "new Function() - dynamic code execution"),
    (r'setTimeout\s*\(\s*[^,\)]+\s*,\s*0\)', "setTimeout with string - potential eval-like risk"),
    (r'localStorage\.setItem\s*\(\s*["\']access_token["\']',
     "Tokens stored in localStorage (should use sessionStorage)"),
    (r'localStorage\.setItem\s*\(\s*["\']refresh_token["\']',
     "Refresh tokens in localStorage (should use sessionStorage)"),
    (r'localStorage\.setItem\s*\(\s*["\']user["\']',
     "User data in localStorage (should use sessionStorage)"),
    (r'password.*=\s*["\'][^"\']+["\']', "Hardcoded password in source"),
    (r'apikey["\']?\s*[:=]\s*["\'][^"\']+["\']', "Hardcoded API key"),
    (r'secret["\']?\s*[:=]\s*["\'][^"\']+["\']', "Hardcoded secret"),
    (r'\.src\s*=\s*[^;]+\+\s*[^;]+', "Dynamic script src injection"),
    (r'window\.location\s*=\s*[^;]+\+', "Dynamic URL redirect"),
    (r'fetch\s*\([^)]+,\s*\{[^}]*body:\s*[^}]*\+', "Dynamic body in fetch - potential injection"),
]

print("=" * 70)
print("SECURITY AUDIT REPORT - Aurum Ghana Frontend")
print("=" * 70)

all_issues = []

for js in sorted(base.glob("*.js")):
    text = js.read_text(encoding="utf-8")
    for pattern, desc in DANGEROUS_PATTERNS:
        for i, line in enumerate(text.split('\n'), 1):
            if re.search(pattern, line):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith('//') or stripped.startswith('*'):
                    continue
                # Skip Security module itself for escapeHtml checks
                if 'escapeHtml' in line and 'innerHTML' not in desc:
                    continue
                all_issues.append(f"  [{js.name}:{i}] {desc}")
                print(f"  [{js.name}:{i}] {desc}")
                # Show the line
                print(f"    -> {line.strip()[:100]}")

print()
print("-" * 70)

# Check HTML files for inline scripts and other issues
print("\nHTML SECURITY CHECKS:")
for html in sorted(base.glob("*.html")):
    text = html.read_text(encoding="utf-8")
    
    # Check for inline event handlers (onclick, onerror, etc.)
    inline_handlers = re.findall(r'\bon\w+\s*=\s*["\']([^"\']+)["\']', text)
    if inline_handlers:
        print(f"  [{html.name}] Inline event handlers found: {list(set(inline_handlers))[:5]}")
    
    # Check for javascript: URLs
    js_urls = re.findall(r'javascript:[^"\']+', text)
    if js_urls:
        print(f"  [{html.name}] javascript: URLs found: {js_urls[:3]}")
    
    # Check for data: URLs in img/script src
    data_urls = re.findall(r'(?:src|href)\s*=\s*["\']data:[^"\']+["\']', text)
    if data_urls:
        print(f"  [{html.name}] data: URLs found: {len(data_urls)}")

print()
print("=" * 70)
print(f"TOTAL ISSUES FOUND: {len(all_issues)}")
print("=" * 70)
