import boto3
import os
from functools import partial
from multiprocessing import Pool, cpu_count

import zaius.auth as auth


def init_s3_client(auth_struct):
    """
    initializes a s3 client for multiprocessing workers
    """
    auth_struct = auth_struct if auth_struct is not None else auth.default()
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


def par_s3_download(auth_struct, bucket, keys, local_path):
    """
    Download a list of files living under s3:<bucket>/<keys>
    into a local folder.
    """
    f = partial(download_from_s3, auth_struct, bucket, local_path)
    cores = cpu_count()
    
    with Pool(cores) as p:
        p.map(f, keys)


def upload_to_s3(auth_struct, local_path, bucket, key):
    """
    uploads a file to s3, defined outside of class for general use
    and to allow for paralellism
    """
    client = init_s3_client(auth_struct)
    client.upload_file(local_path, bucket, key)


def list_objects(auth_struct, bucket, prefix):
    """
    lists objects found at an s3_url
    """
    client = init_s3_client(auth_struct)
    return client.list_objects_v2(Bucket=bucket, Prefix=prefix)
