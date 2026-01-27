# Lean Playground Code Guidelines

## Project Structure
- **algorithms/**: QuantConnect Lean algorithm projects (Python)
- **research/**: Standalone Jupyter research notebooks
- **data/**: Local market data for Lean engine (download separately)
- **results/**: Backtest output and reports
- **scripts/**: Utility scripts
- **tests/**: Smoke and integration tests

## Commands

### Installation
```bash
uv pip install -r requirements.txt  # Install dependencies
```

### Running Backtests
```bash
# Via Lean CLI
lean backtest algorithms/sample_sma_crossover

# Via script
./scripts/run_backtest.sh algorithms/sample_sma_crossover
```

### Research
```bash
# Start Jupyter Lab
./scripts/start_jupyter.sh
# Open http://localhost:8888/lab
```

### Data Management
```bash
# Download sample data from QuantConnect
./scripts/download_data.sh
```

### Testing
```bash
pytest tests/ -v
```

## Code Style

### General
- **Doc Style**: Google-style docstrings with Args/Returns
- **Typing**: Use type annotations extensively
- **Naming**: CamelCase for classes, snake_case for methods/functions/variables
- **Imports**: Standard lib first, external packages second, internal modules last

### Lean Algorithm Conventions
- Algorithms inherit from `QCAlgorithm`
- Use `from AlgorithmImports import *` for imports
- Implement `initialize()` for setup and `on_data()` for logic
- Use snake_case method names (Lean Python API convention)
- Each algorithm project has its own directory with `main.py`

### Python Best Practices
- **Error Handling**: Try-except blocks with specific exception types
- **Testing**: Use pytest fixtures, smoke tests for environment verification

==================

Center on programming a domain model with rich understanding of processes/rules. Focus on core domain logic, base designs on domain models, iteratively refine.

Never use mocks or fallbacks to patch the issues. Implement the intended functionality and fix the root causes of the problems. Raise errors when the code can not operate properly. Don't cover problems by silencing the exceptions. Keep the code elegant and clean.

When runnig tests, if tests fail, investigate the failures and look for root causes. The problems might be either in the source code or the tests. The end goal is to have the code run as intended, not just pass the tests.

Apply the principles from "Code Complete" by Steve McConnell:
- Tame complexity with disciplined abstractions and naming conventions.
- Quality is speed: Prevent defects during construction to ship faster.
- Plan before typing—understand requirements, sketch designs, spot risks.
- Write for people first: Clear formatting, self-explanatory identifiers, meaningful comments only where intent needs context.
- Modularize & encapsulate so changes touch the fewest files.
- Program defensively: Validate inputs, handle errors explicitly, guard against nulls and edge cases.
- Iterate & refactor relentlessly—continuous small improvements beat big-bang rewrites.

Apply the principles from "Clean Architecture" by Robert C. Martin:
- Dependency Rule: Source code dependencies point inward toward business rules.
- Core is framework-, UI-, and DB-agnostic—outer layers depend on inner, never vice-versa.
- Architecture's purpose: Keep options open and minimize long-term human effort.
- Scale SOLID upward: Reuse/Release, Common-Closure, Common-Reuse; aim for acyclic, stable-yet-abstract components.
- Push volatile details (frameworks, gateways) to the periphery.
- "Screaming Architecture": Folder names and boundaries should shout the business intent, not the technology stack.

Apply principles from "Clean Code" by Robert C. Martin:
- Code is read far more than written—optimize for clarity.
- KISS and consistent; avoid accidental complexity.
- Small, single-purpose functions & classes; eliminate duplication (DRY).
- Use intention-revealing, searchable names and uniform formatting.
- Apply SOLID at code level: Prefer polymorphism, inject dependencies.
  - Single Responsibility: Each class has one purpose.
  - Open/Closed: Open for extension, closed for modification.
  - Liskov Substitution: Derived classes must be substitutable.
  - Interface Segregation: Many client-specific interfaces over general-purpose.
  - Dependency Inversion: Depend on abstractions, not concretions.
- Boy-Scout Rule: Leave every file cleaner than found.
- Fast, independent, self-validating tests (TDD mindset).
- Prefer exceptions to error codes; separate error-handling paths.
- Prefer composition over inheritance.
- Code to interfaces, not implementations.
- Encapsulate changing parts.

Architectural Decisions Prioritization (in order):
- Reliability
- Performance
- Modularity
- Testability
- Maintainability
- Deployability

Additional Principles:
- Follow established patterns/styles.
- Design for extensibility/future changes.
- Maintain clear component boundaries.
- Use appropriate abstractions.
- Consider security in decisions.
- Plan for observability/monitoring
- Design for scalability where needed.
- Keep clean abstractions, encapsulation, separation of concerns.
- Apply Design Patterns appropriately (e.g., State for Position, Observer for events).
