import boto3
import urllib.parse
import os
from PIL import Image

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    
    raw_key = event['Records'][0]['s3']['object']['key']
    file_key = urllib.parse.unquote_plus(raw_key, encoding='utf-8')
    download_path = f"/tmp/{os.path.basename(file_key)}"
    
    s3.download_file(source_bucket, file_key, download_path)

    
    with Image.open(download_path) as image:
        image.thumbnail((1920, 1920))
        processed_download_path = f"/tmp/processed_{os.path.basename(file_key)}"
        image.save(processed_download_path, optimize=True, quality=85)

    
    destination_bucket = 'minor-project-processed-egress-2026'
    s3.upload_file(processed_download_path, destination_bucket, file_key)

    
    table = dynamodb.Table('ImageMetadata')
    table.put_item(Item={'ImageID': file_key, 'Status': 'Processed'})

    return {"statusCode": 200, "body": "Success"}
    