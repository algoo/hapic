# -*- coding: utf-8 -*-


class HapicException(Exception):
    pass


class ConfigurationException(HapicException):
    pass


class WorkflowException(HapicException):
    pass


class DecorationException(HapicException):
    pass


class AlreadyDecoratedException(DecorationException):
    pass


class ProcessException(HapicException):
    pass


class ValidationException(ProcessException):
    pass


class InputWorkflowException(WorkflowException):
    pass


class OutputWorkflowException(WorkflowException):
    pass


class InputValidationException(InputWorkflowException, ValidationException):
    pass


class OutputValidationException(OutputWorkflowException, ValidationException):
    pass


class DocumentationException(HapicException):
    pass


class NoRoutesException(DocumentationException):
    pass


class RouteNotFound(DocumentationException):
    pass


class NotLowercaseCaseException(HapicException):
    """Raised when a given dict key must be in lowercase but it is not"""
