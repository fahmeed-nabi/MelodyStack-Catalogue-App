import os, boto3

def upload_file(filename, bucket, object_name=None):
    '''
    Upload a file to an s3 bucket
    Parameters
    ----------
    filename : string
        filename for file to be uploaded
    bucket : string
        name of bucket to be uploaded to
    object_name : string
        name of file once uploaded, defaulted to filename

    Returns
    -------
    boolean
        True if successful, False otherwise
    '''
    from dotenv import load_dotenv
    load_dotenv()
    if object_name is None:
        object_name = os.path.basename(filename)
    client = boto3.client('s3', aws_access_key_id = os.getenv('AWS_ID'), aws_secret_access_key = os.getenv('AWS_KEY'))
    try:
        client.upload_file(filename, bucket, object_name)
    except:
        print(f"file at {filename} was not successfully uploaded")
        return False
    return True

def download_file(filename, bucketname, dir):
    '''
    Download a file from s3 bucket
    Parameters
    ----------
    filename : string
        filename for file to be downloaded
    bucket : string
        name of bucket to be downloaded from
    dir : string
        desired directory for download

    Returns
    -------
    boolean
        True if successful, False otherwise
    '''
    from dotenv import load_dotenv
    load_dotenv()
    client = boto3.client('s3', aws_access_key_id = os.getenv('AWS_ID'), aws_secret_access_key = os.getenv('AWS_KEY'))
    try:
        client.download_file(bucketname, filename, dir)
        print(f"File '{filename}' downloaded from bucket '{bucketname}' to '{dir}'")
    except:
        print(f"failed to download {filename} from {bucketname} to {dir}")
        return False
    return True 