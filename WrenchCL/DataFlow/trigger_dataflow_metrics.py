#  Copyright (c) $YEAR$. Copyright (c) $YEAR$ Wrench.AI., Willem van der Schans, Jeong Kim
#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#  All works within the Software are owned by their respective creators and are distributed by Wrench.AI.
#
#  For inquiries, please contact Willem van der Schans through the official Wrench.AI channels or directly via GitHub at [Kydoimos97](https://github.com/Kydoimos97).
#


import time
import json
import uuid
from typing import Any, Dict
from ..Tools.WrenchLogger import logger

# Created by Jeong Kim
# Github: https://github.com/dalmad2
# Annotated by Willem van der Schans
# Github: https://github.com/Kydoimos97


def trigger_minimum_dataflow_metrics(
        event: Dict[str, Any],
        context: Any,
        lambda_client: Any,
        **kwargs: Any
) -> None:
    """
    Triggers the minimum dataflow metrics for a given job.

    This function triggers the minimum set of dataflow metrics, capturing essential
    information about the job execution.

    Args:
        event: Dict[str, Any]
            The event input received by the Lambda function.
        context: Any
            The context object provided by AWS Lambda.
        lambda_client: Any
            The AWS Lambda client object.
        kwargs: Any
            'job_type': str
                The type of job being executed (e.g., glue, batch, lambda, fargate).
            'job_name': str
                The name of the job being executed.
            'status_code': int
                The status code indicating the result of the job execution.
            'client_id': str, optional
                The client ID associated with the job.
            'action': str, optional
                The action performed by the job.
            'exception_msg': str, optional
                The exception message encountered during the job execution.
            Additional keyword arguments can be passed to provide more detailed metrics.
    """
    trigger_dataflow_metrics(event=event, context=context, lambda_client=lambda_client, **kwargs)


def trigger_dataflow_metrics(
        event: Dict[str, Any],
        context: Any,
        lambda_client: Any,
        **kwargs: Any
) -> None:
    """
    Triggers comprehensive dataflow metrics for a given job.

    This function captures comprehensive dataflow metrics related to a job execution,
    including details about resource usage, input/output counts, exception messages,
    and other relevant information.

    Args:
        event: Dict[str, Any]
            The event input received by the Lambda function.
        context: Any
            The context object provided by AWS Lambda.
        lambda_client: Any
            The AWS Lambda client object.
        kwargs: Any
            Additional keyword arguments can be passed to provide more detailed metrics:
            'job_type': str
                The type of job being executed (e.g., glue, batch, lambda, fargate).
            'job_name': str
                The name of the job being executed.
            'status_code': int
                The status code indicating the result of the job execution.
            'client_id': str, optional
                The client ID associated with the job.
            'action': str, optional
                The action performed by the job.
            'exception_msg': str, optional
                The exception message encountered during the job execution.
            'trigger': str
                The type of job being executed (e.g., glue, batch, lambda, fargate).
            'job_name': str
                The name of the job being executed.
            'state_machine_name': str
                The name of the state machine associated with the job.
            'state_name': str
                The name of the state under which the job is run.
            'workflow_id': str
                The ID of the workflow associated with the job.
            'job_type': str
                The type of job being executed (e.g., glue, batch, lambda, fargate).
            'job_run_state': str
                The state of the job execution (e.g., 'Success', 'Failure').
            'client_id': str
                The client ID associated with the job.
            'client_job_processing_datetime': str
                The processing datetime associated with the job.
            'job_run_started_on': str
                The start time of the job run.
            'duration': None
                The duration of the job execution.
            'bootstrap_duration': float
                The duration of the bootstrap process.
            'lifecycle_duration': None
                The duration of the job lifecycle.
            'max_memory_used': None
                The maximum memory used during the job execution.
            'rows_input': Any
                The number of input rows for the job.
            'rows_input_detail': Any
                Additional details about the input rows.
            'rows_output': Any
                The number of output rows for the job.
            'rows_output_detail': Any
                Additional details about the output rows.
            'uuids_input_detail': Any
                Details about the UUIDs of input rows.
            'uuids_output': Any
                Details about the UUIDs of output rows.
            'exception_msg': str
                The exception message encountered during the job execution.
            's3_output_path': str
                The S3 output path for the job.
            'rds_target_table': str
                The target RDS table for the job.
            'rds_input_table': str
                The input RDS table for the job.
            'job_id': str
                The ID of the job.
            'memory_limit_in_mb': int
                The memory limit in megabytes.
            'time_remaining_in_ms': int
                The time remaining in milliseconds.
            'source_id': str
                The ID of the source service.
            'log_stream_name': str
                The name of the log stream.
            'log_group_name': str
                The name of the log group.
            'state_entered_time': str
                The time when the state was entered.
            'status_code': int
                The status code indicating the result of the job execution.
            'message': str
                Additional message related to the job execution.
            'action': str
                The action performed by the job.
    """
    try:
        end_time = time.time()
        bootstrap_duration = end_time - kwargs.get('start_time', time.time())

        '''
        Input From Lambda
        '''
        memory_limit_in_mb = context.memory_limit_in_mb
        time_remaining_in_ms = context.get_remaining_time_in_millis()
        source_id = context.aws_request_id
        log_stream_name = context.log_stream_name
        log_group_name = context.log_group_name

        '''
        Input From Step Function
        '''
        job_run_started_on = event.get('execution_starttime')
        state_entered_time = event.get('state_enteredtime')
        state_name = event.get('state_name')
        workflow_id = event.get('statemachine_id')
        state_machine_name = event.get('state_machine_name')

        '''
        Input From User Input
        '''
        job_id = event.get('job_id')
        processing_datetime = event.get('processing_datetime')

        job_run_state = 'Success' if kwargs.get('status_code') == 200 else None

        performance_metrics = {
            'trigger': kwargs.get('job_type'),
            'job_name': kwargs.get('job_name'),
            'state_machine_name': state_machine_name,
            'state_name': state_name,
            'workflow_id': workflow_id,
            'job_type': kwargs.get('job_type'),
            'job_run_state': job_run_state,
            'client_id': str(kwargs.get('client_id')) if isinstance(kwargs.get('client_id'), uuid.UUID) else kwargs.get(
                'client_id'),
            'client_job_processing_datetime': processing_datetime,
            'job_run_started_on': job_run_started_on,
            'duration': None,
            'bootstrap_duration': bootstrap_duration,
            'lifecycle_duration': None,
            'max_memory_used': None,
            'rows_input': kwargs.get('rows_input'),
            'rows_input_detail': kwargs.get('rows_input_details'),
            'rows_output': kwargs.get('rows_output'),
            'rows_output_detail': kwargs.get('rows_output_details'),
            'uuids_input_detail': kwargs.get('uuids_input_details'),
            'uuids_output': kwargs.get('uuids_output'),
            'exception_msg': kwargs.get('exception_msg'),
            's3_output_path': kwargs.get('s3_output_path'),
            'rds_target_table': kwargs.get('rds_target_table'),
            'rds_input_table': kwargs.get('rds_input_table'),
            'job_id': job_id,
            'memory_limit_in_mb': memory_limit_in_mb,
            'time_remaining_in_ms': time_remaining_in_ms,
            'source_id': source_id,
            'log_stream_name': log_stream_name,
            'log_group_name': log_group_name,
            'state_entered_time': state_entered_time,
            'status_code': kwargs.get('status_code'),
            'message': kwargs.get('message'),
            'action': kwargs.get('action')
        }

        performance_lambda_response = lambda_client.invoke(
            FunctionName='dataflow-metrics',
            InvocationType='Event',
            Payload=json.dumps(performance_metrics, default=str)
        )
        logger.info('Invoked dataflow-metrics lambda')
    except Exception as e:
        logger.warning('Failed to invoke dataflow-metrics lambda')
        logger.warning(e)
