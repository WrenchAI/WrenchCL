#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Literal

from typing_extensions import TYPE_CHECKING

from Connect import AwsClientHub
from Decorators import SingletonClass
from ..Types.TTLSet import TTLSet
from .. import logger

if TYPE_CHECKING:
    from mypy_boto3_rds import RDSClient


# ---------------------------------------------------------------------------
# Dataclass for an event
# ---------------------------------------------------------------------------
@dataclass
class ProcessingEvent:
    """
    Represents a single processing event stored in the `datastore.processing_events` table.

    This model defines the schema and lifecycle of a tracked job, including
    metadata, timestamps, and row counts. It provides methods for validation,
    status transitions, and completion tracking.

    Attributes:
        processing_id (str): Unique identifier for the processing event.
        service_name (str): Logical service identifier (e.g. 'ai_pipeline').
        processor_name (str): Component or processor performing the work.
        reference (str): External reference (e.g. run_id, s3_key, etc.).
        event (dict): Arbitrary input event payload stored as JSONB.
        status (Literal): Current job status ('in-progress', 'success', 'failure').
        status_note (Optional[str]): Optional human-readable note or error message.
        input_rows (Optional[int]): Number of input rows processed.
        output_rows (Optional[int]): Number of output rows produced.
        started_at (datetime): UTC timestamp when the event started.
        ended_at (Optional[datetime]): UTC timestamp when the event finished.
    """

    processing_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str = ""
    processor_name: str = ""
    reference: str = ""
    event: dict = field(default_factory=dict)
    status: Literal["in-progress", "success", "failure"] = "in-progress"
    status_note: Optional[str] = None
    input_rows: Optional[int] = None
    output_rows: Optional[int] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None

    _required_fields = [
        "processing_id",
        "service_name",
        "processor_name",
        "reference",
        "event",
        "status",
        "started_at",
    ]

    # -----------------------------------------------------------------------
    # Lifecycle management
    # -----------------------------------------------------------------------
    def finish_job(
        self,
        status: Literal["success", "failure"],
        status_note: Optional[str] = None,
        output_rows: Optional[int] = None,
    ):
        """
        Mark the job as finished, updating timestamps and optional row counts.

        Args:
            status (Literal): Completion status ('success' or 'failure').
            status_note (Optional[str]): Optional status message or error detail.
            output_rows (Optional[int]): Optional number of output rows produced.
        """
        self.status = status
        self.status_note = status_note
        self.output_rows = output_rows
        self.ended_at = datetime.now(timezone.utc)

    def check_init(self):
        """
        Validate that all required fields are initialized and the status is valid.

        Raises:
            ValueError: If a required field is missing or invalid.
        """
        for field in self._required_fields:
            if getattr(self, field) in (None, ""):
                raise ValueError(f"Missing required field: {field}")
        self.check_status()

    def check_status(self):
        """
        Validate that the job status is one of the supported literals.

        Raises:
            ValueError: If the status is not in ['in-progress', 'success', 'failure'].
        """
        if self.status not in ["in-progress", "success", "failure"]:
            raise ValueError(f"Invalid status: {self.status}")

    def is_finished(self) -> bool:
        """
        Returns True if the event is in a terminal state (success or failure).
        """
        return self.status in ["success", "failure"]

    def has_failed(self) -> bool:
        """
        Returns True if the event has failed.
        """
        return self.status == "failure"


# ---------------------------------------------------------------------------
# Singleton Tracker
# ---------------------------------------------------------------------------
@SingletonClass
class ProcessingTracker:
    """
    Thread-safe singleton tracker that manages `processing_events` in Postgres.

    This class acts as the in-memory coordinator for all running jobs within a
    service/processor context. It records new jobs, updates their status, and
    retrieves information from the backing Postgres table.

    Key features:
        - Thread-safe access using RLock
        - TTL-based cleanup for finished/failed jobs
        - Python-side timestamps (UTC)
        - Full lifecycle tracking: start, finish, retrieve

    Attributes:
        _sql_client (Optional[RDSClient]): Lazily-initialized RDS client.
        _service_name (Optional[str]): Logical service identifier.
        _processor_name (Optional[str]): Logical processor or component.
        _lock (threading.RLock): Lock ensuring thread-safe updates.
        _running_job_ids (dict[str, ProcessingEvent]): Active in-memory jobs.
        _finished_job_ids (TTLSet): Recently finished job IDs with TTL expiry.
        _failed_job_ids (TTLSet): Recently failed job IDs with TTL expiry.
    """

    _sql_client: Optional["RDSClient"] = None
    _service_name: Optional[str] = None
    _processor_name: Optional[str] = None

    _lock = threading.RLock()

    _running_job_ids: dict[str, ProcessingEvent] = {}
    _finished_job_ids = TTLSet(ttl=600)
    _failed_job_ids = TTLSet(ttl=600)

    def __init__(self, service_name: str, processor_name: str, sql_client: Optional["RDSClient"] = None):
        """
        Initialize a ProcessingTracker instance for a given service/processor.

        Args:
            service_name (str): Logical service identifier (e.g. 'ai_pipeline').
            processor_name (str): Logical processor name (e.g. 'embedding_batch').
            sql_client (Optional[RDSClient]): Optional custom RDS connection.
        """
        self._sql_client = sql_client
        self._processor_name = processor_name
        self._service_name = service_name

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------
    @property
    def sql_client(self):
        """
        Lazily instantiate and return the RDS client.

        Returns:
            RDSClient: Active RDS client connection.
        """
        if self._sql_client is None:
            client_manager = AwsClientHub()
            self._sql_client = client_manager.db
        return self._sql_client

    @property
    def service_name(self) -> str:
        """
        Return the current service name, falling back to environment variable.

        Raises:
            ValueError: If no service name is set or environment variable missing.
        """
        if self._service_name is None:
            self._service_name = os.getenv("SERVICE_NAME")
        if self._service_name is None:
            raise ValueError("No service name set (missing env: SERVICE_NAME)")
        return self._service_name

    @service_name.setter
    def service_name(self, value: str):
        """Set the logical service name."""
        self._service_name = value

    @property
    def processor_name(self) -> str:
        """Return the processor name."""
        if self._processor_name is None:
            raise ValueError("No processor name set")
        return self._processor_name

    @processor_name.setter
    def processor_name(self, value: str):
        """Set the logical processor name."""
        self._processor_name = value

    # -----------------------------------------------------------------------
    # Event lifecycle
    # -----------------------------------------------------------------------
    def start_event(self, reference: str, event: dict, input_rows: Optional[int] = None) -> Optional[str]:
        """
        Start a new processing event and insert it into Postgres.

        Args:
            reference (str): Unique external reference (e.g. run_id or s3_key).
            event (dict): JSON-compatible input payload.
            input_rows (Optional[int]): Optional count of input rows.

        Returns:
            Optional[str]: Processing ID if successfully created, else None.
        """
        evt = ProcessingEvent(
            service_name=self.service_name,
            processor_name=self.processor_name,
            reference=reference,
            event=event,
            input_rows=input_rows,
        )
        evt.check_init()

        with self._lock:
            if self._store_initial_event(evt):
                self._running_job_ids[evt.processing_id] = evt
                return evt.processing_id
        return None

    def _store_initial_event(self, evt: ProcessingEvent) -> bool:
        """
        Persist a new processing event into Postgres using Python timestamps.

        Args:
            evt (ProcessingEvent): Event to be inserted.

        Returns:
            bool: True if successful, False otherwise.
        """
        query = """
            INSERT INTO datastore.processing_events 
                (processing_id, service_name, processor_name, reference, event, input_rows, started_at)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s)
            ON CONFLICT (service_name, processor_name, reference)
                WHERE status = 'in-progress'
            DO UPDATE SET started_at = EXCLUDED.started_at
        """
        params = (
            evt.processing_id,
            evt.service_name,
            evt.processor_name,
            evt.reference,
            evt.event,
            evt.input_rows,
            evt.started_at,
        )

        try:
            with self.sql_client.cursor() as cursor:
                cursor.execute(query, params)
                self.sql_client.commit()
            return True
        except Exception as e:
            logger._internal.log_internal(f"[ProcessingTracker] Error storing initial event: {e}")
            return False

    def end_event(
        self,
        processing_id: str,
        success: bool = True,
        status_note: Optional[str] = None,
        output_rows: Optional[int] = None,
    ) -> bool:
        """
        Mark a processing job as complete (success or failure) and persist its status.

        Args:
            processing_id (str): UUID of the processing event.
            success (bool, optional): Whether the job succeeded. Defaults to True.
            status_note (Optional[str], optional): Optional completion message.
            output_rows (Optional[int], optional): Optional output row count.

        Returns:
            bool: True if persisted successfully, False otherwise.
        """
        with self._lock:
            evt = self._running_job_ids.pop(processing_id, None)

        if not evt:
            logger.error(f"[ProcessingTracker] Invalid or unknown processing ID: {processing_id}")
            return False

        status = "success" if success else "failure"
        evt.finish_job(status, status_note, output_rows)

        ok = self._store_status_update(evt)
        if ok:
            if success:
                self._finished_job_ids.add(evt.processing_id)
            else:
                self._failed_job_ids.add(evt.processing_id)
        else:
            logger._internal.log_internal(f"[ProcessingTracker] Failed to persist end_event for {processing_id}")
        return ok

    def _store_status_update(self, evt: ProcessingEvent) -> bool:
        """
        Update an existing processing record with completion metadata.

        Args:
            evt (ProcessingEvent): Event containing updated status info.

        Returns:
            bool: True if successful, False otherwise.
        """
        query = """
            UPDATE datastore.processing_events
            SET status = %s,
                status_note = %s,
                output_rows = %s,
                ended_at = %s
            WHERE processing_id = %s
        """
        params = (evt.status, evt.status_note, evt.output_rows, evt.ended_at, evt.processing_id)

        try:
            with self.sql_client.cursor() as cursor:
                cursor.execute(query, params)
                self.sql_client.commit()
            return True
        except Exception as e:
            logger._internal.log_internal(f"[ProcessingTracker] Error storing status update: {e}")
            return False

    # -----------------------------------------------------------------------
    # Retrieval helpers
    # -----------------------------------------------------------------------
    def get_processing_id(self, reference: str) -> Optional[str]:
        """
        Retrieve a running job's processing_id from memory by reference.

        Args:
            reference (str): External reference tied to the job.

        Returns:
            Optional[str]: Processing ID if active, else None.
        """
        with self._lock:
            for evt in self._running_job_ids.values():
                if evt.reference == reference:
                    return evt.processing_id
        return None

    def get_event(self, id_value: str, id_type: Literal["processing_id", "reference"] = "processing_id"):
        """
        Retrieve an event object by ID or reference.

        Args:
            id_value (str): The identifier (processing_id or reference).
            id_type (Literal): Type of identifier ('processing_id' or 'reference').

        Returns:
            Optional[ProcessingEvent]: Matching ProcessingEvent if found.
        """
        if id_type == "processing_id":
            return self._get_event_by_processing_id(id_value)
        elif id_type == "reference":
            return self._get_event_by_reference(id_value)
        else:
            raise ValueError(f"Invalid id_type: {id_type}")

    def _get_event_by_processing_id(self, processing_id: str) -> Optional[ProcessingEvent]:
        """
        Retrieve an event by processing_id, searching in-memory first.

        Args:
            processing_id (str): UUID of the processing event.

        Returns:
            Optional[ProcessingEvent]: Found event, or None if not active.
        """
        with self._lock:
            evt = self._running_job_ids.get(processing_id)
        if evt:
            return evt

        if processing_id in self._finished_job_ids:
            logger._internal.log_internal(f"[ProcessingTracker] Processing ID {processing_id} is finished")
        elif processing_id in self._failed_job_ids:
            logger._internal.log_internal(f"[ProcessingTracker] Processing ID {processing_id} has failed")
        else:
            logger.error(f"[ProcessingTracker] Cannot find processing ID: {processing_id}")
        return None

    def _get_event_by_reference(self, reference: str) -> Optional[ProcessingEvent]:
        """
        Retrieve an event object using its external reference.

        Args:
            reference (str): External reference to the job.

        Returns:
            Optional[ProcessingEvent]: Found event, or None if missing.
        """
        pid = self.get_processing_id(reference)
        if pid:
            return self._get_event_by_processing_id(pid)

        pid = self._get_from_db_by_reference(reference)
        if pid:
            return self._get_from_db_by_id(pid)

        logger.error(f"[ProcessingTracker] Cannot find processing ID for reference {reference}")
        return None

    def _get_from_db_by_id(self, processing_id: str) -> Optional[ProcessingEvent]:
        """
        Fetch a ProcessingEvent directly from Postgres by its ID.

        Args:
            processing_id (str): UUID of the processing event.

        Returns:
            Optional[ProcessingEvent]: Reconstructed ProcessingEvent object, or None.
        """
        query = """
            SELECT processing_id, service_name, processor_name, reference, event, status, status_note,
                   input_rows, output_rows, started_at, ended_at
            FROM datastore.processing_events
            WHERE processing_id = %s
        """
        try:
            with self.sql_client.cursor() as cursor:
                cursor.execute(query, (processing_id,))
                result = cursor.fetchone()
            if not result:
                logger._internal.log_internal(f"[ProcessingTracker] No processing event found for ID {processing_id}")
                return None
            return ProcessingEvent(*result)
        except Exception as e:
            logger._internal.log_internal(f"[ProcessingTracker] Error fetching event by ID: {e}")
            return None

    def _get_from_db_by_reference(self, reference: str) -> Optional[str]:
        """
        Fetch the latest processing_id from Postgres using a reference.

        Args:
            reference (str): External reference to the processing event.

        Returns:
            Optional[str]: The corresponding processing_id if found.
        """
        query = """
            SELECT processing_id 
            FROM datastore.processing_events 
            WHERE service_name = %s
              AND processor_name = %s
              AND reference = %s
            ORDER BY started_at DESC
            LIMIT 1
        """
        params = (self.service_name, self.processor_name, reference)
        try:
            with self.sql_client.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
            if result:
                return result[0]
            logger._internal.log_internal(f"[ProcessingTracker] No processing ID found for reference {reference}")
            return None
        except Exception as e:
            logger._internal.log_internal(f"[ProcessingTracker] Error fetching ID by reference: {e}")
            return None
