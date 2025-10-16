# Integration Contracts

This directory contains detailed interface specifications that define how different agents' work integrates together. These contracts are written **before implementation** and serve as the source of truth for coordination.

## Contract Types

### 1. Interface Contracts
Define function signatures, method contracts, and class interfaces that multiple agents depend on.

### 2. Data Flow Contracts
Specify how data moves between components, including format, validation rules, and transformation requirements.

### 3. Configuration Contracts
Define shared configuration values, environment variables, and settings that multiple components use.

### 4. Quality Contracts
Establish performance requirements, reliability targets, and security standards that all implementations must meet.

## Contract Files

### Wave 1 Contracts

- **`security-api-contract.md`** - Security fixes must maintain existing API contracts
- **`test-infrastructure-contract.md`** - Test infrastructure requirements and pytest configuration

### Wave 2 Contracts

- **`docling-parser-refactor-contract.md`** - Strategy pattern interface for document parsers
- **`processor-refactor-contract.md`** - Handler pattern interface for embedding processors
- **`test-coverage-contract.md`** - Coverage requirements for new modules

### Wave 3 Contracts

- **`file-operations-contract.md`** - Shared file I/O utility interface
- **`validation-contract.md`** - Centralized validation utility interface
- **`accessibility-contract.md`** - WCAG 2.1 AA compliance requirements

### Wave 4 Contracts

- **`performance-optimization-contract.md`** - Performance improvement targets and constraints
- **`final-validation-contract.md`** - Comprehensive validation requirements

## Using Contracts

### For Implementing Agents (Providers)

1. **Read the Contract** before starting implementation
2. **Validate Compliance** using provided test cases
3. **Document Deviations** if contract cannot be met exactly
4. **Update Contract** if legitimate changes needed (requires orchestrator approval)

### For Consuming Agents

1. **Read the Contract** to understand what's provided
2. **Write Tests** against the contract interface
3. **Mock Implementation** for parallel development
4. **Validate Integration** when provider completes work

### For Orchestrator

1. **Write Contracts First** before agents start work
2. **Review Compliance** during wave synchronization gates
3. **Arbitrate Disputes** if contract interpretation differs
4. **Approve Changes** if contracts need updates

## Contract Template

Each contract file follows this structure:

```markdown
# {Component Name} Contract

## Provider Agent
{agent-name}

## Consumer Agents
- {agent-1}
- {agent-2}

## Public Interface

### Functions/Methods
\`\`\`python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    Description of what this does.

    Args:
        param1: Description
        param2: Description

    Returns:
        Description of return value

    Raises:
        ErrorType: When this error occurs
    """
    pass
\`\`\`

## Data Contracts

### Input Format
\`\`\`python
{
    "field1": "value",
    "field2": 123
}
\`\`\`

### Output Format
\`\`\`python
{
    "result": "value",
    "status": "success"
}
\`\`\`

## Quality Requirements

- **Performance:** < X ms response time
- **Reliability:** 99.9% success rate
- **Security:** Input validation required
- **Testing:** 80% code coverage minimum

## Validation Tests

\`\`\`python
def test_contract_compliance():
    """Test that implementation meets contract."""
    result = function_name("input", 42)
    assert result.status == "success"
    assert result.response_time < 100  # ms
\`\`\`

## Dependencies

- Package requirements
- Environment variables
- External services

## Backward Compatibility

- Breaking changes: {Yes/No}
- Migration path: {Description}
- Deprecation timeline: {Date}

## Integration Points

### With Component A
- {Description of integration}

### With Component B
- {Description of integration}

## Notes

Additional context, gotchas, or implementation guidance.
```

## Contract Evolution

Contracts may evolve as implementation reveals new requirements:

1. **Minor Changes** (no breaking changes) can be made by provider with notification
2. **Major Changes** (breaking changes) require orchestrator approval and wave re-planning
3. **All Changes** must be documented with rationale and migration path
4. **Version History** tracked at bottom of each contract file

## See Also

- `../orchestration-plan.md` - Overall execution plan
- `../agent-assignments.md` - Territorial ownership boundaries
- `../validation-strategy.md` - Testing and quality assurance approach
- `../coordination-protocol.md` - Communication and status management
