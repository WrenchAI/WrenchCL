import boto3
from WrenchCL.WrenchLogger import wrench_logger


class S3Handler:
    """
    A class to handle S3 operations following the Singleton pattern.

    Attributes:
    - s3_client (boto3.client): The S3 client used for operations.
    """

    _instance = None  # Singleton instance

    def __new__(cls):
        """Implement Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(S3Handler, cls).__new__(cls)
            cls._instance.initialized = False  # Indicate if the class has been initialized with configuration
        return cls._instance

    def __init__(self):
        self.initialized = False
        """Initialize the S3Handler class."""
        if not hasattr(self, "s3_client"):
            self.s3_client = None

    def load_configuration(self, key_id, secret_key, region):
        """
        Load AWS configuration for S3 client.

        Parameters:
        - key_id (str): AWS Access Key ID
        - secret_key (str): AWS Secret Access Key
        - region (str): AWS region
        """
        try:
            self.s3_client = boto3.client('s3', aws_access_key_id=key_id,
                                          aws_secret_access_key=secret_key,
                                          region_name=region)
            wrench_logger.debug('Initialized S3 client successfully.')
            self.initialized = True
        except Exception as e:
            wrench_logger.error(f'Failed to initialize S3 client: {e}')
            self.initialized = False
            raise e

    def list_files(self, bucket_name, s3_path_prefix=''):
        """
        List files in an S3 bucket path.

        Parameters:
        - bucket_name (str): Name of the S3 bucket
        - s3_path_prefix (str): Path prefix to filter files

        Returns:
        - list: List of file names
        """
        if not self.initialized:
            wrench_logger.error('S3Handler is not initialized. Please run the load_configuration() method')
            raise NotImplementedError

        response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_path_prefix)
        return [item['Key'] for item in response.get('Contents', [])]

    def upload_file(self, bucket_name, file_path, s3_path):
        """
        Upload a file to an S3 bucket.

        Parameters:
        - bucket_name (str): Name of the S3 bucket
        - file_path (str): Local path to the file to be uploaded
        - s3_path (str): Destination path in the S3 bucket

        Returns:
        - bool: True if successful, False otherwise
        """
        try:
            self.s3_client.upload_file(file_path, bucket_name, s3_path)
            wrench_logger.info(f'File {file_path} uploaded to {s3_path} in bucket {bucket_name}.')
            return True
        except Exception as e:
            wrench_logger.error(f'Failed to upload file {file_path} to {s3_path} in bucket {bucket_name}: {e}')
            return False

    def delete_file(self, bucket_name, s3_path):
        """
        Delete a file from an S3 bucket.

        Parameters:
        - bucket_name (str): Name of the S3 bucket
        - s3_path (str): Path in the S3 bucket to the file to be deleted

        Returns:
        - bool: True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=s3_path)
            wrench_logger.info(f'File {s3_path} deleted from bucket {bucket_name}.')
            return True
        except Exception as e:
            wrench_logger.error(f'Failed to delete file {s3_path} from bucket {bucket_name}: {e}')
            return False


s3Instance = S3Handler()
