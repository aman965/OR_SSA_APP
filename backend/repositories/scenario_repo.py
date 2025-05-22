"""Repository adapter for the :class:`~backend.core.models.Scenario` model.

This tiny layer abstracts away the underlying Django ORM, giving the rest of
our code-base a stable, test-friendly surface that can later be swapped out or
augmented without touching business logic or UI code.
"""

from __future__ import annotations

from typing import Final

from django.db import transaction

from backend.core.models import Scenario

__all__: Final = ["ScenarioRepo"]


class ScenarioRepo:  # noqa: D101 – Simple CRUD wrapper, docstring in module-level.
    """CRUD operations for `Scenario` using Django ORM only."""

    # ---------------------------------------------------------------------
    # Read
    # ---------------------------------------------------------------------

    @staticmethod
    def get(pk: str) -> Scenario:  # noqa: D401 – simple accessor
        """Return the Scenario identified by *pk*.

        The method delegates to ``Scenario.objects.get`` and therefore raises
        ``Scenario.DoesNotExist`` if the row is missing. Keeping Django's own
        exception allows callers to decide how they want to handle it.
        """

        return Scenario.objects.get(pk=pk)

    # ---------------------------------------------------------------------
    # Write helpers
    # ---------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def save(obj: Scenario) -> None:  # noqa: D401 – action method
        """Persist *obj* to the database inside an atomic transaction."""

        obj.save()

    # ------------------------------------------------------------------
    # Domain-specific helpers
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def add_constraint_prompt(pk: str, prompt: str) -> None:  # noqa: D401
        """Update *gpt_prompt* for the scenario with id *pk* and save.

        A row-level lock (``select_for_update``) prevents concurrent updates in
        a multi-worker environment.
        """

        scenario: Scenario = Scenario.objects.select_for_update().get(pk=pk)
        scenario.gpt_prompt = prompt
        scenario.save() 