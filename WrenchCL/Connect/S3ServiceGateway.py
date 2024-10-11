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
import binascii
import io
import base64
import mimetypes
from pathlib import Path
from typing import Union, IO, Optional
from io import BytesIO

from botocore.config import Config
from botocore.exceptions import ClientError
from botocore.response import StreamingBody
import warnings

# Assuming these are your custom modules
from ..Decorators.Retryable import Retryable
from ..Decorators.SingletonClass import SingletonClass
from ..Tools import logger
from .AwsClientHub import AwsClientHub


@SingletonClass
class S3ServiceGateway:
    """
    Provides methods to interact with AWS S3, including uploading, downloading, moving, and deleting objects. Ensures
    that a single instance is used throughout the application via the Singleton pattern.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initializes the S3ServiceGateway by setting up the S3 client using the AwsClientHub.
        """
        client_manager = AwsClientHub()
        self.s3_client = client_manager.get_s3_client(config=config)
        logger.debug("S3ServiceGateway initialized with S3 client.")

    @staticmethod
    def _get_mime_extension(mime_type: str) -> str:
        """Get the file extension for a given MIME type."""
        return mimetypes.guess_extension(mime_type)

    def verify_and_correct_extension(self, object_key: str, mime_type: str) -> str:
        """Verify the extension of the object key and correct it if necessary."""
        correct_extension = self._get_mime_extension(mime_type)
        if not correct_extension:
            return object_key

        current_extension = Path(object_key).suffix
        if current_extension != correct_extension:
            logger.debug(f"Correcting file extension from {current_extension} to {correct_extension}")
            object_key = str(Path(object_key).with_suffix(correct_extension))
        return object_key

    @Retryable()
    def upload_file(self, file: Union[str, Path, bytes, BytesIO, StreamingBody], bucket_name: str, object_key: str,
            return_url: bool = False) -> Union[None, str]:
        """
        Uploads a file to S3. Handles file paths, bytes, file-like objects, and StreamingBody.

        :param file: The file path, bytes, file-like object, or StreamingBody to be uploaded.
        :type file: Union[str, Path, bytes, BytesIO, StreamingBody]
        :param bucket_name: The name of the S3 bucket.
        :type bucket_name: str
        :param object_key: The key of the object in the S3 bucket.
        :type object_key: str
        :param return_url: Whether to return the S3 URL of the uploaded file.
        :type return_url: bool
        :return: The S3 URL of the uploaded file if `return_url` is True, otherwise None.
        :rtype: Union[None, str]
        """
        if isinstance(file, (str, Path)) and Path(file).is_file():
            file_path = Path(file)
            if file_path.stat().st_size == 0:
                raise ValueError("The file is empty.")
            logger.debug(f"Uploading file from path: {file_path} to bucket: {bucket_name} as object: {object_key}")
            with open(file_path, 'rb') as f:
                self.s3_client.upload_fileobj(f, bucket_name, object_key)
        elif isinstance(file, bytes) or (isinstance(file, str) and not Path(file).is_file()):
            # Handle base64 encoded strings
            try:
                file_content = base64.b64decode(file) if isinstance(file, str) else file
            except binascii.Error:
                file_content = file.encode('utf-8') if isinstance(file, str) else file

            if len(file_content) == 0:
                raise ValueError("The byte content is empty.")

            file_obj = BytesIO(file_content)
            logger.debug(f"Uploading bytes object to bucket: {bucket_name} as object: {object_key}")
            self.s3_client.upload_fileobj(file_obj, bucket_name, object_key)
        elif hasattr(file, 'read') and callable(file.read):
            if file.seek(0, 2) == 0:  # Move to the end of the file and check the position
                raise ValueError("The file-like object is empty.")
            file.seek(0)  # Move back to the beginning of the file
            logger.debug(f"Uploading file-like object to bucket: {bucket_name} as object: {object_key}")
            self.s3_client.upload_fileobj(file, bucket_name, object_key)
        else:
            raise ValueError("The file parameter must be a file path, bytes, file-like object, or StreamingBody.")

        logger.debug(f"File uploaded to bucket: {bucket_name} as object: {object_key}")

        if return_url:
            s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"
            return s3_url

    @Retryable()
    def get_object(self, bucket_name: str, object_key: str) -> io.BytesIO:
        """
        Retrieves an object from S3 and returns its content as a file stream.

        :param bucket_name: The name of the S3 bucket.
        :type bucket_name: str
        :param object_key: The key of the object in the S3 bucket.
        :type object_key: str
        :returns: The content of the object as a BytesIO stream.
        :rtype: io.BytesIO
        """
        logger.debug(f"Attempting to retrieve object: {object_key} from bucket: {bucket_name}")
        obj = self.s3_client.get_object(Bucket=bucket_name, Key=object_key)
        file_stream = io.BytesIO(obj['Body'].read())
        logger.debug(f"Object retrieved: {object_key} from bucket: {bucket_name}")
        return file_stream

    @Retryable()
    def download_object(self, bucket_name: str, object_key: str, local_path: str) -> None:
        """
        Downloads an object from S3 to a local file.

        :param bucket_name: The name of the S3 bucket.
        :type bucket_name: str
        :param object_key: The key of the object in the S3 bucket.
        :type object_key: str
        :param local_path: The local path where the object will be saved.
        :type local_path: str
        """
        logger.debug(f"Downloading object: {object_key} from bucket: {bucket_name} to {local_path}")
        with open(local_path, 'wb') as f:
            self.s3_client.download_fileobj(bucket_name, object_key, f)
        logger.debug(f"Object downloaded: {object_key} to {local_path}")

    @Retryable()
    def get_object_headers(self, bucket_name: str, object_key: str) -> dict:
        """
        Retrieves the headers of an object in S3.

        :param bucket_name: The name of the S3 bucket.
        :type bucket_name: str
        :param object_key: The key of the object in the S3 bucket.
        :type object_key: str
        :returns: The headers of the object.
        :rtype: dict
        """
        logger.debug(f"Getting headers for object: {object_key} in bucket: {bucket_name}")
        obj = self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
        logger.debug(f"Headers retrieved for object: {object_key}")
        return obj

    @Retryable()
    def delete_object(self, bucket_name: str, object_key: str) -> None:
        """
        Deletes an object from S3.

        :param bucket_name: The name of the S3 bucket.
        :type bucket_name: str
        :param object_key: The key of the object in the S3 bucket.
        :type object_key: str
        """
        logger.debug(f"Deleting object: {object_key} from bucket: {bucket_name}")
        self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        logger.debug(f"Object deleted: {object_key} from bucket: {bucket_name}")

    @Retryable()
    def move_object(self, src_bucket_name: str, src_object_key: str, dst_bucket_name: str, dst_object_key: str) -> None:
        """
        Moves an object from one S3 bucket to another.

        :param src_bucket_name: The source S3 bucket name.
        :type src_bucket_name: str
        :param src_object_key: The key of the source object in the source S3 bucket.
        :type src_object_key: str
        :param dst_bucket_name: The destination S3 bucket name.
        :type dst_bucket_name: str
        :param dst_object_key: The key of the object in the destination S3 bucket.
        :type dst_object_key: str
        """
        logger.debug(f"Moving object: {src_object_key} from {src_bucket_name} to {dst_bucket_name}/{dst_object_key}")
        self.s3_client.copy_object(Bucket=dst_bucket_name, Key=dst_object_key,
                                   CopySource={'Bucket': src_bucket_name, 'Key': src_object_key})
        self.s3_client.delete_object(Bucket=src_bucket_name, Key=src_object_key)
        logger.debug(f"Object moved: {src_object_key} to {dst_bucket_name}/{dst_object_key}")

    @Retryable()
    def copy_object(self, src_bucket_name: str, src_object_key: str, dst_bucket_name: str, dst_object_key: str) -> None:
        """
        Copies an object from one S3 bucket to another.

        :param src_bucket_name: The source S3 bucket name.
        :type src_bucket_name: str
        :param src_object_key: The key of the source object in the source S3 bucket.
        :type src_object_key: str
        :param dst_bucket_name: The destination S3 bucket name.
        :type dst_bucket_name: str
        :param dst_object_key: The key of the object in the destination S3 bucket.
        :type dst_object_key: str
        """
        logger.debug(f"Copying object: {src_object_key} from {src_bucket_name} to {dst_bucket_name}/{dst_object_key}")
        self.s3_client.copy_object(Bucket=dst_bucket_name, Key=dst_object_key,
                                   CopySource={'Bucket': src_bucket_name, 'Key': src_object_key})
        logger.debug(f"Object copied: {src_object_key} to {dst_bucket_name}/{dst_object_key}")

    @Retryable()
    def check_object_existence(self, bucket_name: str, object_key: str) -> bool:
        """
        Checks if an object exists in an S3 bucket.

        :param bucket_name: The name of the S3 bucket.
        :type bucket_name: str
        :param object_key: The key of the object in the S3 bucket.
        :type object_key: str
        :returns: True if the object exists, False otherwise.
        :rtype: bool
        """
        logger.debug(f"Checking existence for object: {object_key} in bucket: {bucket_name}")
        try:
            self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
            logger.debug(f"Object exists: {object_key} in bucket: {bucket_name}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                logger.debug(f"Object does not exist: {object_key} in bucket: {bucket_name}")
                return False
            else:
                raise

    @Retryable()
    def list_objects(self, bucket_name: str, prefix: str = None) -> list:
        """
        Lists objects in an S3 bucket, optionally filtered by a prefix.

        :param bucket_name: The name of the S3 bucket.
        :type bucket_name: str
        :param prefix: The prefix to filter the objects.
        :type prefix: str, optional
        :returns: A list of object keys.
        :rtype: list
        """
        logger.debug(f"Listing objects in bucket: {bucket_name} with prefix: {prefix}")
        paginator = self.s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
        object_list = [item['Key'] for page in page_iterator for item in page.get('Contents', [])]
        logger.debug(f"Objects listed in bucket: {bucket_name} with prefix: {prefix}")
        return object_list

    @Retryable()
    def check_bucket_permissions(self, bucket_name: str) -> dict:
        """
        Checks the permissions of an S3 bucket.

        :param bucket_name: The name of the S3 bucket.
        :type bucket_name: str
        :returns: The access control list (ACL) of the bucket.
        :rtype: dict
        """
        logger.debug(f"Checking permissions for bucket: {bucket_name}")
        acl = self.s3_client.get_bucket_acl(Bucket=bucket_name)
        logger.debug(f"Permissions checked for bucket: {bucket_name}")
        return acl

    @Retryable()
    def list_buckets(self) -> list:
        """
        Lists all S3 buckets.

        :returns: A list of bucket names.
        :rtype: list
        """
        logger.debug("Listing all S3 buckets")
        response = self.s3_client.list_buckets()
        bucket_list = [bucket['Name'] for bucket in response.get('Buckets', [])]
        logger.debug("S3 buckets listed")
        return bucket_list

    @Retryable()
    def get_signed_url(self, bucket_name: str, object_key: str, expiration_seconds: int = 3600) -> str:
        """
        Generate a signed URL for an S3 object.

        :param bucket_name: Name of the S3 bucket
        :type bucket_name: str
        :param object_key: Key of the S3 object
        :type object_key: str
        :param expiration_seconds: Time in seconds for the presigned URL to remain valid
        :type expiration_seconds: int
        :return: Presigned URL as a string
        :rtype: str
        :raises: Exception if URL generation fails
        """
        logger.debug(f'Generating signed URL for bucket: {bucket_name}, key: {object_key}')
        try:
            url = self.s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=expiration_seconds)
            if url:
                logger.debug(f'Signed URL generated successfully: {url}')
                return url
            else:
                logger.error('Failed to generate signed URL')
                raise ValueError('Generated URL is invalid')
        except ClientError as e:
            logger.error(f'Error generating signed URL: {e}')
            raise ValueError('Failed to generate signed URL') from e

    # Aliases for backward compatibility with deprecation warnings
    def upload_fileobj(self, file_path: Union[str, IO[bytes]], bucket_name: str, object_key: str):
        """
        Uploads a file-like object to S3.

        This method is deprecated and will be removed in a future release.
        Use 'upload_file' instead.

        :param file_path: The file-like object or path to be uploaded.
        :type file_path: Union[str, IO[bytes]]
        :param bucket_name: The name of the S3 bucket.
        :type bucket_name: str
        :param object_key: The key of the object in the S3 bucket.
        :type object_key: str
        """
        warnings.warn(
            "The 'upload_fileobj' method is deprecated and will be removed in a future release. Use 'upload_file' instead.",
            DeprecationWarning)
        return self.upload_file(file=file_path, bucket_name=bucket_name, object_key=object_key)

    def upload_object(self, obj: Union[str, bytes, IO[bytes], StreamingBody], bucket_name: str, object_key: str):
        """
        Uploads an object to S3.

        This method is deprecated and will be removed in a future release.
        Use 'upload_file' instead.

        :param obj: The bytes of the object to be uploaded.
        :type obj: Union[str, bytes, IO[bytes], StreamingBody]
        :param bucket_name: The name of the S3 bucket.
        :type bucket_name: str
        :param object_key: The key of the object in the S3 bucket.
        :type object_key: str
        """
        warnings.warn(
            "The 'upload_object' method is deprecated and will be removed in a future release. Use 'upload_file' instead.",
            DeprecationWarning)
        return self.upload_file(file=obj, bucket_name=bucket_name, object_key=object_key)

    def rename_object(self, bucket_name: str, src_object_key: str, dst_object_key: str):
        """
        Renames an object within the same S3 bucket.

        This method is deprecated and will be removed in a future release.
        Use 'move_object' instead.

        :param bucket_name: The name of the S3 bucket.
        :type bucket_name: str
        :param src_object_key: The current key of the object.
        :type src_object_key: str
        :param dst_object_key: The new key of the object.
        :type dst_object_key: str
        """
        warnings.warn(
            "The 'rename_object' method is deprecated and will be removed in a future release. Use 'move_object' instead.",
            DeprecationWarning)
        return self.move_object(src_bucket_name=bucket_name, src_object_key=src_object_key, dst_bucket_name=bucket_name,
                                dst_object_key=dst_object_key)
