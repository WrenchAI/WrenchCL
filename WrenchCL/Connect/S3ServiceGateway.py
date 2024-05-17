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

import io
from botocore.exceptions import ClientError

from ..Decorators.Retryable import Retryable
from ..Decorators.SingletonClass import SingletonClass
from ..Tools.WrenchLogger import logger
from .AwsClientHub import AwsClientHub


@SingletonClass
class S3ServiceGateway:
    """
    Provides methods to interact with AWS S3, including uploading, downloading, moving, and deleting objects. Ensures
    that a single instance is used throughout the application via the Singleton pattern.

    Attributes:
        s3_client (boto3.client.S3): The S3 client for interacting with AWS S3.
    """

    def __init__(self):
        """
        Initializes the S3ServiceGateway by setting up the S3 client using the AwsClientHub.
        """
        client_manager = AwsClientHub()
        self.s3_client = client_manager.get_s3_client()
        logger.debug("S3Manager initialized with S3 client.")

    @Retryable()
    def get_object(self, bucket_name, object_key):
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
    def download_object(self, bucket_name, object_key, local_path):
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
    def get_object_headers(self, bucket_name, object_key):
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
    def upload_object(self, file_path, bucket_name, object_key):
        """
        Uploads a file to S3.

        :param file_path: The local path of the file to be uploaded.
        :type file_path: str
        :param bucket_name: The name of the S3 bucket.
        :type bucket_name: str
        :param object_key: The key of the object in the S3 bucket.
        :type object_key: str
        """
        logger.debug(f"Uploading file: {file_path} to bucket: {bucket_name} as object: {object_key}")
        with open(file_path, 'rb') as f:
            self.s3_client.upload_fileobj(f, bucket_name, object_key)
        logger.debug(f"File uploaded: {file_path} as object: {object_key} in bucket: {bucket_name}")

    @Retryable()
    def delete_object(self, bucket_name, object_key):
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
    def move_object(self, src_bucket_name, src_object_key, dst_bucket_name, dst_object_key):
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
    def copy_object(self, src_bucket_name, src_object_key, dst_bucket_name, dst_object_key):
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
    def rename_object(self, bucket_name, src_object_key, dst_object_key):
        """
        Renames an object within the same S3 bucket.

        :param bucket_name: The name of the S3 bucket.
        :type bucket_name: str
        :param src_object_key: The current key of the object.
        :type src_object_key: str
        :param dst_object_key: The new key of the object.
        :type dst_object_key: str
        """
        logger.debug(f"Renaming object: {src_object_key} to {dst_object_key} in bucket: {bucket_name}")
        self.move_object(bucket_name, src_object_key, bucket_name, dst_object_key)
        logger.debug(f"Object renamed: {src_object_key} to {dst_object_key} in bucket: {bucket_name}")

    @Retryable()
    def check_object_existence(self, bucket_name, object_key):
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
    def list_objects(self, bucket_name, prefix=None):
        """
        Lists objects in an S3 bucket, optionally filtered by a prefix.

        :param bucket_name: The name of the S3 bucket.
        :type bucket_name: str
        :param prefix: The prefix to filter the objects.
        :type prefix: str, optional
        :returns: A list of object keys.
        :rtype: List[str]
        """
        logger.debug(f"Listing objects in bucket: {bucket_name} with prefix: {prefix}")
        paginator = self.s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
        object_list = [item['Key'] for page in page_iterator for item in page.get('Contents', [])]
        logger.debug(f"Objects listed in bucket: {bucket_name} with prefix: {prefix}")
        return object_list

    @Retryable()
    def check_bucket_permissions(self, bucket_name):
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
