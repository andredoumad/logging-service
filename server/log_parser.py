import boto3
import errno
import inspect
import logging
import glob
import os
import os.path
import socket
import sys
import unittest
import string
# import numpy as np
# import cv2
# import pyautogui
from datetime import datetime
# from settings import (SCREENSHOTS_ENABLED, AWS_S3_BUCKET)

# from settings import LOG_FILE_PATH

dir_path = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger(__name__)


def parse(payload): # noqa: C901, E261, E501
    """
    :param msg = base message for this log
    :param level = log level defaults to info but can also be debug, warning, error
    """

    def mkdir_p(path):
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    path = os.path.join(os.getcwd())
    filename = "log_parser.log"
    filepath = os.path.join(path, filename)

    now = datetime.utcnow()
    audit_init_time = str(now)
    audit_attempts = str(0)

    def bucket_object_exists(s3, path, bucket):
        s3 = boto3.resource("s3")
        bucket = s3.Bucket(bucket)
        for object_summary in bucket.objects.filter(Prefix=path):
            return True
        return False

    def upload_to_aws(local_filepath, bucket, s3_filename):
        s3 = boto3.client("s3")

        # is root audit_init_time folder missing?
        if not bucket_object_exists(s3, str(audit_init_time + "/"), bucket):
            s3.put_object(Bucket=bucket, Key=(audit_init_time+"/"))

        # is attempts subfolder created?
        s3_sub_directory = f"{audit_init_time}/{audit_attempts}/"
        if not bucket_object_exists(s3, s3_sub_directory, bucket):
            s3.put_object(Bucket=bucket, Key=(s3_sub_directory))

        # is screenshot subfolder created?
        s3_sub_directory = f"{audit_init_time}/{audit_attempts}/screenshots/"
        if not bucket_object_exists(s3, s3_sub_directory, bucket):
            s3.put_object(Bucket=bucket, Key=(s3_sub_directory))

        try:
            s3.upload_file(local_filepath, bucket, f"{s3_sub_directory}{s3_filename}")
            print("Upload Successful")
            return True
        except Exception as e:
            print(f"upload_to_aws error: {e}")
            return False

    def get_timestamp():
        time_string = float(datetime.utcnow().strftime("%y%m%d%H%M%S.%f"))
        time_string = str(round(time_string, 3))
        time_string = time_string.replace(".", "")
        while len(time_string) < 15:
            time_string += "0"
        return time_string

    def safe_name(filename):
        valid_chars = "-_() %s%s" % (string.ascii_letters, string.digits)
        name = str("".join(c for c in filename if c in valid_chars))[:150]
        return name.replace(" ", "_")

    # Combine AdviNow related information with message
    record = ""
    record += f"UTC: {now.strftime('%y-%m-%d %H:%M:%S')} "
    record += f"Level: {payload.get('level', 'info')} "
    record += f"Msg: {payload.get('msg', '')} "
    sys.stdout.write(record + "\n")
    with open(filepath, "a+") as f:
        f.write(record + "\n")

    if os.path.getsize(filepath) > 10000:
        with open(filepath, "w+") as f:
            f.write("")
    return record



class UnitTest(unittest.TestCase):
    def test_a(self):
        payload = {
            "msg": "hello",
            "level": "info"
        }
        # logger.info(process(payload))
        parse(payload)


if __name__ == ("__main__"):
    unittest.main()
