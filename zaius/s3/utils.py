import boto3
import os
from functools import partial
from multiprocessing import Pool, cpu_count

import zaius.auth as auth

class S3Client():

    def __init__(self, auth_struct=None):
        self.auth = auth_struct if auth_struct is not None else auth.default()
        self.client = init_s3_client(self.auth)

    def download_from_s3(self, bucket, local_path, key):
        """
        downloads a file from s3
        """
        download_from_s3(bucket, local_path, key)
    
    def upload_to_s3(self, local_path, bucket, key):
        """
        uploads a file to s3
        """
        upload_to_s3(self.auth, local_path, bucket, key)

    def par_s3_download(self, bucket, keys, local_path):
        """
        Download a list of files living under s3:<bucket>/<keys>
        into a local folder.
        """
        f = partial(download_from_s3, self.auth, bucket, local_path)
        cores = cpu_count()
        
        with Pool(cores) as p:
            p.map(f, keys)


def init_s3_client(auth_struct):
    """
    initializes a s3 client for multiprocessing workers
    """
    return boto3.client("s3",
                        aws_access_key_id=auth_struct["aws_access_key_id"],
                        aws_secret_access_key=auth_struct["aws_secret_access_key"]
                        )

def download_from_s3(auth_struct, bucket, local_path, key):
    """
    downloads a file from s3, defined outside of class for general use
    and to allow for paralellism
    """
    _, fname = os.path.split(key)
    output = os.path.join(local_path, fname)
    client = init_s3_client(auth_struct)
    client.download_file(bucket, key, output)

def upload_to_s3(auth_struct, local_path, bucket, key):
    """
    uploads a file to s3, defined outside of class for general use
    and to allow for paralellism
    """
    client = init_s3_client(auth_struct)
    print(auth_struct['aws_access_key_id'])
    print(auth_struct["aws_secret_access_key"])
    client.upload_file(local_path, bucket, key)