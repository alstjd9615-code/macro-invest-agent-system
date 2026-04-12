# Architecture Overview

## System Design

The macro investment agent platform is organized into modular layers that clearly separate concerns and establish contract boundaries.

```
┌─────────────────────────────────────────────────────────────────┐
│                      MCP Server & Handlers                       │
│      (Request/Response Schemas - Read-Only Interface)            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    Service Layer                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ MacroService         │ SignalService                      │   │
│  │ (Data fetching)      │ (Signal evaluation)                │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     Domain Layer                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Macro Domain          │ Signal Domain                    │   │
│  │ • MacroFeature        │ • SignalDefinition               │   │
│  │ • MacroSnapshot       │ • SignalRule                     │   │
│  │ • Enums               │ • SignalOutput                   │   │
│  │                       │ • SignalResult                   │   │
│  │                       │ • SignalEngine                   │   │
│  │                       │ • Rule Evaluation                │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

## Key Layers

### Domain Layer (`domain/`)
**Purpose**: Define the core business contracts and logic.

**Macro Subdomain** (`domain/macro/`):
- `enums.py`: MacroIndicatorType, MacroSourceType, DataFrequency
- `models.py`: MacroFeature (single observation), MacroSnapshot (collection of features)
- Validation: Ensures data consistency, finite values, non-empty collections

**Signal Subdomain** (`domain/signals/`):
- `enums.py`: SignalType (BUY/SELL/HOLD), SignalStrength, TrendDirection
- `models.py`: SignalRule, SignalDefinition, SignalOutput, SignalResult
- `engine.py`: Deterministic signal evaluation engine
- `rules.py`: Rule evaluation functions (placeholder-based)

**Characteristics**:
- Independent of external dependencies
- Fully typed with Pydantic validation
- Deterministic and stateless
- Contains business logic and contracts

### Service Layer (`services/`)
**Purpose**: Coordinate domain objects and provide implementation stubs.

**Interfaces** (`services/interfaces.py`):
- `MacroServiceInterface`: Contract for macro data retrieval
- `SignalServiceInterface`: Contract for signal evaluation

**Implementations**:
- `MacroService`: Fetches features, manages snapshots (placeholder)
- `SignalService`: Orchestrates engine, evaluates signals (skeleton)

**Characteristics**:
- Async-first design
- Interface-based, allowing multiple implementations
- Thin layer: orchestration, not business logic
- Future: add caching, audit logging, persistence

### MCP Layer (`mcp/schemas/`, `mcp/tools/`)
**Purpose**: Define request/response contracts and provide thin callable entrypoints for external systems (read-only interface).

**Base Schemas** (`mcp/schemas/common.py`):
- `MCPRequest`: Base for all requests (request_id, timestamp)
- `MCPResponse`: Base for all responses (request_id, success, error_message)

**Feature Schemas** (`mcp/schemas/get_macro_features.py`):
- `GetMacroFeaturesRequest`: Fetch specific indicators
- `GetMacroFeaturesResponse`: Return requested features
- `GetMacroSnapshotRequest`: Fetch all current indicators
- `GetMacroSnapshotResponse`: Return complete snapshot

**Engine Schemas** (`mcp/schemas/run_signal_engine.py`):
- `RunSignalEngineRequest`: Trigger signal evaluation
- `RunSignalEngineResponse`: Return generated signals with metadata

**Tool Handlers** (`mcp/tools/`):
- `handle_get_macro_features`: Resolves `GetMacroFeaturesRequest` → `MacroService.fetch_features()`
- `handle_get_macro_snapshot`: Resolves `GetMacroSnapshotRequest` → `MacroService.get_snapshot()`
- `handle_run_signal_engine`: Resolves `RunSignalEngineRequest` → registry lookup → `MacroService.get_snapshot()` → `SignalService.run_engine()`

**Signal Registry** (`domain/signals/registry.py`):
- `SignalRegistry`: In-memory mapping of signal_id → SignalDefinition
- `default_registry`: Pre-populated with built-in signal definitions

**Characteristics**:
- Immutable request/response objects
- Validation at boundaries
- Tracing via request_id
- Status and error reporting
- Tool handlers never raise — all errors become structured responses

## Data Flow

### Macro Data Retrieval Flow
```
MCP Request (GetMacroFeaturesRequest)
         ↓
Service Layer (MacroService.fetch_features)
         ↓
Domain Layer (MacroFeature model validation)
         ↓
MCP Response (GetMacroFeaturesResponse)
```

### Signal Evaluation Flow
```
MCP Request (RunSignalEngineRequest)
         ↓
Service Layer (SignalService.run_engine)
         ↓
Signal Engine (deterministic evaluation)
         ↓
Domain Layer (SignalOutput/SignalResult models)
         ↓
MCP Response (RunSignalEngineResponse)
```

## Design Principles

### 1. Determinism
- Signal engine produces identical outputs for identical inputs
- No randomness, external state, or I/O during evaluation
- Enables testing, auditing, and reproducibility

### 2. Typed Contracts
- All data structures use Pydantic models with full type hints
- Validation at model creation time
- Clear documentation via docstrings

### 3. Separation of Concerns
- **Domain**: Business logic and validation
- **Services**: Orchestration and coordination
- **MCP**: External interface and request/response binding

### 4. Interface-Based Design
- Services expose abstract interfaces (protocols)
- Enables testing with mocks and alternative implementations
- Facilitates dependency injection

### 5. Placeholder-First Approach
- Real implementations stubbed with deterministic defaults
- Prevents over-engineering before requirements are clear
- Tests verify structure and contracts, not implementation details

## Boundaries

### What Lives in Domain Layer
✅ Business rules and validation  
✅ Data models and enums  
✅ Deterministic algorithms  
✅ Type contracts  

### What Does NOT Live in Domain Layer
❌ External service calls  
❌ I/O operations (database, API)  
❌ Randomness or non-deterministic behavior  
❌ Framework dependencies  

### What Lives in Service Layer
✅ Coordination between domains  
✅ Orchestration of workflows  
✅ Implementation of interfaces  
✅ Future: caching, logging, persistence  

### What Lives in MCP Layer
✅ Request/response schemas  
✅ Tool handler functions (thin dispatch to service layer)  
✅ Input validation at the MCP boundary  
✅ Structured error responses  
✅ Tracing and error reporting  

### What Does NOT Live in MCP Layer
❌ Business logic  
❌ Data transformation  
❌ Complex validation (defer to domain)  
❌ State mutation or side effects  
❌ FastAPI routes or HTTP endpoints  

## Future Extensibility

### Adding New Signals
1. Create `SignalRule` instances with condition strings
2. Create `SignalDefinition` with rules
3. Evaluate via `SignalService.run_engine()`

### Adding New Data Sources
1. Extend `MacroSourceType` enum
2. Implement data fetch logic in `MacroService` (placeholder → real)
3. No changes needed in domain or MCP layers

### Adding New Services
1. Define interface in `services/interfaces.py`
2. Create implementation following existing patterns
3. Register in service layer initialization

## Testing Strategy

### Unit Tests
- **Domain tests**: Validation, model creation, business logic
- **Service tests**: Interface contracts, error handling
- **MCP tests**: Schema validation, request/response structure

### Test Coverage
- ✅ Normal paths (valid inputs, expected outputs)
- ✅ Error paths (invalid inputs, validation failures)
- ✅ Edge cases (empty collections, boundary values)
- ✅ Schema compatibility (serialization/deserialization)

### Mock Approach
- Services use placeholder implementations
- Tests verify contracts, not external dependencies
- Engine uses deterministic rule evaluation

## Development Workflow

1. **Schema First**: Define MCP request/response contracts
2. **Domain Model Second**: Create Pydantic models with validation
3. **Service Third**: Implement service interfaces
4. **Tests Last**: Write comprehensive unit tests
5. **Documentation**: Keep README and architecture updated

## Out of Scope (v0.1.0)

❌ FastAPI route implementation  
❌ Database storage and migrations  
❌ Real data integration (FRED, World Bank, etc.)  
❌ Autonomous trading decisions  
❌ Performance optimization  
❌ Deployment and containerization  
❌ Multi-tenancy  
❌ Audit logging and compliance  

These will be added in future phases as the platform matures.
