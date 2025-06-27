# files_api_sdk.DefaultApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**upload_file_v1_files_file_path_put**](DefaultApi.md#upload_file_v1_files_file_path_put) | **PUT** /v1/files/{file_path} | Upload File


# **upload_file_v1_files_file_path_put**
> PutFileResponse upload_file_v1_files_file_path_put(file_path, file)

Upload File

Upload a file.

### Example

```python
import time
import os
import files_api_sdk
from files_api_sdk.models.put_file_response import PutFileResponse
from files_api_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = files_api_sdk.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with files_api_sdk.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = files_api_sdk.DefaultApi(api_client)
    file_path = 'file_path_example' # str | Valid file path without invalid characters
    file = None # bytearray | 

    try:
        # Upload File
        api_response = api_instance.upload_file_v1_files_file_path_put(file_path, file)
        print("The response of DefaultApi->upload_file_v1_files_file_path_put:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->upload_file_v1_files_file_path_put: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **file_path** | **str**| Valid file path without invalid characters | 
 **file** | **bytearray**|  | 

### Return type

[**PutFileResponse**](PutFileResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

