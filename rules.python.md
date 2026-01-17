## Cardinal Rules - Engineering Standards

> These are non-negotiable principles for all code in this repo. Failure to adhere will result in code rejection or possible dismissal.

These principles guide all code contributions.  They exist to maintain quality,
enable collaboration, and ensure long-term maintainability. 

---

## 1. Self-Documenting Code

Write code that explains itself through clear naming and logical structure. 
Use comments only when explaining non-obvious business requirements, complex algorithms, or surprising behavior.

### ❌ Bad:  Comment-dependent code

```python
# Get the user
def get(id):
    # Check if id is valid
    if id is None:
        return None
    # Query the database
    r = db.query(f"SELECT * FROM users WHERE id = {id}")
    # Return first result
    return r[0] if r else None
```

### ✅ Good: Self-explanatory code

```python
def get_user_by_id(user_id:  int) -> User | None:
    if user_id is None:
        return None
    results = db.query("SELECT * FROM users WHERE id = %s", [user_id])
    return results[0] if results else None
```

### ✅ Good: Comment explains WHY, not WHAT

```python
def calculate_retry_delay(attempt: int) -> float:
    # Exponential backoff required:  upstream API rate limit resets on 60s window
    # Linear retry caused cascading failures in prod (incident INC-2847)
    return min(2 ** attempt, 60)
```

---

## 2. Strategic Documentation

Write docstrings for public APIs, LLM-consumed tools, and complex functions.
Skip docstrings for self-evident helper functions. 

### ❌ Bad:  Docstring adds no value

```python
def add(a: int, b: int) -> int:
    """
    Add two numbers. 

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The sum of a and b.
    """
    return a + b
```

### ✅ Good: Docstring provides essential context

```python
def calculate_compound_interest(
    principal:  Decimal,
    annual_rate:  Decimal,
    years: int,
    compounding_frequency: int = 12
) -> Decimal:
    """
    Calculate compound interest using standard financial formula.

    Args:
        principal: Initial investment amount (must be positive)
        annual_rate: Annual interest rate as decimal (e.g., 0.05 for 5%)
        years: Investment duration in years
        compounding_frequency: Times interest compounds per year (default:  monthly)

    Returns:
        Final amount after compound interest applied

    Raises:
        ValueError:  If principal is negative or rate exceeds 100%

    Example:
        >>> calculate_compound_interest(Decimal("1000"), Decimal("0.05"), 10)
        Decimal('1647.01')
    """
```

### ✅ Good: LLM tool with complete docstring

```python
def search_customer_orders(
    customer_id: str,
    status:  Literal["pending", "shipped", "delivered"] | None = None,
    limit: int = 10
) -> list[Order]:
    """
    Search for orders belonging to a specific customer.

    Use this tool when users ask about their order history, order status,
    or need to find a specific order.  Always confirm the customer_id
    before searching.

    Args:
        customer_id:  Unique customer identifier (format: CUS-XXXXX)
        status: Filter by order status.  If None, returns all statuses.
        limit: Maximum number of orders to return (default: 10, max: 100)

    Returns:
        List of Order objects sorted by date descending (newest first)
    """
```

---

## 3. Type Safety (Required)

All functions must have complete type annotations for parameters and return types. 

### ❌ Bad: Missing or incomplete types

```python
def process_users(users, active_only=True):
    result = []
    for user in users:
        if active_only and not user.get("active"):
            continue
        result. append(user)
    return result
```

### ✅ Good: Complete type annotations

```python
from typing import TypedDict

class UserRecord(TypedDict):
    id: int
    name: str
    active: bool

def process_users(
    users: list[UserRecord],
    active_only: bool = True
) -> list[UserRecord]:
    return [
        user for user in users
        if not active_only or user["active"]
    ]
```

### ✅ Good: Complex types with aliases for readability

```python
from typing import TypeAlias
from collections.abc import Callable, Awaitable

JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
AsyncHandler: TypeAlias = Callable[[Request], Awaitable[Response]]

def register_route(
    path: str,
    handler: AsyncHandler,
    methods: list[str] | None = None
) -> None:
    ...
```

---

## 4. Automated Formatting

Use `ruff` for formatting and linting.  Configure pre-commit hooks to automate this.

### Setup

```bash
# Install
pip install ruff

# Format code
ruff format .

# Check and fix linting issues
ruff check --fix .
```

### Pre-commit configuration

```yaml name=".pre-commit-config.yaml"
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

### CI enforcement

```yaml name=".github/workflows/lint.yml"
name: Lint
on: [push, pull_request]
jobs: 
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/ruff-action@v1
        with: 
          args: "check --output-format=github"
      - uses: astral-sh/ruff-action@v1
        with: 
          args: "format --check"
```

---

## 5. Meaningful Tests

Focus on testing critical functionality, not chasing coverage percentages.

### ❌ Bad: Tests that chase coverage but miss real bugs

```python
def test_user_exists():
    user = User(name="test")
    assert user.name == "test"  # Tests nothing meaningful

def test_list_not_empty():
    users = [User(name="test")]
    assert len(users) > 0  # Obvious, adds no value
```

### ✅ Good: Tests that catch real bugs

```python
class TestOrderPriceCalculation:
    """Price calculation is critical business logic - test edge cases thoroughly."""

    def test_applies_percentage_discount_correctly(self):
        order = Order(subtotal=Decimal("100.00"))
        order.apply_discount(DiscountType.PERCENTAGE, Decimal("15"))
        assert order.total == Decimal("85.00")

    def test_discount_cannot_exceed_subtotal(self):
        order = Order(subtotal=Decimal("50.00"))
        order.apply_discount(DiscountType. FIXED, Decimal("75"))
        assert order.total == Decimal("0.00")  # Not negative! 

    def test_multiple_discounts_apply_sequentially(self):
        order = Order(subtotal=Decimal("100.00"))
        order.apply_discount(DiscountType. PERCENTAGE, Decimal("10"))  # -> 90
        order.apply_discount(DiscountType.FIXED, Decimal("5"))        # -> 85
        assert order.total == Decimal("85.00")

    def test_handles_zero_subtotal(self):
        order = Order(subtotal=Decimal("0.00"))
        order.apply_discount(DiscountType.PERCENTAGE, Decimal("50"))
        assert order.total == Decimal("0.00")


class TestPaymentProcessing:
    """External integration - test failure modes."""

    def test_retries_on_network_timeout(self, mocker):
        mock_gateway = mocker.patch("payments.gateway.charge")
        mock_gateway.side_effect = [TimeoutError(), TimeoutError(), {"status": "success"}]

        result = process_payment(amount=Decimal("50.00"), retries=3)

        assert result. status == "success"
        assert mock_gateway.call_count == 3

    def test_fails_gracefully_after_max_retries(self, mocker):
        mock_gateway = mocker.patch("payments. gateway.charge")
        mock_gateway.side_effect = TimeoutError()

        result = process_payment(amount=Decimal("50.00"), retries=3)

        assert result.status == "failed"
        assert result.error_code == "GATEWAY_TIMEOUT"
```

### What to test (prioritized)

| Priority | Category | Example |
|----------|----------|---------|
| 🔴 Critical | Business logic with conditionals | Pricing, discounts, eligibility |
| 🔴 Critical | Data transformations | ETL, serialization, parsing |
| 🟠 High | External integrations | API calls, database queries |
| 🟠 High | Error handling paths | Retries, fallbacks, validation |
| 🟡 Medium | State transitions | Workflows, status changes |
| 🟢 Low | Pure utility functions | Usually obvious, test if complex |

---

## 6. Documentation-Driven Development

Verify against official documentation before making changes.  Use available tools to validate assumptions.

### ❌ Bad: Assuming API behavior

```python
# "I think this is how it works..."
response = requests.get(url, timeout=30)
data = response.json()  # Assumes 200 OK, assumes JSON response
return data["results"]  # Assumes "results" key exists
```

### ✅ Good: Verified against documentation

```python
# Verified against API docs:  https://api.example.com/docs/v2/search
# - Returns 200 with JSON on success
# - Returns 429 with Retry-After header on rate limit
# - Results are paginated with "results" array and "next_cursor" field

response = requests.get(url, timeout=30)
response.raise_for_status()

data = response.json()
if "results" not in data:
    raise APIContractError(f"Expected 'results' key in response:  {data. keys()}")

return SearchResults(
    items=data["results"],
    next_cursor=data.get("next_cursor")
)
```

### ❌ Bad: Using deprecated packages

```python
# Don't use deprecated/unmaintained packages
from dateutil.parser import parse  # OK but check if still maintained
import asyncio_redis  # Last updated 2019 - find alternative
```

### ✅ Good: Verify package health before adoption

```markdown
Before adding a dependency, check:
- [ ] Last commit date (< 1 year preferred)
- [ ] Open issues / response time
- [ ] Security advisories (pip-audit, safety)
- [ ] License compatibility
- [ ] Active maintainer(s)
```

### Available research tools

| Tool | Use for |
|------|---------|
| Official docs | API contracts, SDK usage |
| Context7 | Library-specific patterns |
| Web search | Recent changes, deprecations |
| `pip-audit` | Security vulnerabilities |
| GitHub issues | Known bugs, workarounds |

---

## 7. Maintainable Code

Write the least amount of code necessary to solve the problem correctly.  Every line of code is a liability—it must be read, understood, tested, and maintained for years.  Optimize for deletion. 

### Core Principles

| Principle | Description |
|-----------|-------------|
| **Less is more** | The best code is code that doesn't exist |
| **Clarity over cleverness** | Write for the reader, not to impress |
| **Optimize for deletion** | Code should be easy to remove when requirements change |
| **Single responsibility** | Each function/class does one thing well |
| **Shallow abstractions** | Avoid deep nesting and inheritance hierarchies |

---

### ❌ Bad: Over-engineered abstraction

```python
class AbstractDataProcessorFactory(ABC):
    @abstractmethod
    def create_processor(self) -> "AbstractDataProcessor":
        ... 

class AbstractDataProcessor(ABC):
    @abstractmethod
    def preprocess(self, data: Any) -> Any:
        ... 
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        ...
    
    @abstractmethod
    def postprocess(self, data: Any) -> Any:
        ... 

class ConcreteUserDataProcessorFactory(AbstractDataProcessorFactory):
    def create_processor(self) -> "ConcreteUserDataProcessor":
        return ConcreteUserDataProcessor()

class ConcreteUserDataProcessor(AbstractDataProcessor):
    def preprocess(self, data: dict) -> dict:
        return data
    
    def process(self, data: dict) -> dict:
        return {k: v. strip() if isinstance(v, str) else v for k, v in data.items()}
    
    def postprocess(self, data: dict) -> dict:
        return data

# Usage (finally!)
factory = ConcreteUserDataProcessorFactory()
processor = factory.create_processor()
result = processor.postprocess(processor.process(processor.preprocess(data)))
```

### ✅ Good:  Simple function that does the job

```python
def clean_user_data(data: dict[str, Any]) -> dict[str, Any]:
    """Strip whitespace from string values."""
    return {k: v.strip() if isinstance(v, str) else v for k, v in data.items()}

# Usage
result = clean_user_data(data)
```

---

### ❌ Bad:  Clever one-liner that's hard to debug

```python
def get_active_admin_emails(users: list[User]) -> list[str]:
    return [u.email for u in users if u.active and u.role == "admin" and u.email and "@" in u.email and not u.email.endswith(". invalid") and u.verified_at is not None]
```

### ✅ Good: Clear, debuggable, and testable

```python
def is_valid_admin(user: User) -> bool:
    """Check if user is an active, verified admin with valid email."""
    if not user.active:
        return False
    if user.role != "admin":
        return False
    if not user. email or "@" not in user.email:
        return False
    if user.email.endswith(".invalid"):
        return False
    if user.verified_at is None:
        return False
    return True

def get_active_admin_emails(users: list[User]) -> list[str]:
    return [user.email for user in users if is_valid_admin(user)]
```

---

### ❌ Bad: Premature abstraction

```python
# "We might need to support other databases someday..."
class DatabaseAdapter(ABC):
    @abstractmethod
    def connect(self) -> None: ...
    @abstractmethod
    def query(self, sql: str) -> list[dict]: ...
    @abstractmethod
    def execute(self, sql:  str) -> int: ...

class PostgresAdapter(DatabaseAdapter):
    def connect(self) -> None:
        self.conn = psycopg2.connect(...)
    
    def query(self, sql: str) -> list[dict]:
        # 50 lines of implementation
        ... 
    
    def execute(self, sql: str) -> int:
        # 30 lines of implementation
        ... 

class MySQLAdapter(DatabaseAdapter):  # Never actually used
    ... 

class SQLiteAdapter(DatabaseAdapter):  # Never actually used
    ... 
```

### ✅ Good: Solve today's problem, refactor when needed

```python
# Just use PostgreSQL - that's what we have
import psycopg2
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        yield conn
    finally: 
        conn.close()

def fetch_users(active_only: bool = True) -> list[User]:
    query = "SELECT * FROM users WHERE active = %s"
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, [active_only])
            return [User(**row) for row in cur.fetchall()]

# If we ever need MySQL, we refactor THEN - not now
```

---

### ❌ Bad: Deep nesting

```python
def process_order(order: Order) -> Result:
    if order is not None:
        if order.items:
            if order.customer: 
                if order.customer.active:
                    if order.payment_method:
                        if order. payment_method.valid:
                            total = calculate_total(order)
                            if total > 0:
                                if order.customer.balance >= total:
                                    # Finally, the actual logic buried 8 levels deep
                                    return charge_customer(order. customer, total)
                                else: 
                                    return Result. error("Insufficient balance")
                            else:
                                return Result.error("Invalid total")
                        else:
                            return Result.error("Invalid payment method")
                    else: 
                        return Result.error("No payment method")
                else:
                    return Result.error("Inactive customer")
            else:
                return Result.error("No customer")
        else:
            return Result.error("No items")
    else:
        return Result. error("No order")
```

### ✅ Good: Early returns, flat structure

```python
def process_order(order: Order | None) -> Result:
    if order is None:
        return Result.error("No order")
    
    if not order.items:
        return Result.error("No items")
    
    if not order.customer or not order.customer.active:
        return Result.error("Invalid or inactive customer")
    
    if not order.payment_method or not order.payment_method.valid:
        return Result.error("Invalid payment method")
    
    total = calculate_total(order)
    if total <= 0:
        return Result. error("Invalid total")
    
    if order.customer.balance < total:
        return Result.error("Insufficient balance")
    
    return charge_customer(order. customer, total)
```

---

### ❌ Bad:  Reinventing the wheel

```python
def remove_duplicates(items: list[str]) -> list[str]:
    """Remove duplicates while preserving order."""
    seen = []
    result = []
    for item in items:
        if item not in seen:
            seen. append(item)
            result. append(item)
    return result

def merge_dicts(dict1: dict, dict2: dict) -> dict:
    """Merge two dictionaries."""
    result = {}
    for k, v in dict1.items():
        result[k] = v
    for k, v in dict2.items():
        result[k] = v
    return result
```

### ✅ Good: Use the standard library

```python
from collections import OrderedDict

def remove_duplicates(items: list[str]) -> list[str]:
    return list(dict. fromkeys(items))

def merge_dicts(dict1: dict, dict2: dict) -> dict:
    return {**dict1, **dict2}  # Or dict1 | dict2 in Python 3.9+
```

---

### ❌ Bad: Unnecessary state and classes

```python
class StringProcessor:
    def __init__(self):
        self.input_string = None
        self.processed = False
    
    def set_input(self, s: str) -> None:
        self.input_string = s
        self.processed = False
    
    def process(self) -> None:
        if self.input_string is None:
            raise ValueError("No input set")
        self.input_string = self.input_string.strip().lower()
        self.processed = True
    
    def get_result(self) -> str:
        if not self.processed:
            raise ValueError("Not processed yet")
        return self.input_string

# Usage
processor = StringProcessor()
processor.set_input("  HELLO  ")
processor.process()
result = processor.get_result()
```

### ✅ Good: Just a function

```python
def normalize_string(s: str) -> str:
    return s.strip().lower()

# Usage
result = normalize_string("  HELLO  ")
```

---

### Maintenance Cost Formula

Think of every line of code as having ongoing costs: 

```
Annual Cost = Lines of Code × (
    Reading Time +      # Every new team member reads it
    Debugging Time +    # Time spent when things break  
    Testing Time +      # Tests must be maintained too
    Update Time +       # Dependencies, Python versions, etc.
    Review Time         # Every change needs re-review
)
```

**Less code = lower cost = sustainable velocity**

---

### Decision Framework

Before writing code, ask: 

```
┌─────────────────────────────────────────────────────┐
│ 1. Can I delete this requirement entirely?           │
│    └─→ Best outcome: no code needed                 │
│                                                     │
│ 2. Does a standard library solution exist?          │
│    └─→ Use it:  battle-tested, maintained for free   │
│                                                     │
│ 3. Does a well-maintained package solve this?       │
│    └─→ Evaluate: is the dependency worth it?        │
│                                                     │
│ 4. Can I solve this with a simple function?         │
│    └─→ Start here, refactor to class only if needed │
│                                                     │
│ 5. Do I need this abstraction NOW or "someday"?     │
│    └─→ YAGNI: You Aren't Gonna Need It              │
└─────────────────────────────────────────────────────┘
```

---

### Code Smell Checklist

| Smell | Symptom | Fix |
|-------|---------|-----|
| **Speculative generality** | Abstractions with one implementation | Delete the abstraction |
| **Dead code** | Unused functions, commented blocks | Delete it (git remembers) |
| **Feature envy** | Function uses another class's data heavily | Move it to that class |
| **Long parameter lists** | 5+ parameters | Use a dataclass/TypedDict |
| **Deep nesting** | 3+ levels of indentation | Early returns, extract functions |
| **Primitive obsession** | Passing around raw dicts/tuples | Create domain types |
| **Copy-paste code** | Same logic in multiple places | Extract shared function |

---

### The Ultimate Test

> "Can a new team member understand this code in under 5 minutes?"

If not, simplify. 
```
