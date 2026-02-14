#!/usr/bin/env python3
"""Extract samples for manual review"""
import json
import random

with open('al_rased/data/labeledSamples/training_data.json', 'r') as f:
    data = json.load(f)

# Extract unique samples from each weak category
categories = ['Hacking', 'Financial Scams', 'Spam']

for cat in categories:
    samples = [d for d in data if d['label'] == cat and not d.get('is_augmented', False)]
    unique = list({d['text']: d for d in samples}.values())
    
    print('\n' + '='*70)
    print(f'📂 {cat.upper()} (Unique: {len(unique)})')
    print('='*70)
    
    # Show 10 random unique samples
    preview = random.sample(unique, min(10, len(unique)))
    for i, d in enumerate(preview, 1):
        txt = d['text'].replace('\n', ' ')[:120]
        print(f'{i}. {txt}...')
