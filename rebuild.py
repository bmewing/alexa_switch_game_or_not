#! /bin/python3
import boto3

def upload_zip():
    s3 = boto3.resource('s3')
    response = s3.meta.client.upload_file('lambda.zip', 'lambda-upload-mewing', 'switch_game_or_not_alexa.zip')
    return response

def migrate_zip():
    client = boto3.client('lambda')
    response = client.update_function_code(
        FunctionName = "arn:aws:lambda:us-east-1:243701628035:function:switch_game_or_not_alexa",
        S3Bucket='lambda-upload-mewing',
        S3Key='switch_game_or_not_alexa.zip'
    )
    return response

if __name__ == "__main__":
    _ = upload_zip()
    _ = migrate_zip()