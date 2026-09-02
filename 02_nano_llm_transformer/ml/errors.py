"""Typed failures for artifact validation and inference support."""

class ArtifactError(Exception):
    code = "artifact_error"
    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class ArtifactMissing(ArtifactError):
    code = "artifact_missing"
    status_code = 503

class ArtifactInvalid(ArtifactError):
    code = "artifact_invalid"
    status_code = 500

class ArtifactMismatch(ArtifactError):
    code = "artifact_mismatch"
    status_code = 409

class BackendUnsupported(ArtifactError):
    code = "backend_unsupported"
    status_code = 501
