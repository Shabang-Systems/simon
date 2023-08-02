'''
Utilities for interacting with AWS services (especially S3).
'''

import os
from urllib.parse import urlparse, parse_qs

import boto3


S3_CONSOLE_NETLOC = 's3.console.aws.amazon.com'


def __parse_s3_console_url(url):
    # URLs will either be in the form
    # https://s3.console.aws.amazon.com/s3/buckets/{bucket}?prefix={prefix}
    # or
    # https://s3.console.aws.amazon.com/s3/object/{bucket}?prefix={prefix}
    # with (optional) additional query parameters.
    parsed = urlparse(url)

    if parsed.netloc != S3_CONSOLE_NETLOC:
        return None, None

    # The bucket name is always the last part of the URL path
    bucket = os.path.basename(parsed.path)

    # Parse query string to separate arguments into dict
    query_params = parse_qs(parsed.query)
    # Because query params are always parsed to lists, need to specifically get first element
    key = query_params.get('prefix', [''])[0]

    return bucket, key


def parse_s3_uri(uri):
    '''
    Given a valid S3 URI of any form, returns the bucket and item key. Returns (None, None) otherwise.
    '''
    parsed = urlparse(uri)
    if parsed.scheme == 's3':
        # S3 URIs are straightforward, taking the form s3://bucket/key
        # The key might be a full path like s3://bucket/some/long/path/to/item but that doesn't matter here.
        return parsed.netloc, parsed.path.lstrip('/')
    elif parsed.scheme == 'https':
        # Check if this is a console URL and handle it accordingly
        if parsed.netloc == S3_CONSOLE_NETLOC:
            return __parse_s3_console_url(uri)

        if not parsed.netloc.endswith('s3.amazonaws.com'):
            # Doesn't look like an S3 URL
            return None, None

        # netloc should be of the form {bucket}.s3.amazonaws.com
        if len(parsed.netloc.split('.')) != 4:
            # Should be 4 parts: {bucket}, s3, amazonaws, com
            return None, None

        bucket = parsed.netloc.split('.')[0]
        key = parsed.path.lstrip('/')

        return bucket, key
    else:
        # S3 URIs must use either the S3 scheme or HTTPS.
        # If neither, URI is invalid
        return None, None


def is_s3_uri(uri):
    bucket, _ = parse_s3_uri(uri)

    return bool(bucket)


def get_files_at_s3_uri(uri):
    '''
    Given an S3 URI, return a list of files at that location.

    If the URI points to a directory, returns all files in that directory and its subdirectories.
    If the URI points to a single file, returns a list containing just that file.
    '''
    bucket_name, path = parse_s3_uri(uri)
    if not bucket_name:
        raise Exception(f'Invalid S3 URI: {uri}')
    s3_client = boto3.client('s3')
    response = s3_client.list_objects_v2(
        Bucket=bucket_name, Prefix=path, Delimiter='/')

    contents = response.get('Contents', [])
    # Filter out directories and empty files
    contents = [obj for obj in contents if obj.get('Size', 0) > 0]
    objects = [f's3://{bucket_name}/{obj["Key"]}' for obj in contents]

    if 'CommonPrefixes' in response:
        # This is a directory with subdirectories
        # Grab all the objects in the subdirectories and return those too
        subdirectories = response['CommonPrefixes']
        for subdir in subdirectories:
            subdir_uri = f's3://{bucket_name}/{subdir["Prefix"]}'
            objects.extend(get_files_at_s3_uri(subdir_uri))

    return objects


def s3_uri_to_http(uri):
    '''
    Given a valid S3 URI of any form, returns the HTTPS URL for the same object. Returns None otherwise.
    '''
    bucket, key = parse_s3_uri(uri)

    if not bucket:
        return None

    return f'https://{bucket}.s3.amazonaws.com/{key}'


def read_file_from_s3(uri):
    '''
    Read a file from S3 and return its contents.
    '''
    bucket, path = parse_s3_uri(uri)
    file_name = os.path.basename(path)

    s3_client = boto3.client('s3')
    response = s3_client.get_object(Bucket=bucket, Key=path)
    file_data = response['Body'].read().decode('utf-8')

    return file_name, file_data
