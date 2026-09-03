"""Domain errors for Signature Builder."""


class SignatureBuilderError(Exception):
    """Base error for recoverable application failures."""


class BrandConfigError(SignatureBuilderError):
    """Raised when brand.json is missing or invalid."""


class AssetError(SignatureBuilderError):
    """Raised when a required brand asset cannot be loaded."""


class TemplateError(SignatureBuilderError):
    """Raised when a signature template cannot be loaded or rendered."""
