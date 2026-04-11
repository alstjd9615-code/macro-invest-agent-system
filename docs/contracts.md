# Contract Definitions & Boundaries

## Domain Contracts

### Macro Domain

**MacroFeature**
```
Represents a single macroeconomic indicator observation.

Required Fields:
  - indicator_type: MacroIndicatorType (enum)
  - source: MacroSourceType (enum)
  - value: float (must be finite, within -1e10..1e10)
  - timestamp: datetime

Optional Fields:
  - frequency: DataFrequency (default: DAILY)
  - country: ISO 3166-1 alpha-2 code (e.g., "US", "GB")
  - region: Geographic region name
  - metadata: dict[str, str] (arbitrary key-value pairs)

Validation Rules:
  ✓ Value must be a finite number (no NaN, no infinity)
  ✓ Timestamp must be a valid datetime
  ✓ Country and region must match expected formats (future)
```

**MacroSnapshot**
```
Represents a collection of macro features at a point in time.

Required Fields:
  - features: list[MacroFeature] (must not be empty)
  - snapshot_time: datetime

Optional Fields:
  - version: int (default: 1)

Validation Rules:
  ✓ Must contain at least one feature
  ✓ snapshot_time must be a valid datetime

Methods:
  - get_feature_by_indicator(indicator_type) → MacroFeature | None
    Returns first feature matching the indicator type
```

**MacroIndicatorType** (Enum)
```
GDP, INFLATION, UNEMPLOYMENT, INTEREST_RATE, EXCHANGE_RATE,
STOCK_INDEX, BOND_YIELD, CREDIT_SPREAD, COMMODITY_PRICE, PMI
```

**MacroSourceType** (Enum)
```
FRED, WORLD_BANK, IMF, OECD, ECB, MARKET_DATA, CUSTOM
```

**DataFrequency** (Enum)
```
DAILY, WEEKLY, MONTHLY, QUARTERLY, ANNUAL
```

---

### Signal Domain

**SignalRule**
```
Represents a single condition within a signal definition.

Required Fields:
  - name: str (rule identifier, must be unique within signal)
  - description: str (human-readable explanation)
  - condition: str (expression, e.g., "gdp_growth > 2.0")

Optional Fields:
  - weight: float (default: 1.0, must be >= 0.0)

Validation Rules:
  ✓ Weight must be non-negative
  ✓ Name must be non-empty
  ✓ Condition must be non-empty
```

**SignalDefinition**
```
Defines an investment signal and its evaluation rules.

Required Fields:
  - signal_id: str (unique identifier)
  - name: str (human-readable signal name)
  - signal_type: SignalType (BUY, SELL, HOLD, NEUTRAL)
  - description: str (detailed explanation of signal logic)
  - rules: list[SignalRule] (must not be empty)

Optional Fields:
  - required_indicators: list[str] (indicator types needed)
  - version: int (default: 1)

Validation Rules:
  ✓ Must contain at least one rule
  ✓ signal_id must be unique per system
  ✓ All required_indicators must exist in MacroIndicatorType
```

**SignalOutput**
```
Result of evaluating a signal against macro data.

Required Fields:
  - signal_id: str (which signal was evaluated)
  - signal_type: SignalType (result type)
  - strength: SignalStrength (confidence level)
  - score: float (0.0-1.0, where 1.0 is full confidence)
  - triggered_at: datetime (when signal was generated)

Optional Fields:
  - trend: TrendDirection (default: NEUTRAL)
  - rationale: str (human-readable explanation)
  - rule_results: dict[str, bool] (which rules passed)

Validation Rules:
  ✓ Score must be between 0.0 and 1.0
  ✓ triggered_at must be a valid datetime
  ✓ signal_id must reference a valid signal
```

**SignalResult**
```
Complete result of signal engine execution.

Required Fields:
  - run_id: str (unique UUID for this evaluation)
  - timestamp: datetime (when evaluation occurred)
  - macro_snapshot: MacroSnapshot (data evaluated against)

Optional Fields:
  - signals: list[SignalOutput] (default: empty)
  - success: bool (default: True)
  - error_message: str (present if success is False)

Validation Rules:
  ✓ run_id must be unique and valid UUID format
  ✓ Must reference a valid MacroSnapshot
  ✓ If error_message is present, success must be False

Methods:
  - get_signals_by_type(signal_type) → list[SignalOutput]
  - get_buy_signals() → list[SignalOutput]
  - get_sell_signals() → list[SignalOutput]
  - strongest_signal() → SignalOutput | None
```

**SignalType** (Enum)
```
BUY, SELL, HOLD, NEUTRAL
```

**SignalStrength** (Enum)
```
VERY_WEAK, WEAK, MODERATE, STRONG, VERY_STRONG

Mapping from score:
  0.0-0.3  → VERY_WEAK
  0.3-0.5  → WEAK
  0.5-0.7  → MODERATE
  0.7-0.9  → STRONG
  0.9-1.0  → VERY_STRONG
```

**TrendDirection** (Enum)
```
UP, DOWN, NEUTRAL, UNKNOWN
```

---

## Service Contracts

### MacroServiceInterface

```python
async def fetch_features(
    indicator_types: list[str],
    country: str = "US"
) → list[MacroFeature]
```
**Purpose**: Fetch specific macro indicators for a country.  
**Raises**: 
- `ValueError` if indicator_types is empty
- `RuntimeError` if data fetch fails
**Future**: Will integrate with FRED, World Bank APIs

```python
async def get_snapshot(
    country: str = "US"
) → MacroSnapshot
```
**Purpose**: Get all available macro data at current time.  
**Raises**:
- `RuntimeError` if snapshot cannot be created
**Future**: Will implement caching and multi-country support

---

### SignalServiceInterface

```python
async def evaluate_signal(
    signal_def: SignalDefinition,
    snapshot: MacroSnapshot
) → dict[str, bool]
```
**Purpose**: Evaluate a single signal's rules.  
**Returns**: Dictionary mapping rule names to pass/fail.  
**Raises**:
- `ValueError` if signal is invalid
- `RuntimeError` if evaluation fails
**Current**: Placeholder returns all rules as True

```python
async def run_engine(
    signal_definitions: list[SignalDefinition],
    snapshot: MacroSnapshot
) → SignalResult
```
**Purpose**: Run engine against all signals.  
**Returns**: Complete SignalResult with all outputs.  
**Raises**:
- `ValueError` if inputs are invalid
- `RuntimeError` if engine fails
**Current**: Calls SignalEngine with placeholder rule evaluation

---

## MCP Contracts

### Base Schemas

**MCPRequest**
```
All requests inherit from this base.

Fields:
  - request_id: str (unique identifier for this request)
  - timestamp: datetime (request creation time)
```

**MCPResponse**
```
All responses inherit from this base.

Fields:
  - request_id: str (echo of request that triggered this)
  - timestamp: datetime (response creation time)
  - success: bool (whether operation succeeded)
  - error_message: str | None (if success is False)
```

---

### Macro Data Retrieval

**GetMacroFeaturesRequest**
```
Inherits from MCPRequest

Additional Fields:
  - indicator_types: list[str] (required)
  - country: str (default: "US")
```

**GetMacroFeaturesResponse**
```
Inherits from MCPResponse

Additional Fields:
  - features_count: int (number of features returned)
```

**GetMacroSnapshotRequest**
```
Inherits from MCPRequest

Additional Fields:
  - country: str (default: "US")
```

**GetMacroSnapshotResponse**
```
Inherits from MCPResponse

Additional Fields:
  - snapshot_timestamp: datetime (time of snapshot)
  - features_count: int (number of features in snapshot)
```

---

### Signal Engine Execution

**RunSignalEngineRequest**
```
Inherits from MCPRequest

Additional Fields:
  - signal_ids: list[str] (signal IDs to evaluate, required)
  - country: str (country for macro data, default: "US")
  - use_latest_snapshot: bool (fetch fresh data, default: True)
```

**RunSignalEngineResponse**
```
Inherits from MCPResponse

Additional Fields:
  - engine_run_id: str (unique ID for this execution)
  - signals_generated: int (total signal count)
  - buy_signals: int (count of BUY signals)
  - sell_signals: int (count of SELL signals)
  - hold_signals: int (count of HOLD signals)
  - execution_time_ms: float (time taken in milliseconds)
```

---

## Validation Rules Summary

### Domain Layer
- ✓ All models use Pydantic with strict validation
- ✓ Type hints enforced at runtime
- ✓ No None values where not explicitly Optional
- ✓ Enums restrict values to known set
- ✓ Numeric bounds checked (finite, in range)
- ✓ Collections non-empty where required

### Service Layer
- ✓ Interfaces define expected exceptions
- ✓ Async-first, no blocking operations
- ✓ Return types match domain contracts
- ✓ Input validation delegates to domain

### MCP Layer
- ✓ Requests validated at parse time (Pydantic)
- ✓ Responses include tracing (request_id)
- ✓ Error messages included on failures
- ✓ Timestamps used for ordering and auditing

---

## Extension Points

### Adding a New Indicator Type
1. Add to `MacroIndicatorType` enum
2. No other changes needed in existing code
3. Tests should cover new type

### Adding a New Signal
1. Create `SignalRule` instances
2. Create `SignalDefinition` with rules
3. Pass to `SignalService.run_engine()`
4. No code changes required

### Adding a New Data Source
1. Add to `MacroSourceType` enum
2. Implement data fetching in `MacroService` (future)
3. Return as `MacroFeature` objects
4. Transparent to signal layer

### Adding a New Service
1. Define interface in `services/interfaces.py`
2. Implement following existing patterns
3. Inject via dependency management (future)

---

## Out of Scope (This Version)

- 🚫 Authentication and authorization
- 🚫 Multi-tenancy
- 🚫 Audit logging and compliance
- 🚫 Real data source integration
- 🚫 Performance optimization
- 🚫 Horizontal scaling
- 🚫 Autonomous trading decisions
- 🚫 FastAPI route handlers

These are planned for future releases.
