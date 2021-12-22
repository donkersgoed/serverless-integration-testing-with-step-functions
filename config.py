"""Config Module."""
# Standard library imports
# -

# Related third party imports
# -

# Local application/library specific imports
# -


class Config:  # pylint: disable=too-few-public-methods
    """Config class."""

    def __init__(self) -> None:
        """Initialize config class."""

        self._default_config = {}

    def base(self):
        """Define the base configuration."""
        __config = {}
        return {**__config, **self._default_config}
