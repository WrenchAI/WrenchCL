#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""Wrench internal API helpers for service-to-service communication."""

from ._slack import slack_post

__all__ = ["slack_post"]
