# -*- coding: utf-8 -*-


class HapicException(Exception):
    pass


class WorkflowException(HapicException):
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
