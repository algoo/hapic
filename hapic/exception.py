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


class InputWorkflowException(WorkflowException):
    pass


class OutputWorkflowException(WorkflowException):
    pass


class InputValidationException(InputWorkflowException, ProcessException):
    pass


class OutputValidationException(InputWorkflowException, ProcessException):
    pass


class DocumentationException(HapicException):
    pass


class NoRoutesException(DocumentationException):
    pass


class RouteNotFound(DocumentationException):
    pass
