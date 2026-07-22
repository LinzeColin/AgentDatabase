"""Independent execution, input, calculation, and generation status planes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class StatusPlaneError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


class ExecutionStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    NEEDS_USER_INPUT = "NEEDS_USER_INPUT"
    EXPECTED_BLOCKED = "EXPECTED_BLOCKED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class InputReadinessStatus(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    SUFFICIENT = "SUFFICIENT"
    SUFFICIENT_WITH_DOCUMENTED_SCOPE = "SUFFICIENT_WITH_DOCUMENTED_SCOPE"
    NEEDS_SUPPLEMENT = "NEEDS_SUPPLEMENT"
    NEEDS_EXPLICIT_HANDLING = "NEEDS_EXPLICIT_HANDLING"
    BLOCKED_NON_WAIVABLE = "BLOCKED_NON_WAIVABLE"


class CalculationStatus(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    VALIDATED = "VALIDATED"
    BLOCKED_SOURCE = "BLOCKED_SOURCE"
    BLOCKED_SCHEMA = "BLOCKED_SCHEMA"
    BLOCKED_IDENTITY = "BLOCKED_IDENTITY"
    BLOCKED_RELATIONSHIP = "BLOCKED_RELATIONSHIP"
    BLOCKED_FORMULA = "BLOCKED_FORMULA"
    BLOCKED_RECONCILIATION = "BLOCKED_RECONCILIATION"
    BLOCKED_SECURITY = "BLOCKED_SECURITY"
    BLOCKED_PERIOD = "BLOCKED_PERIOD"
    ERROR = "ERROR"


class GenerationStatus(str, Enum):
    NOT_GENERATED = "NOT_GENERATED"
    FINAL_GENERATED = "FINAL_GENERATED"
    BLOCKED_DIAGNOSTICS_GENERATED = "BLOCKED_DIAGNOSTICS_GENERATED"
    FAILED = "FAILED"
    SUPERSEDED = "SUPERSEDED"


class ReplayFidelityStatus(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    EXACT = "EXACT"
    BLOCKED_HASH = "BLOCKED_HASH"
    BLOCKED_LINE_DELTA = "BLOCKED_LINE_DELTA"


class SourceQualityStatus(str, Enum):
    CONSISTENT = "CONSISTENT"
    SOURCE_ARITHMETIC_DIFFERENCE = "SOURCE_ARITHMETIC_DIFFERENCE"
    UNKNOWN = "UNKNOWN"


SUFFICIENT_INPUT_STATUSES = frozenset(
    {
        InputReadinessStatus.SUFFICIENT,
        InputReadinessStatus.SUFFICIENT_WITH_DOCUMENTED_SCOPE,
    }
)


@dataclass(frozen=True)
class RunStatusPlanes:
    execution_status: ExecutionStatus
    input_readiness_status: InputReadinessStatus
    calculation_status: CalculationStatus
    generation_status: GenerationStatus

    def validate(self) -> None:
        if not isinstance(self.execution_status, ExecutionStatus):
            raise StatusPlaneError("EXECUTION_STATUS_INVALID", "execution status is not registered")
        if not isinstance(self.input_readiness_status, InputReadinessStatus):
            raise StatusPlaneError("INPUT_STATUS_INVALID", "input readiness status is not registered")
        if not isinstance(self.calculation_status, CalculationStatus):
            raise StatusPlaneError("CALCULATION_STATUS_INVALID", "calculation status is not registered")
        if not isinstance(self.generation_status, GenerationStatus):
            raise StatusPlaneError("GENERATION_STATUS_INVALID", "generation status is not registered")

        if self.calculation_status == CalculationStatus.VALIDATED and self.input_readiness_status not in SUFFICIENT_INPUT_STATUSES:
            raise StatusPlaneError(
                "VALIDATED_WITH_INSUFFICIENT_INPUT",
                "calculation cannot validate before input readiness is sufficient",
            )
        if self.generation_status == GenerationStatus.FINAL_GENERATED:
            expected = (
                self.execution_status == ExecutionStatus.SUCCEEDED
                and self.input_readiness_status in SUFFICIENT_INPUT_STATUSES
                and self.calculation_status == CalculationStatus.VALIDATED
            )
            if not expected:
                raise StatusPlaneError(
                    "FINAL_STATUS_COMBINATION_INVALID",
                    "final generation requires succeeded execution, sufficient input, and validated calculation",
                )
        if self.generation_status == GenerationStatus.BLOCKED_DIAGNOSTICS_GENERATED:
            if self.execution_status not in {ExecutionStatus.NEEDS_USER_INPUT, ExecutionStatus.EXPECTED_BLOCKED}:
                raise StatusPlaneError(
                    "BLOCKED_STATUS_COMBINATION_INVALID",
                    "blocked diagnostics require an explicit user-input or expected-block execution state",
                )
            if self.calculation_status == CalculationStatus.VALIDATED:
                raise StatusPlaneError(
                    "BLOCKED_VALIDATED_CONFLICT",
                    "validated calculation cannot publish blocked diagnostics",
                )
        if self.generation_status == GenerationStatus.FAILED and self.execution_status != ExecutionStatus.FAILED:
            raise StatusPlaneError("FAILED_STATUS_COMBINATION_INVALID", "failed generation requires failed execution")

    def as_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "execution_status": self.execution_status.value,
            "input_readiness_status": self.input_readiness_status.value,
            "calculation_status": self.calculation_status.value,
            "generation_status": self.generation_status.value,
        }
