import urllib.parse
import os
import boto3
import datetime
from PIL import Image
import exifread

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

table = dynamodb.Table('ImageMetadata')  

def lambda_handler(event, context):
    try:
        source_bucket = event['Records'][0]['s3']['bucket']['name']
        destination_bucket = 'minor-project-processed-egress-2026' # Update if needed
        
        raw_key = event['Records'][0]['s3']['object']['key']
        file_key = urllib.parse.unquote_plus(raw_key, encoding='utf-8')
        
        download_path = f"/tmp/{os.path.basename(file_key)}"
        processed_download_path = f"/tmp/processed_{os.path.basename(file_key)}"
        
        s3.download_file(source_bucket, file_key, download_path)
        original_size_kb = round(os.path.getsize(download_path) / 1024, 2)

        camera_model = "Unknown"
        with open(download_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            if 'Image Model' in tags:
                camera_model = str(tags['Image Model'])

        image = Image.open(download_path)
        width, height = image.size
 
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
     
        image.save(processed_download_path, optimize=True, quality=85)
        compressed_size_kb = round(os.path.getsize(processed_download_path) / 1024, 2)

        s3.upload_file(processed_download_path, destination_bucket, file_key)

        table.put_item(
            Item={
                'ImageID': file_key,
                'UploadTimestamp': str(datetime.datetime.now()),
                'CameraModel': camera_model,
                'Dimensions': f"{width}x{height}",
                'OriginalSize_KB': str(original_size_kb),
                'CompressedSize_KB': str(compressed_size_kb)
            }
        )

        print(f"Success! {file_key} processed and logged to DynamoDB.")
        return {'statusCode': 200, 'body': 'Pipeline complete.'}

    except Exception as e:
        print(f"Error processing {file_key}: {str(e)}")
        raise e