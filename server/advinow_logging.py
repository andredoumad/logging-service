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


def advilog(msg, task=None, patient_id=None, patient_name=None, advinow_id=None, level="info",
            sqs_recv=None, sqs_state=None, chart_session_id=None, charting=None, exception=None,
            path=None, filename=None, screenshot=False, audit_init_time=None, audit_attempts=None): # noqa: C901, E261, E501
    """
    :param msg = base message for this log
    :param level =  log level can be: info, debug, warning, error
    :param advinow_id = advinow ID
    :param patient_id = patient ID
    :param patient_name = full patient name
    :param sqs_recv = description of the task from sqs, what was the program supposed to do.
    :param sqs_state = the current state of the sqs task, what is the program currently doing.
    :param chart_session_id = the chart session ID
    :param charting = major charting tasks that are being performed
    :param exception = error message

    :param path = directory path to write to
    :param filename = filename to write

    :param screenshot = bool whether or not to take a screenshot
    :param audit_init_time = the timestamp extracted from the audit IO 'init_audit' value - the primary key of the audit_record.
    :param audit_attempts = the current number of audit attempts.

    you have the option of setting path and filename for logs otherwise:
    if LOG_FILE_PATH != "" and path == "" and filename == "":
         os.path.join(os.getcwd, "filebeat", "advilog.log")
    """
    audit_init_time = str(audit_init_time)
    audit_attempts = str(audit_attempts)

    def mkdir_p(path):
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    LOG_FILE_PATH = os.path.dirname(os.path.realpath(__file__))
    if LOG_FILE_PATH and path is None and filename is None:
        path = os.path.split(LOG_FILE_PATH)[0]
        if not os.path.exists(path):
            mkdir_p(os.path.dirname(path))
        filename = os.path.split(LOG_FILE_PATH)[1]
    else:
        # os agnostic pathing
        if path is None:
            path = os.path.join(os.getcwd(), "filebeat")
        if not os.path.exists(path):
            mkdir_p(os.path.dirname(path))
        if filename is None:
            filename = "advilog.log"
    filepath = os.path.join(path, filename)

    # get stack info, for debuging information
    previous_frame = inspect.currentframe().f_back
    (filename, line_number, function_name, lines, index) = inspect.getframeinfo(previous_frame)
    del previous_frame  # drop the reference to the stack frame to avoid reference cycles
    now = datetime.utcnow()

    def bucket_object_exists(s3, path, bucket):
        s3 = boto3.resource("s3")
        bucket = s3.Bucket(bucket)
        for object_summary in bucket.objects.filter(Prefix=path):
            return True
        return False

    def upload_to_aws(local_file, bucket, s3_file):
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
            s3.upload_file(local_file, bucket, f"{s3_sub_directory}{s3_file}")
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
    #
    # def take_screenshot(screenshot_filepath):
    #     # take screenshot using pyautogu
    #     image = pyautogui.screenshot()
    #
    #     # since the pyautogui takes as a
    #     # PIL(pillow) and in RGB we need to
    #     # convert it to numpy array and BGR
    #     # so we can write it to the disk
    #     image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    #
    #     # writing it to the disk using opencv
    #     cv2.imwrite(screenshot_filepath, image)
    #
    # pyautogui_screenshot_message = None
    # # take screenshot
    # if SCREENSHOTS_ENABLED == 1 and screenshot:
    #     path = os.path.join(os.getcwd(), "screenshots")
    #     if not os.path.exists(path):
    #         mkdir_p(path)
    #     t = get_timestamp()
    #     if not exception and str(msg).lower().find("error") == -1:
    #         screenshot_filename = f"{t}_MSG_{msg.lower()}_METHOD_{function_name}"
    #     else:
    #         screenshot_filename = f"{t}_ERROR_MSG_{msg.lower()}_METHOD_{function_name}"
    #     screenshot_filename = f"{safe_name(screenshot_filename)}.png"
    #     screenshot_filepath = os.path.join(path, screenshot_filename)
    #     # selenium_driver.save_screenshot(screenshot_filepath)
    #     take_screenshot(screenshot_filepath)
    #     uploaded = upload_to_aws(screenshot_filepath, AWS_S3_BUCKET, screenshot_filename)
    #     if uploaded:
    #         pyautogui_screenshot_message = (
    #             f"Uploaded screenshot. {screenshot_filename} to AWS S3 bucket: "
    #             f"{AWS_S3_BUCKET}.")
    #     else:
    #         pyautogui_screenshot_message = (
    #             f"WARNING: Uploading screenshot to AWS S3: {AWS_S3_BUCKET} FAILED!.")
    #     images = glob.glob(f"{path}/*.png")
    #     if len(images) > 20:
    #         # os.remove(images[len(images)-1])
    #         os.remove(min(images, key=os.path.getctime))

    # Combine AdviNow related information with message
    record = ""
    record += f"UTC: {now.strftime('%y-%m-%d %H:%M:%S')} "
    if advinow_id:
        record += f"AdviNow_ID: {advinow_id} "
    if patient_id:
        record += f"Patient_ID: {patient_id} "
    if patient_name:
        record += f"Patient_Name: f{truncate_data(patient_name)} "
    record += f"Level: {level} "
    record += f"Msg: {msg} "
    if task:
        record += f"Task: {task} "
    if chart_session_id:
        record += f"Chart_session_id: {chart_session_id} "
    if charting:
        record += f"Charting: {charting} "
    if sqs_state:
        record += f"SQS_recv: {sqs_recv} "
    if sqs_state:
        record += f"SQS_state: {sqs_state} "
    if exception:
        record += f"Exception: {exception} "
    record += f"Host: {socket.gethostname()} "
    record += f"File: {str(filename)[-25:]} "
    record += f"Line: {line_number} "
    record += f"Method: {function_name} "
    # if pyautogui_screenshot_message is not None:
    #     record += f"Screenshot: {pyautogui_screenshot_message} "

    sys.stdout.write(record + "\n")
    with open(filepath, "a+") as f:
        f.write(record + "\n")

    if os.path.getsize(filepath) > 10000:
        with open(filepath, "w+") as f:
            f.write("")
    return record


def truncate_data(s: str) -> str:
    """
    s = string of one or more words.
    """
    s = str(s)

    def truncate(data):
        truncated_data = data[0:int(len(data)/3)+1] + "... "
        return truncated_data

    patient_truncated_data = ""
    if s.find(" ") != -1:
        strings = s.split()
        for item in strings:
            patient_truncated_data += truncate(item)
    else:
        patient_truncated_data = truncate(s)
    return patient_truncated_data


class UnitTest(unittest.TestCase):
    def test_a(self):
        logger.info(advilog(
            msg="hi",
            advinow_id=1234,
            patient_id=5678,
            patient_name="John Doe",
            sqs_recv="requested sqs work",
            sqs_state="state of sqs work",
            chart_session_id=1001,
            charting="procedure a, procedure b, ...",
            exception="a test exception.",
        ))
        logger.info(advilog(
            msg="hi",
            advinow_id=None,
            patient_id=None,
            patient_name="John Doe",
            sqs_recv="requested sqs work",
            sqs_state="state of sqs work",
            chart_session_id=1001,
            charting="procedure a, procedure b, ...",
            exception="a test exception.",
        ))
        logger.info(advilog(
            msg="hi",
        ))

    def test_truncate_patient_name(self):
        patient_name = "andre doumad"
        print(truncate_data(patient_name))
        patient_name = "a b c"
        print(truncate_data(patient_name))
        patient_name = "Joe j Johnson"
        print(truncate_data(patient_name))
        patient_name = 12345
        print(truncate_data(patient_name))

    def test_advilog_screenshot(self):
        logger.info(advilog(
            msg="hi",
            advinow_id=None,
            patient_id=None,
            patient_name="John Doe",
            sqs_recv="requested sqs work",
            sqs_state="state of sqs work",
            chart_session_id=1001,
            charting="procedure a, procedure b, ...",
            exception="a test exception.",
            screenshot=True,
            audit_init_time=12345,
            audit_attempts=0,
        ))


if __name__ == ("__main__"):
    unittest.main()
