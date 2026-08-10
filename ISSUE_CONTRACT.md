# Issue contract — CRM Action Authority

## Problem
Trusted autonomous action over CRM context and enterprise integration layers.

## Desired outcome
A bounded, open, testable implementation of **CRM Action Authority** that demonstrates Gate CRM mutations behind grants with field scopes and reverse-operation receipts.

## Non-goals
- Salesforce affiliation or proprietary integration
- Portfolio-wide scale/performance claims
- UI marketing site

## Acceptance
1. Mechanism module implements allow + refuse with structured receipts
2. pytest behavioral suite green
3. operate.py cold-start produces JSON receipt
4. Non-affiliation disclaimer preserved
