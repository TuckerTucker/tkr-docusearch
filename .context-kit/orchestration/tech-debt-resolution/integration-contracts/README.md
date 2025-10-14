# Integration Contracts

**Purpose**: Define explicit interfaces between components to enable zero-conflict parallel development

---

## Overview

Integration contracts are specifications that define:
- API signatures and return types
- Data schemas and formats
- Error handling patterns
- Integration points (where code connects)
- Usage examples and test cases

---

## Contract Lifecycle

```
Draft → Under Review → Published → Validated → Integrated
```

1. **Draft**: Contract author creates initial specification
2. **Under Review**: Consumer agents review for completeness
3. **Published**: Contract frozen, implementation begins
4. **Validated**: Tests confirm contract compliance
5. **Integrated**: Consumers successfully use the interface

---

## Contract Index

### Wave 1 Contracts

| Contract | Provider | Consumers | Status |
|----------|----------|-----------|--------|
| [file-validator-api.md](file-validator-api.md) | validation-core-agent | webhook-refactor, legacy-refactor, config-refactor | To be created |
| [worker-integration-spec.md](worker-integration-spec.md) | worker-analysis-agent | webhook-refactor, legacy-refactor | To be created |
| [config-integration-spec.md](config-integration-spec.md) | config-analysis-agent | webhook-config, legacy-config, config-refactor | To be created |

### Wave 4 Contracts

| Contract | Provider | Consumers | Status |
|----------|----------|-----------|--------|
| [worker-architecture-decision.md](worker-architecture-decision.md) | worker-decision-agent | documentation-agent | To be created |

---

## Contract Template

Use this template for new contracts:

```markdown
# {Contract Name}

**Provider**: {agent-name}
**Consumers**: {list-of-consumer-agents}
**Wave**: {wave-number}
**Status**: {draft | published | validated}
**Version**: 1.0
**Last Updated**: {date}

## Overview

Brief description of what this contract defines

## API Specification

### Module/File

`path/to/module.py`

### Functions

#### function_name

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    Brief description.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ErrorType: When this error occurs
    """
```

**Behavior**:
- What the function does
- Edge cases handled
- Performance characteristics

### Constants

```python
CONSTANT_NAME: Type = value
```

**Description**: What this constant represents

## Data Schemas

### Input Schema
```python
{
    "field": "type",
    "optional_field?": "type"
}
```

### Output Schema
```python
{
    "result": "type",
    "error": "type | null"
}
```

## Error Handling

| Error Type | Condition | Return Value | Example |
|------------|-----------|--------------|---------|
| ValueError | Invalid input | (False, "error msg") | Invalid file extension |
| TypeError | Wrong type | Raise exception | None passed as string |

## Integration Points

### Call Sites

| Location | Current Code | Replacement | Notes |
|----------|-------------|-------------|-------|
| file.py:123 | `old code` | `new code` | Preserve error format |

### Dependencies

**Required Modules**:
- module1 (for X)
- module2 (for Y)

**Environment Variables**:
- `ENV_VAR`: Description (default: value)

## Usage Examples

### Example 1: Basic Usage
```python
from module import function_name

result = function_name(param1, param2)
if result[0]:
    print("Success!")
else:
    print(f"Error: {result[1]}")
```

### Example 2: Error Handling
```python
try:
    result = function_name(param1, param2)
except ValueError as e:
    print(f"Validation error: {e}")
```

## Test Requirements

### Unit Tests
- [ ] Test normal operation
- [ ] Test error conditions
- [ ] Test edge cases
- [ ] Test type validation

### Integration Tests
- [ ] Test with real consumers
- [ ] Test in production-like environment
- [ ] Verify backward compatibility

## Validation Checklist

- [ ] API signatures match specification
- [ ] Return types correct
- [ ] Error formats preserved
- [ ] All integration points documented
- [ ] Usage examples tested
- [ ] Documentation complete
- [ ] Type hints present
- [ ] Docstrings complete

## Migration Guide

### For Existing Code

**Before**:
```python
# Old pattern
```

**After**:
```python
# New pattern using contract
```

### Breaking Changes

- None (backward compatible)

OR

- Change 1: Description and migration path
- Change 2: Description and migration path

## Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-13 | Initial specification | agent-name |

## References

- Related contracts: [contract-name.md](contract-name.md)
- Implementation: [path/to/implementation.py](../../path/to/implementation.py)
- Tests: [path/to/tests.py](../../path/to/tests.py)
```

---

## Contract Review Process

### Step 1: Draft Creation
Provider agent creates contract based on requirements

### Step 2: Self-Review
Provider validates:
- [ ] All required sections complete
- [ ] API signatures well-defined
- [ ] Error handling specified
- [ ] Examples work
- [ ] Integration points clear

### Step 3: Consumer Review
Consumer agents check:
- [ ] Interface meets their needs
- [ ] Examples are clear
- [ ] Error handling sufficient
- [ ] Migration path feasible

### Step 4: Publication
Once approved:
- Set status to "published"
- Freeze specification
- Implementation can begin

### Step 5: Validation
After implementation:
- Run tests against spec
- Verify contract compliance
- Set status to "validated"

---

## Best Practices

### DO:
✅ Define explicit return types
✅ Document all error conditions
✅ Provide working examples
✅ Specify performance characteristics
✅ Include migration guides
✅ Keep contracts focused and cohesive

### DON'T:
❌ Leave implementation details ambiguous
❌ Change published contracts without versioning
❌ Assume consumers understand implicit behavior
❌ Skip error handling documentation
❌ Forget edge cases
❌ Make breaking changes without migration path

---

## Troubleshooting

### Contract Not Working

**Problem**: Implementation doesn't match contract

**Solution**:
1. Compare implementation against spec line-by-line
2. Run validation tests
3. Check for version mismatches
4. Verify all dependencies met

### Contract Incomplete

**Problem**: Missing critical information

**Solution**:
1. Review template checklist
2. Add missing sections
3. Get consumer feedback
4. Update and republish

### Contract Conflicts

**Problem**: Multiple contracts define same interface

**Solution**:
1. Identify which is authoritative
2. Deprecate others
3. Provide migration path
4. Update all consumers

---

## Tools

### Validate Contract
```bash
#!/bin/bash
# validate_contract.sh

CONTRACT=$1

echo "Validating $CONTRACT..."

# Check all required sections present
required_sections="Overview|API Specification|Error Handling|Usage Examples|Validation Checklist"

for section in $(echo $required_sections | tr '|' ' '); do
  if ! grep -q "## $section" "$CONTRACT"; then
    echo "❌ Missing section: $section"
    exit 1
  fi
done

echo "✅ All required sections present"

# Check code blocks are valid Python
python -m py_compile <(sed -n '/```python/,/```/p' "$CONTRACT" | grep -v '```')

if [ $? -eq 0 ]; then
  echo "✅ Code examples are valid Python"
else
  echo "❌ Code examples have syntax errors"
  exit 1
fi

echo "✅ Contract validation passed"
```

### Extract Examples
```bash
#!/bin/bash
# extract_examples.sh

CONTRACT=$1

echo "Extracting examples from $CONTRACT..."

# Extract all Python code blocks
sed -n '/```python/,/```/p' "$CONTRACT" | grep -v '```' > examples.py

echo "Examples extracted to examples.py"
echo "Run: python examples.py"
```

---

## Summary

Integration contracts are the **foundation of zero-conflict parallel development**:

1. **Explicit Interfaces**: No ambiguity about what's expected
2. **Early Validation**: Catch mismatches before integration
3. **Clear Communication**: Providers and consumers aligned
4. **Reduced Rework**: Get it right the first time
5. **Audit Trail**: Document decisions and rationale

**All agents must publish contracts before implementation begins!**
