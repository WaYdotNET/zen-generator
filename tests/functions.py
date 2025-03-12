"""some docstring"""

from __future__ import annotations

import logging

from .models import FooBar, Mida4TaskEnvironmentChoices, TaskAttachment, UserTaxDeclarationInfo

logger = logging.getLogger("Fake")


def get_attachments_from_utd(
    utd_id: int | str | TaskAttachment, kinds: list[str], other: int | FooBar | None
) -> list[TaskAttachment]:
    """
    Descrizione metodo get_attachments_from_utd
    Args:
        utd_id (): id dichiarazione
        kinds (): elenco tipologie
        other (): altro task attachment

    Returns:
        Torno cose
    """
    ...


def empty() -> None: ...


def generate_sync_task(
    utd_info: UserTaxDeclarationInfo, sequence: int | None, skip_create_f24s: bool
) -> int | None: ...


def generate_iiacc_task(
    utd_info: UserTaxDeclarationInfo, fiscal_elements: list[object] | None
) -> int | str | TaskAttachment | None: ...


def generate_iva_sync_task(
    user_id: int,
    ref_year: int,
    environment: Mida4TaskEnvironmentChoices,
    custom_actions: object | None,
) -> None: ...
