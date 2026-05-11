# sqlsift

A Python library for detecting slow queries and generating optimization suggestions from query logs.

---

## Installation

```bash
pip install sqlsift
```

---

## Usage

```python
from sqlsift import QueryAnalyzer

analyzer = QueryAnalyzer(threshold_ms=500)

# Load and analyze a query log file
results = analyzer.analyze("query.log")

for entry in results.slow_queries:
    print(f"[{entry.duration_ms}ms] {entry.query}")
    print(f"  Suggestion: {entry.suggestion}")
    print()
```

**Example output:**

```
[1243ms] SELECT * FROM orders WHERE customer_id = 42
  Suggestion: Consider adding an index on `orders.customer_id`.

[876ms] SELECT * FROM products
  Suggestion: Avoid SELECT *; specify only required columns.
```

You can also pass raw query strings directly:

```python
suggestion = analyzer.suggest("SELECT * FROM users WHERE email = 'test@example.com'")
print(suggestion)
# → Consider adding an index on `users.email`.
```

---

## Features

- Parses common SQL query log formats (MySQL, PostgreSQL)
- Flags queries exceeding a configurable time threshold
- Provides human-readable optimization suggestions
- Supports batch analysis and single-query inspection

---

## License

This project is licensed under the [MIT License](LICENSE).