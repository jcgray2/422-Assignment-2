import boto3

def upload_file_to_s3(file_path, bucket_name, object_name=None):
    if object_name is None:
        object_name = file_path

    # Initialize the S3 client
    s3 = boto3.client('s3')

    # Upload the file to S3
    try:
        response = s3.upload_file(file_path, bucket_name, object_name)
        print(f'File uploaded successfully: {object_name}')
    except Exception as e:
        print(f'Error uploading file: {e}')

# Specify the path to the file, bucket name, and object name (optional)
file_path = '/path/to/local/file.jpg'
bucket_name = 'your-s3-bucket-name'
object_name = 'uploaded-file.jpg'  # Optional: specify a different object name

# Upload the file to S3
upload_file_to_s3(file_path, bucket_name, object_name)
