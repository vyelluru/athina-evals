# Guardrails Gibberish Evaluator
# https://hub.guardrailsai.com/validator/guardrails/gibberish_text

from typing import List, Optional
import time
from athina.interfaces.result import EvalResult, EvalResultMetric
from athina.helpers.logger import logger
from ...base_evaluator import BaseEvaluator
from guardrails.hub import GibberishText as GuardrailsGibberishText
from guardrails import Guard
from athina.metrics.metric_type import MetricType


# Passes when the text is sensible, fails when the text is gibberish.
class NotGibberishText(BaseEvaluator):
    _validation_method: str
    _threshold: float
    
    def __init__(
        self,
        validation_method: str = "sentence",
        threshold: float = 0.75,
    ):
        self._validation_method = validation_method
        self._threshold = threshold
        # Initialize Validator
        self.validator = GuardrailsGibberishText(
            threshold=self._threshold,
            validation_method=self._validation_method,
            on_fail="noop",
        )

    @property
    def name(self) -> str:
        return "NotGibberishText"

    @property
    def display_name(self) -> str:
        return "Not Gibberish Text"

    @property
    def metric_ids(self) -> List[str]:
        return [MetricType.PASSED.value]

    @property
    def required_args(self) -> List[str]:
        return ["response"]  # TODO: allow running this on user_query OR response

    @property
    def examples(self):
        pass

    def is_failure(self, result: bool) -> bool:
        return not(bool(result))

    def _evaluate(self, **kwargs) -> EvalResult:
        """
        Run the Guardrails evaluator.
        """
        start_time = time.time()
        self.validate_args(**kwargs)
        metrics = []
        try:
            text = kwargs["response"]
            # Setup Guard
            guard = Guard.from_string(validators=[self.validator])
            # Pass LLM output through guard
            guard_result = guard.parse(text)
            grade_reason = "Text is sensible" if guard_result.validation_passed else "Text is gibberish"
            # Boolean evaluator
            metrics.append(
                EvalResultMetric(
                    id=MetricType.PASSED.value,
                    value=guard_result.validation_passed,
                )
            )
        except Exception as e:
            logger.error(f"Error occurred during eval: {e}")
            raise e

        end_time = time.time()
        eval_runtime_ms = int((end_time - start_time) * 1000)
        llm_eval_result = EvalResult(
            name=self.name,
            display_name=self.display_name,
            data=kwargs,
            failure=self.is_failure(guard_result.validation_passed),
            reason=grade_reason,
            runtime=eval_runtime_ms,
            model=None,
            metrics=metrics,
        )
        return {k: v for k, v in llm_eval_result.items() if v is not None}