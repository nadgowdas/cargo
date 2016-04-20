#
#Copyright IBM Corporation 2015.
#LICENSE: Apache License 2.0 http://opensource.org/licenses/Apache-2.0

"""
Constant variables library

This library holds constants for all the return codes of cargo System.
And possible HTTP code constants in the context of this system.

Available Functions:
 -herror: Mapping function from PubSub return codes to standard HTTP status codes
  
"""

SUCCESS = 0
FAILED = 1
IGNORE_MSG = 2
DUP_REQUEST = 3
NOT_FOUND = 4
NO_MSG_READY = 5
BAD_REQ = 9

HTTP_SUCCESS = 200
HTTP_CREATED = 201
HTTP_NO_CONTENT = 204
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409
HTTP_INTERNAL_ERR = 500

def herror(rc):
    """
    Map the cargo systems code to the standard HTTP return status code
    
    Args:
        rc: cargo system's return code constant
    
    Returns:
        corresponding HTTP status code
        
    """
    if rc in (SUCCESS, IGNORE_MSG, DUP_REQUEST):
        return HTTP_SUCCESS 
    if rc == NOT_FOUND:
        return HTTP_NOT_FOUND
    if rc == NO_MSG_READY:
        return  HTTP_NO_CONTENT
    if rc  == BAD_REQ:
        return HTTP_BAD_REQUEST
         
    return HTTP_INTERNAL_ERR
    
