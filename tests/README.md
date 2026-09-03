# Development test plan

This test suite is intended for development stability checks only. It is not a user-facing feature set.

## Core regression tests
- demo ranking stability for the packaged sample dataset
- filter compatibility for legacy dict filters and new rule-based filters
- export correctness for CSV and XLSX
- deterministic MCDA ranking on the sample data

## GUI smoke tests
- application window can initialize
- data preview renders after loading or generating data
- analysis results populate the results table
- export buttons do not crash on valid result sets

## Recommended workflow
1. Run the focused subset for the feature being changed.
2. Run the full development suite before a release candidate.
3. Keep demo-data ranking assertions as a guardrail for structural regressions.
