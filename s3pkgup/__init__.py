import glob
import logging
import os
import sys

import boto3
import pkg_resources
from jinja2 import Template

s3 = boto3.client('s3')

#  hardcoded values for now
https_endpoint = 'http://pypi-prod-annalise-ai.s3-website-ap-southeast-2.amazonaws.com'
bucket = 'pypi-prod-annalise-ai'
root_prefix = 'simple'
#  variables
project_name = os.environ['BUILDKITE_PIPELINE_SLUG']

index_template = pkg_resources.resource_filename(__name__, 'index.html.j2')

artifacts_path = './artifacts'

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('s3pkg')


def get_wheels():
    wheels = glob.glob('dist/*.tar.gz')
    return wheels


def get_key_name(wheel):
    object = os.path.basename(wheel)
    key = f'{root_prefix}/{project_name}/{object}'
    return key


def upload_to_s3(wheel, key):
    try:
        logger.info('Uploading %s to S3', key)
        s3.upload_file(wheel, bucket, key, ExtraArgs={'ACL': 'public-read'})
    except Exception as e:
        print(str(e))


def list_keys(prefix):
    kwargs = {
        'Bucket': bucket,
        'Prefix': prefix,
        'Delimiter': '/'
    }
    resp = s3.list_objects_v2(**kwargs)
    return resp


def generate_template(bucket_listing):
    listing = [ x['Key'] for x in bucket_listing['Contents'] if 'index.html' not in x['Key'] ]
    keys = []
    for i in listing:
        bn = os.path.basename(i)
        uri = f'{https_endpoint}/{i}'
        keys.append({'uri': uri, 'bn': bn})
    with open(index_template) as f:
        template = Template(f.read())
    output = template.render(keys=keys)
    with open(os.path.join(artifacts_path, 'index.html', 'w')) as f:
        f.write(output)


def upload_index():
    uri = f'{root_prefix}/{project_name}/index.html'
    try:
        s3.upload_file(os.path.join(artifacts_path, 'index.html'), bucket, uri, ExtraArgs={'ACL': 'public-read', 'ContentType': 'text/html'})
    except Exception as e:
        print(str(e))


def publish_wheel():
    wheels = get_wheels()
    for wheel in wheels:
        key = get_key_name(wheel)
        upload_to_s3(wheel, key)
    prefix = f'{root_prefix}/{project_name}/'
    bucket_listing = list_keys(prefix)
    index = generate_template(bucket_listing)
    upload_index()
