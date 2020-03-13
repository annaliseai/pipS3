import glob
import logging
import os
import sys

import boto3
import pkg_resources
from jinja2 import Template

s3 = boto3.client("s3")

#  hardcoded values for now
https_endpoint = "http://pypi-prod-annalise-ai.s3-website-ap-southeast-2.amazonaws.com"
bucket = "pypi-prod-annalise-ai"
root_prefix = "simple"


index_template = pkg_resources.resource_filename(__name__, "data/index.html.j2")

artifacts_path = "./artifacts"
os.makedirs(artifacts_path, exist_ok=True)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("s3pkg")


def get_packages():
    for filename in glob.glob('dist/*.*'):
        ext = os.path.splitext(filename)[1]
        if ext in ['.gz', '.whl']:
            yield filename 


def get_key_name(wheel, project_name):
    object = os.path.basename(wheel)
    key = f"{root_prefix}/{project_name}/{object}"
    return key


def upload_to_s3(wheel, key):
    try:
        logger.info("Uploading %s to S3", key)
        s3.upload_file(wheel, bucket, key, ExtraArgs={"ACL": "public-read"})
    except Exception as e:
        print(str(e))


def list_keys(prefix):
    kwargs = {"Bucket": bucket, "Prefix": prefix, "Delimiter": "/"}
    resp = s3.list_objects_v2(**kwargs)
    return resp


def generate_template(bucket_listing):
    listing = [
        x["Key"] for x in bucket_listing["Contents"] if "index.html" not in x["Key"]
    ]
    keys = []
    for i in listing:
        bn = os.path.basename(i)
        uri = f"{https_endpoint}/{i}"
        keys.append({"uri": uri, "bn": bn})
    with open(index_template) as f:
        template = Template(f.read())
    output = template.render(keys=keys)
    with open(os.path.join(artifacts_path, "index.html"), "w") as f:
        f.write(output)


def upload_index(project_name):
    uri = f"{root_prefix}/{project_name}/index.html"
    try:
        s3.upload_file(
            os.path.join(artifacts_path, "index.html"),
            bucket,
            uri,
            ExtraArgs={"ACL": "public-read", "ContentType": "text/html"},
        )
    except Exception as e:
        print(str(e))


def publish_packages(project_name=None):

    if project_name is None:
        project_name = os.environ["BUILDKITE_PIPELINE_SLUG"]

    at_least_one = False
    for pkg in get_packages():
        key = get_key_name(pkg, project_name)
        upload_to_s3(pkg, key)
        prefix = f"{root_prefix}/{project_name}/"
        bucket_listing = list_keys(prefix)
        index = generate_template(bucket_listing)
        upload_index(project_name)
        at_least_one = True
    if not at_least_one:
        raise EnvironmentError("0 packages published")
