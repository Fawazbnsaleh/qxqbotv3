#!/usr/bin/env python3
"""
COMPLETE MANUAL VERIFICATION
Extract 10 samples from each category for human review
"""
import json
import random

print('🔍 COMPLETE MANUAL VERIFICATION')
print('=' * 70)

with open('al_rased/data/labeledSamples/training_data.json', 'r') as f:
    data = json.load(f)

categories = ['Academic Cheating', 'Medical Fraud', 'Financial Scams', 'Spam', 'Hacking', 'Unethical', 'Normal']

for cat in categories:
    samples = [d for d in data if d['label'] == cat and not d.get('is_augmented') and not d.get('upsampled_by')]
    
    # Get 10 random unique samples
    unique = list({d['text']: d for d in samples}.values())
    preview = random.sample(unique, min(10, len(unique)))
    
    print(f'\n{"="*70}')
    print(f'📂 {cat.upper()} ({len(unique)} unique samples)')
    print('='*70)
    
    for i, d in enumerate(preview, 1):
        txt = d['text'].replace('\n', ' ')[:120]
        source = d.get('source', 'original')
        print(f'{i:2}. [{source[:10]:10}] {txt}...')
