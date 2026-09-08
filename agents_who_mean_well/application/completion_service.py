"""Use case: answer a caller's prompt with a language model."""

from __future__ import annotations

import time
from logging import Logger

from agents_who_mean_well.application.ports.completion_port import CompletionPort
from agents_who_mean_well.application.ports.current_user_port import CurrentUserPort
from agents_who_mean_well.application.ports.metrics_port import MetricsPort
from agents_who_mean_well.constants.static_messages import StaticMessages
from agents_who_mean_well.domain.conversation.completion_result import CompletionResult
from agents_who_mean_well.domain.conversation.message import Message
from agents_who_mean_well.domain.enums.message_role import MessageRole
from agents_who_mean_well.domain.exceptions.validation_exception import ValidationException


class CompletionService:
    """Turns a caller's prompt into an answer from the language model."""

    def __init__(
        self,
        *,
        logger: Logger,
        completion: CompletionPort,
        current_user: CurrentUserPort,
        metrics: MetricsPort,
        system_prompt: str,
    ) -> None:
        self._logger = logger
        self._completion = completion
        self._current_user = current_user
        self._metrics = metrics
        self._system_prompt = system_prompt

    async def complete(self, *, prompt: str) -> CompletionResult:
        """Answer ``prompt`` on behalf of the current caller."""
        if not prompt.strip():
            raise ValidationException(
                detail=StaticMessages.EMPTY_PROMPT, field="Prompt"
            )

        user = self._current_user.get_current_user()
        self._metrics.increment(name="completion.requested")
        started = time.perf_counter()

        answer = await self._completion.complete(
            messages=[Message(role=MessageRole.USER, content=prompt)],
            system=self._system_prompt,
        )

        self._metrics.record_duration(
            name="completion.duration", seconds=time.perf_counter() - started
        )
        self._logger.info("Completed a prompt for user %s.", user.user_id)
        return CompletionResult(answer=answer, requested_by=user.user_id)
