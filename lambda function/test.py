import os
import pytest

os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "eu-north-1"

import boto3
from moto import mock_aws
from PIL import Image
import io
from lambda_function import lambda_handler

@pytest.fixture
def s3_and_dynamodb():
    """Sets up a fake, temporary AWS environment."""
    with mock_aws():
        s3 = boto3.client("s3", region_name="eu-north-1")
        dynamodb = boto3.resource("dynamodb", region_name="eu-north-1")

        s3.create_bucket(
            Bucket="minor-project-raw-ingress-2026",
            CreateBucketConfiguration={'LocationConstraint': 'eu-north-1'}
        )
        s3.create_bucket(
            Bucket="minor-project-processed-egress-2026",
            CreateBucketConfiguration={'LocationConstraint': 'eu-north-1'}
        )

        table = dynamodb.create_table(
            TableName="ImageMetadata", 
            KeySchema=[{'AttributeName': 'ImageID', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'ImageID', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        yield s3, table

def test_lambda_pipeline(s3_and_dynamodb):
    """The actual test that runs against the fake environment."""
    s3, table = s3_and_dynamodb

    file_name = "test image.jpg"
    image = Image.new('RGB', (100, 100), color = 'red')
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    
    s3.put_object(Bucket="minor-project-raw-ingress-2026", Key=file_name, Body=img_byte_arr.getvalue())

    event = {
        "Records": [{
            "s3": {
                "bucket": {"name": "minor-project-raw-ingress-2026"},
                "object": {"key": "test+image.jpg"}
            }
        }]
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 200

    processed_objects = s3.list_objects_v2(Bucket="minor-project-processed-egress-2026")
    assert 'Contents' in processed_objects
    assert processed_objects['Contents'][0]['Key'] == "test image.jpg"

    db_response = table.get_item(Key={'ImageID': "test image.jpg"})
    assert 'Item' in db_response
    assert db_response['Item']['Dimensions'] == "100x100"
