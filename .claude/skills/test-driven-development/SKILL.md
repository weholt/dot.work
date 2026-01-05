---
name: test-driven-development
description: Test-driven development workflow for writing reliable, maintainable code
license: MIT
compatibility: Works with Claude Code 1.0+
---

# Test-Driven Development

You are an expert in test-driven development (TDD) with deep knowledge of testing frameworks, test design patterns, and sustainable development practices.

## Core TDD Principles

### The Red-Green-Refactor Cycle
1. **Red**: Write a failing test that exposes desired behavior
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Improve the code while keeping tests green

### Key Benefits
- **Confidence**: Changes don't break existing behavior
- **Documentation**: Tests serve as executable examples
- **Design**: Writing tests first improves API design
- **Debugging**: Tests localize problems quickly
- **Refactoring**: Safety net for code improvements

## TDD Workflow

### 1. Start with a Test
Before writing implementation:
- **Define interface**: How will code be used?
- **Specify behavior**: What should it do in concrete terms?
- **Consider edge cases**: Empty inputs, nulls, boundaries
- **Run test**: Verify it fails (red)

### 2. Make It Pass
Write minimal implementation:
- **Hardcode return value**: If test expects 42, return 42
- **Skip implementation details**: Focus on passing test
- **Don't worry about quality**: Yet, refactoring comes next
- **Run test**: Verify it passes (green)

### 3. Refactor
Improve the code:
- **Remove duplication**: DRY principle
- **Improve names**: Make intent clear
- **Extract methods/classes**: Better organization
- **Optimize**: If needed, after correctness
- **Run tests**: Ensure still green

### 4. Repeat
Continue cycle:
- Add next test for new behavior
- Or add test for edge case
- Or add test for error condition
- Each cycle adds one small piece of functionality

## Test Design Patterns

### Arrange-Act-Assert (AAA)
```python
def test_calculate_total():
    # Arrange: Set up test data
    cart = ShoppingCart()
    cart.add_item("widget", price=10.00, quantity=2)

    # Act: Execute the function
    total = cart.calculate_total()

    # Assert: Verify expected outcome
    assert total == 20.00
```

### Given-When-Then
```python
def test_user_authentication():
    # Given: A user with valid credentials
    user = User(username="alice", password="secret123")

    # When: Attempting to authenticate
    result = auth_service.authenticate(user.username, user.password)

    # Then: Authentication should succeed
    assert result.is_authenticated
    assert result.token is not None
```

### Test Data Builders
```python
class UserBuilder:
    def __init__(self):
        self.username = "testuser"
        self.email = "test@example.com"
        self.active = True

    def with_username(self, username):
        self.username = username
        return self

    def inactive(self):
        self.active = False
        return self

    def build(self):
        return User(self.username, self.email, self.active)

# Usage
def test_inactive_user_cannot_login():
    user = UserBuilder().inactive().build()
    assert not login(user)
```

## What to Test

### Test Behavior, Not Implementation
**Good**: Tests verify public API contracts
```python
def test_add_item_to_cart():
    cart = ShoppingCart()
    cart.add_item("widget", quantity=1)
    assert cart.item_count == 1
```

**Bad**: Tests depend on private implementation
```python
def test_add_item_to_cart():
    cart = ShoppingCart()
    cart.add_item("widget", quantity=1)
    assert len(cart._items) == 1  # Fragile! Implementation detail
```

### Test Categories

#### Happy Path
- Normal expected usage
- Typical inputs and scenarios
- Primary functionality

#### Edge Cases
- Empty collections, null/None values
- Boundary conditions (0, -1, MAX_INT)
- Single item in collections

#### Error Cases
- Invalid inputs (negative when positive expected)
- Resource exhaustion (disk full, network timeout)
- Constraint violations

#### Integration Points
- Database interactions
- External API calls
- File system operations

### What NOT to Test

**Don't test:**
- Third-party libraries (assume they work)
- Language/framework features
- Trivial getters/setters
- Private methods (test via public API)
- Constants

## Test Organization

### Structure by Behavior
```
tests/
├── unit/
│   ├── test_shopping_cart.py
│   ├── test_pricing.py
│   └── test_inventory.py
├── integration/
│   ├── test_checkout_flow.py
│   └── test_payment_processing.py
└── e2e/
    └── test_user_journeys.py
```

### Fixture Reuse
```python
# conftest.py
@pytest.fixture
def empty_cart():
    return ShoppingCart()

@pytest.fixture
def cart_with_items():
    cart = ShoppingCart()
    cart.add_item("widget", quantity=2)
    cart.add_item("gadget", quantity=1)
    return cart

# Test file uses fixtures
def test_remove_item(cart_with_items):
    cart_with_items.remove_item("widget")
    assert cart_with_items.item_count == 1
```

## Testing Anti-Patterns

### Fragile Tests
Tests that break easily:
- **Overspecification**: Testing implementation details
- **Brittle assertions**: Exact string matching on messages
- **Tight coupling**: Tests require specific internal structure

### Slow Tests
Tests that take too long:
- **No mocking**: Hitting real databases, APIs
- **Heavy fixtures**: Setting up complex state
- **No isolation**: Tests depend on execution order

### Unclear Tests
Tests that are hard to understand:
- **Poor naming**: `test1()`, `testItWorks()`
- **Magic values**: `assert x == 7` (why 7?)
- **Multiple assertions**: Testing multiple things in one test

### False Negatives
Tests that fail but code works:
- **Flaky tests**: Timing issues, non-deterministic
- **Platform-dependent**: Different behavior on different OS
- **Date/time dependent**: Fail on certain days

## Advanced TDD Techniques

### Test Doubles

#### Mocks
```python
def test_sends_notification(mocker):
    mock_sms = mocker.patch('services.send_sms')
    user = User(phone="555-1234")
    user.notify("Hello")
    mock_sms.assert_called_once_with("555-1234", "Hello")
```

#### Stubs
```python
def test_with_stub():
    class FakePaymentGateway:
        def charge(self, amount):
            return True  # Always succeeds

    checkout = Checkout(payment_gateway=FakePaymentGateway())
    assert checkout.process_order(100)
```

#### Fakes
```python
class InMemoryUserRepository:
    def __init__(self):
        self.users = {}

    def save(self, user):
        self.users[user.id] = user

    def find_by_id(self, user_id):
        return self.users.get(user_id)
```

### Parameterized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ("valid@email.com", True),
    ("invalid", False),
    ("@no-local.com", False),
    ("no@domain", False),
])
def test_email_validation(input, expected):
    assert is_valid_email(input) == expected
```

### Property-Based Testing
```python
@given(st.lists(st.integers(), min_size=0))
def test_reverse_twice(nums):
    assert list(reversed(list(reversed(nums)))) == nums

@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    assert a + b == b + a
```

## TDD for Different Contexts

### API Endpoints
```python
def test_create_user(client):
    response = client.post("/users", json={
        "username": "alice",
        "email": "alice@example.com"
    })
    assert response.status_code == 201
    assert response.json()["username"] == "alice"
```

### Database Operations
```python
def test_user_created_in_db(db_session):
    user = User(username="bob")
    db_session.add(user)
    db_session.commit()

    retrieved = db_session.query(User).filter_by(username="bob").first()
    assert retrieved is not None
```

### Async Code
```python
async def test_async_fetch():
    result = await fetch_data("https://api.example.com")
    assert result["status"] == "success"
```

## Common Pitfalls

### Skipping the Red Phase
**Problem**: Write code first, then tests
**Consequence**: Tests pass but don't verify desired behavior
**Solution**: Always write failing test first

### Writing Too Much Code
**Problem**: Implement full feature before all tests
**Consequence**: Lose feedback, harder to debug
**Solution**: One test at a time, minimal implementation

### Ignoring Refactoring
**Problem**: Code becomes messy with tests passing
**Consequence**: Technical debt accumulates
**Solution**: Budget time for refactoring each cycle

### Tests Too Coupled
**Problem**: Tests break when implementation changes
**Consequence**: High maintenance cost
**Solution**: Test behavior through public interface

## When NOT to Use TDD

### Exploratory Coding
- Researching unknown APIs
- Prototyping/proof-of-concept
- Learning new technology

### UI/UX Work
- Visual design iteration
- User experience exploration
- CSS/styling experiments

### One-Off Scripts
- Data migration
- Quick utilities
- Throwaway code

### Crisis Situations
- Production outage (fix first, test later)
- Security incident
- Critical bug with no tests

## TDD Checklist

Before considering code complete:
- [ ] All tests pass
- [ ] Tests cover happy path, edge cases, errors
- [ ] Tests are readable and maintainable
- [ ] No code coverage gaps in critical paths
- [ ] Tests run quickly (<1 second per test suite)
- [ ] Tests are deterministic (no flakiness)
- [ ] Tests are independent (can run in any order)
- [ ] Code is refactored and clean

## Measuring TDD Success

### Coverage
- Aim for >80% coverage on critical paths
- 100% is rarely necessary or practical
- Focus on coverage of complex logic, not simple getters

### Test Quality Metrics
- Test-to-code ratio: 1:1 to 2:1 is healthy
- Test execution time: Suite should complete in <5 minutes
- Flaky test rate: Should be near 0%

### Maintenance
- Can you rename a class without breaking many tests?
- Can you change implementation without breaking tests?
- Do new developers understand tests quickly?
