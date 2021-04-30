from flask import Blueprint, request, jsonify, Response
import log_parser
bp_log = Blueprint('bp_log', __name__)


@bp_log.route("/", methods=["GET", "POST"])
def log():
    if request.method == "GET":
        data = getLog(request)
    elif request.method == "POST":
        data = postLog(request)

    return jsonify(data)



def postLog(request):
    """
    :param msg: message for this log
    :param level: log level defaults to info and can be info, debug, warning, error
    :param patient_token: patient token for log
    :param visit: patient visit
    """

    # TODO: complete ticket https://advinow.atlassian.net/browse/MS-13
    # TODO: POST
    """
    1)  accept json payload from microservice that defines if its an error or a log or both
    2)  generate flatfile with a filename of the visit / patient token
    3)  upload file to s3 bucket
    4)  report error / log to appropriate service
    5)  remove flatfile
    """

    data = request.get_json()
    log = log_parser.process(data)

    return data




def getLog(request):
    # TODO: GET
    """
    1)  receive timestamp or visit id / token
    2)  query s3 bucket for matching filename
    3)  return log file
    4)  optionally accept granular parameters to filter file by and parse file for so that instead of a file returned,
        we return a json payload containing only the data requested
    """
    data = {}
    return data



