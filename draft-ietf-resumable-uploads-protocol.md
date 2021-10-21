title: tus - Resumable Uploads Protocol
abbrev: TODO - Abbreviation
docname: draft-tus-resumable-uploads-protocol-latest
category: info

ipr: trust200902
area: General
workgroup: TODO Working Group
keyword: Internet-Draft

stand_alone: yes
smart_quotes: no
pi: [toc, sortrefs, symrefs]

author:
 -
    ins: M. Kleidl
    name: Marius Kleidl
    organization: Transloadit Ltd
    email: marius@transloadit.com
    ins: J. Mehta
    name: Jiten Mehta
    organization: Apple Inc.
    email: jmehta@apple.com
    ins: G. Zhang
    name: Guoye Zhang
    organization: Apple Inc.
    email: guoye_zhang@apple.com

normative:
  RFC2119:

informative:


--- abstract

This document describes a mechanism which allows HTTP endpoints to add support for resumable uploads. It aims to address the issues around clients having to upload content from the start in case the original upload fails.

--- middle

# Introduction

HTTP already provides resumable downloads using the `Range` header. However, on its own HTTP does not contain a standardized mechanism for resumable uploads. This has lead to a situation where many web services implement a proprietary solution for handling connection issues during file uploads. Such a scattered landscape makes it impossible to develop clients with resumable upload capabilities in a generic approach without focusing on specific, proprietary solutions. It also limits the benefits of resumable uploads to web services that can free up the resources to implement this.

Resuming a previously interrupted upload continues the data transfer where it left off, without the need to transfer the first part again. This capability is especially important in applications handling large files or operating in areas with unreliable network infrastructure. Upload interruptions can occur voluntarily, i.e. the end-user wants to pause the upload, or involuntarily, i.e. the network connection drops.

This protocol specifies an approach for clients and servers to implement resumable uploads on top of HTTP/1.1, HTTP/2 and HTTP/3, allowing the reuse of existing infrastructure. It also allows clients to upgrade regular uploads automatically to resumable uploads based on service discovery.

# Conventions and Definitions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 {{RFC2119}} {{!RFC8174}} when, and only when, they appear in all capitals, as shown here.

# Uploading Procedure

The uploading of a file using the Resumable Uploads Protocol consists of multiple procedures:

1) The Upload Creation Procedure notifies the server that the client wants to begin an upload. The server should then reserve the required resources to accept the upload from the client. The client also begins transferring the file in the request body.

```
+---------+                                  +---------+                                            
| Client  |                                  | Server  |                                            
+---------+                                  +---------+                                            
     |                                            |                                                 
     | POST (with Upload-Token)                   |                                                 
     |------------------------------------------->|                                                 
     |                                            |                                                 
     |                                            | Reserve resources for Upload-Token              
     |                                            |------------------------------------------------ 
     |                                            |                                               | 
     |                                            |<----------------------------------------------- 
     |                                            |                                                 
     | Flow Interrupted                           |                                                 
     |------------------------------------------->|                                                 
     |                                            |                                          
```

 

2) If the connection to the server gets interrupted during the Upload Creation Procedure or the Upload Appending Procedure, the client may want to resume the upload. Before this is possible, the client must know the amount of data that the server was able to receive before the connection got interrupted. To achieve this, the client uses the Offset Retrieving Procedure to obtain the upload's offset.

```
+---------+                                      +---------+
| Client  |                                      | Server  |
+---------+                                      +---------+
     |                                                |
     | HEAD with Upload-Token                         |
     |----------------------------------------------->|
     |                                                |
     |              204 No Content with Upload-Offset |
     |<-----------------------------------------------|
     |                                                |
```

3) After the Offset Retrieving Procedure completes, the client can resume the upload by sending the remaining file content to the server, appending to the already stored data in the upload.

```
+---------+                                 +---------+
| Client  |                                 | Server  |
+---------+                                 +---------+
     |                                           |
     | PATCH with Upload-Token and Upload-Offset |
     |------------------------------------------>|
     |                                           |
     |                 201 Created on completion |
     |<------------------------------------------|
     |                                           |
```

4) If the client is not interesting in completing the upload anymore, it can instruct the server to delete the upload and free all related resources using the Upload Cancellation Procedure.

```
+---------+                                  +---------+
| Client  |                                  | Server  |
+---------+                                  +---------+
     |                                            |
     | DELETE with Upload-Token:                  |
     |------------------------------------------->|
     |                                            |
     |               204 No Content on completion |
     |<-------------------------------------------|
     |                                            |
```

For advanced use cases, the client is allowed to upload chunks to the server directly using Upload Appending Procedure.

1) If the client is aware that server supports resumable upload, it can skip Upload Creation Procedure and use Upload Appending Procedure to start an upload.

```
+---------+                                                     +---------+
| Client  |                                                     | Server  |
+---------+                                                     +---------+
     |                                                               |
     | PATCH with Upload-Token, Upload-Offset, and Upload-Incomplete |
     |-------------------------------------------------------------->|
     |                                                               |
     |              201 Created with Upload-Incomplete on completion |
     |<--------------------------------------------------------------|
     |                                                               |
```

2) The last chunk of the upload does not have the `Upload-Incomplete` header.

```
+---------+                                 +---------+
| Client  |                                 | Server  |
+---------+                                 +---------+
     |                                           |
     | PATCH with Upload-Token and Upload-Offset |
     |------------------------------------------>|
     |                                           |
     |                 201 Created on completion |
     |<------------------------------------------|
     |                                           |
```


## Upload Creation Procedure

Upload Creation Procedure is designed to be compatible with a regular upload, with the intention that the client MAY initiate a resumable upload without the knowledge of server support. Therefore all methods which allow the request body are allowed (including `PATCH`), along with all response status codes. This procedure is identified with the presence of the `Upload-Token` header and the absence of the `Upload-Offset` header [Request Identification]. The client is RECOMMENDED to use `POST` request if not otherwise specified.

The request MUST include the `Upload-Token` header which is a binary token with a minimum of 256-bit (16 byte) cryptographically-secure random binary data. The request MUST NOT include the `Upload-Offset` header or the `Upload-Incomplete` header. The server SHOULD reject shorter tokens by sending a `400 (Bad Request)` response.

`Upload-Token` is a structured field value, and its ABNF is

```
Upload-Token = sf-binary
```

If the request completes successfully, the server MUST acknowledge it by responding with a successful status code between 200 and 299 (inclusive). Server is RECOMMENDED to use `201 (Created)` response is not otherwise specified.

```
:method: POST
:scheme: https
:authority: example.com
:path: /upload
upload-token: :SGVs…SGU=:
[file content]

:status: 201
```

The client MAY automatically attempt upload resumption when the connection is terminated unexpectedly, or if a server error status code between 500 and 599 (inclusive) is received. The client SHOULD NOT automatically retry if a client error status code between 400 and 499 (inclusive) is received.

## Offset Retrieving Procedure

If an upload is interrupted, the client MAY attempt to fetch the offset of the incomplete upload by sending a `HEAD` request to the server with the same `Upload-Token`. The client MUST NOT initiate this procedure without the knowledge of server support [Service Discovery].

The request MUST use the `HEAD` method and include the `Upload-Token` header. The request MUST NOT include the `Upload-Offset` header or the `Upload-Incomplete` header.

If the server has resources allocated for this token, it MUST send back a `204 (No Content)` response with a header `Upload-Offset` which indicates the resumption offset for the client. If the server has multiple discontiguous chunks of the same file, the offset MUST be the end of the first chunk.

The response SHOULD include `Cache-Control: no-store` header to prevent HTTP caching.

ABNF of `Upload-Offset` is

```
Upload-Offset = sf-integer
```

If the server has no record of this token, it MUST respond with `404 (Not Found)` status code.

```
:method: HEAD
:scheme: https
:authority: example.com
:path: /upload
upload-token: :SGVs…SGU=:

:status: 204
upload-offset: 100
cache-control: no-store
```

The client MAY automatically start uploading from the beginning using Upload Creation Procedure if `404 (Not Found)` status code is received. The client SHOULD NOT automatically retry if a status code other than 204 and 404 is received.

## Upload Appending Procedure

Upload Appending Procedure can be used for either resuming an existing upload, or starting a new upload. The client MUST NOT initiate this procedure without the knowledge of server support [Service Discovery].

The request MUST use the `PATCH` method and include both the `Upload-Token` and the `Upload-Offset` header. The `Upload-Incomplete` header MAY be used if the request body is not the complete file. ABNF of `Upload-Incomplete` is

```
Upload-Incomplete = sf-boolean
```

The value of the `Upload-Incomplete` header MUST be true. The server MUST reject other values by sending a `400 (Bad Request)` response.

If the client receives the `Upload-Offset` from Offset Retrieving Procedure, it MAY resume the original upload by starting the transfer from the value indicated in the `Upload-Offset` header. and the values of both headers MUST match the values in Offset Retrieving Procedure.

If the request completes successfully and the entire file is sent, the server MUST acknowledge it by responding with a successful status code between 200 and 299 (inclusive). Server is RECOMMENDED to use a `201 (Created)` response is not otherwise specified.

If the request completes successfully but the file is not complete yet, the server MUST acknowledge it by responding with the `201 (Created)` status code with the `Upload-Incomplete` header set to true. It is worth noting that the server can receive individual chunks out of order, so the presence of the `Upload-Incomplete` header may not match in the request and the response.

If the server has no record of the token in `Upload-Token`, it should treat it as a new upload and allocate resources for this token.

```
:method: PATCH
:scheme: https
:authority: example.com
:path: /upload
upload-token: :SGVs…SGU=:
upload-offset: 100
[file content]

:status: 201
```

```
:method: PATCH
:scheme: https
:authority: example.com
:path: /upload
upload-token: :SGVs…SGU=:
upload-offset: 0
upload-incomplete: ?1
[partial file content]

:status: 201
upload-incomplete: ?1
```

Same as Upload Creation Procedure, the client MAY automatically attempt upload resumption when the connection is terminated unexpectedly, or if a server error status code between 500 and 599 (inclusive) is received. The client SHOULD NOT automatically retry if a client error status code between 400 and 499 (inclusive) is received.

## Upload Cancellation Procedure

If the client wants to stop the transfer before completion, it is OPTIONAL for the client to send a `DELETE` request to the server along with the `Upload-Token` which is an indication that the client is no longer interested in uploading this body and the server can release resources associated with this token. The client MUST NOT initiate this procedure without the knowledge of server support [Service Discovery].

If the server has successfully released the resources allocated for this token, it MUST send back a `204 (No Content)` response. The server SHOULD terminate all ongoing Upload Creation Procedure or Upload Appending Procedure for the same token before sending the response.

If the server has no record of the token in `Upload-Token`, it MUST respond with `404 (Not Found)` status code.

```
:method: DELETE
:scheme: https
:authority: example.com
:path: /upload
upload-token: :SGVs…SGU=:

:status: 204
```

# Request Identification

Upload Creation Procedure supports arbitrary methods including `PATCH`, therefore it is not possible to identify procedures purely by the method. The following algorithm is RECOMMENDED to identify the procedure from a request:

1. The `Upload-Token` header is not present -> Not resumable upload
2. The `Upload-Offset` header is present -> Upload Appending Procedure
3. The method is `HEAD` -> Offset Retrieving Procedure
4. The method is `DELETE` -> Upload Cancellation Procedure
5. Otherwise -> Upload Creation Procedure

# Redirection

The 301 (Moved Permanently) status code and the 302 (Found) status code MUST NOT be used in Offset Retrieving Procedure, Upload Appending Procedure, and Upload Cancellation Procedure responses. A 308 (Permanent Redirect) response MAY be persisted for all subsequent procedures. If client receives a 307 (Temporary Redirect) response in the Offset Retrieving Procedure, it MAY apply the redirection directly in the immediate subsequent Upload Appending Procedure.

# Service Discovery

A general purpose HTTP client can discover server support of resumable upload without prior knowledge. For this purpose, SETTINGS_RESUMABLE_UPLOAD setting is defined by this document for use with HTTP/2, HTTP/3, and future HTTP protocols.

The value of SETTINGS_RESUMABLE_UPLOAD MUST be 0 or 1. Any value other than 0 or 1 MUST be treated as a connection error of type PROTOCOL_ERROR. SETTINGS_RESUMABLE_UPLOAD MUST NOT be sent in client SETTINGS frame. Receiving SETTINGS_RESUMABLE_UPLOAD from the client MUST be treated as a connection error of type PROTOCOL_ERROR.

For HTTP/2, the server MUST send this SETTINGS parameter as part of the first SETTINGS frame. A sender MUST NOT change the SETTINGS_RESUMABLE_UPLOAD parameter value after the first SETTINGS frame. Detection of a change by a receiver MUST be treated as a connection error of type PROTOCOL_ERROR.

Upload Creation Procedure MAY be initiated by the client without the knowledge of server support, but all other procedures MUST NOT be used unless client is aware of server support through service discovery or other forms of hints.

# Security Considerations

`Upload-Token` is selected by the client which has no knowledge of tokens picked by other client, so uniqueness cannot be guaranteed. If the token is guessable, an attacker can append malicious data to existing uploads. To mitigate these issues, at least 256-bit cryptographically-secure random binary data is required for the token.

It is OPTIONAL for the server to partition upload tokens based on client identity established through other channels, such as Cookie or TLS client authentication.

# IANA Considerations

This specification registers the following entry in the Permanent Message Header Field Names registry established by [RFC3864]:

Header field name: Upload-Token, Upload-Offset, Upload-Incomplete

Applicable protocol: http

Status: standard

Author/change controller: IETF

Specification document(s): This document

Related information: n/a

This specification registers the following entry in the HTTP/2 Settings registry established by [HTTP2]:

Name: SETTINGS_RESUMABLE_UPLOAD

Code: 0xfd0g

Initial value: 0

Specification: This document

This specification registers the following entry in the HTTP/3 Settings registry established by [HTTP3]:

Name: SETTINGS_RESUMABLE_UPLOAD

Code: 0xfd0g

Initial value: 0

Specification: This document

--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge.
