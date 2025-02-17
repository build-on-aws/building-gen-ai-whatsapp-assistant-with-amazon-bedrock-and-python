import boto3
import requests

s3_resource = boto3.resource('s3')

client_s3 = boto3.client('s3')

def download_file(base_path,bucket, key, filename):
    print("Download file from s3://{}{}".format(bucket,key))
    with open(base_path+filename, "wb") as data:
        client_s3.download_fileobj(bucket, key, data)
    print("Download file from s3://{}{}".format(bucket,key))
    return True

def upload_data_to_s3(bytes_data,bucket_name, s3_key):
    obj = s3_resource.Object(bucket_name, s3_key)
    obj.put(ACL='private', Body=bytes_data)
    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
    return s3_url

def download_file_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        return None

def get_media_url(mediaId,whatsToken):
    
    URL = 'https://graph.facebook.com/v17.0/'+mediaId
    headers = {'Authorization':  whatsToken}
    print("Requesting")
    response = requests.get(URL, headers=headers)
    responsejson = response.json()
    if('url' in responsejson):
        print("Responses: "+ str(responsejson))
        return responsejson['url']
    else:
        print("No URL returned")
        return None

def get_whats_media(url,whatsToken):
    headers = {'Authorization':  whatsToken}
    response = requests.get(url,headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        return None
    
def put_file(base_path,filename, bucket, key):
    with open(base_path+filename, "rb") as data:
        client_s3.upload_fileobj(data,bucket, key+filename)
    print("Put file in s3://{}{}{}".format(bucket,key,filename))


