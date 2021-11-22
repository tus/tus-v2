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

This protocol specifies an approach for clients and servers to implement resumable uploads on top of HTTP/1.1, HTTP/2 and HTTP/3, allowing the reuse of existing infrastructure. It also allows clients to upgrade regular uploads automatically to resumable uploads.

# Conventions and Definitions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 {{RFC2119}} {{!RFC8174}} when, and only when, they appear in all capitals, as shown here.

# Uploading Procedure

The uploading of a file using the Resumable Uploads Protocol consists of multiple procedures:

1) The Upload Transfer Procedure can be used to notify the server that the client wants to begin an upload. The server should then reserve the required resources to accept the upload from the client. The client also begins transferring the file in the request body. An informational response can be sent to the client to signal the support of resumable upload on the server.

```
+---------+                                  +---------+                                            
| Client  |                                  | Server  |                                            
+---------+                                  +---------+                                            
     |                                            |                                                 
     | POST with Upload-Token                     |                                                 
     |------------------------------------------->|                                                 
     |                                            |                                                 
     |                                            | Reserve resources for Upload-Token              
     |                                            |------------------------------------------------ 
     |                                            |                                               | 
     |                                            |<----------------------------------------------- 
     |                                            |                                                 
     |            104 Upload Resumption Supported |
     |<-------------------------------------------|
     |                                            |                                                 
     | Flow Interrupted                           |                                                 
     |------------------------------------------->|                                                 
     |                                            |                                          
```

2) If the connection to the server gets interrupted during the Upload Transfer Procedure, the client may want to resume the upload. Before this is possible, the client must know the amount of data that the server was able to receive before the connection got interrupted. To achieve this, the client uses the Offset Retrieving Procedure to obtain the upload's offset.

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
     |  POST with Upload-Token and Upload-Offset |
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
     | DELETE with Upload-Token                   |
     |------------------------------------------->|
     |                                            |
     |               204 No Content on completion |
     |<-------------------------------------------|
     |                                            |
```

For advanced use cases, the client is allowed to upload incomplete chunks of a file to the server sequentially.

1) If the client is aware that the server supports resumable upload, it can use the Upload Transfer Procedure with the `Upload-Incomplete` header to start an upload.

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


## Upload Transfer Procedure

The Upload Transfer Procedure can be used for either starting a new upload, or resuming an existing upload. A limited form of this procedure MAY be used by the client to start a new upload without the knowledge of server support.

This procedure is designed to be compatible with a regular upload. Therefore all methods are allowed with the exception of `GET`, `HEAD`, `DELETE`, and `OPTIONS`. And all response status codes are allowed. The client is RECOMMENDED to use `POST` request if not otherwise specified.

The client MUST use the same method throughout an entire upload. The server SHOULD reject the attempt to resume an upload with a different method with `400 (Bad Request)` response.

The client MUST NOT perform multiple Upload Transfer Procedures for the same file in parallel.

The request MUST include the `Upload-Token` header which uniquely identifies an upload. The client MUST NOT reuse the token for a different upload.

When resuming an upload, the `Upload-Offset` header MUST be set to the resumption offset. The resumption offset 0 indicates a new upload. The absence of the `Upload-Offset` header implies the resumption offset of 0.

If the end of the request body is not the end of the upload, the `Upload-Incomplete` header MUST be set to true.

The client MAY send the metadata of the file using headers such as `Content-Type` and `Content-Disposition` when starting a new upload. It is OPTIONAL for the client to repeat the metadata when resuming an upload.

If the server has no record of the token but the offset is non-zero, it MUST respond with 404 (Not Found) status code.

The server MUST terminate any ongoing Upload Transfer Procedure for the same token after validating the request headers before processing the request body. Since the client cannot perform multiple transfers in parallel, the server can assume that the previous attempt has already failed. Therefore, the server MAY abruptly terminate the previous HTTP connection or stream.

If the offset in the `Upload-Offset` header does not match the existing file size, the server MUST respond with 400 (Bad Request) status code.

If the request completes successfully and the entire file is received, the server MUST acknowledge it by responding with a successful status code between 200 and 299 (inclusive). Server is RECOMMENDED to use `201 (Created)` response if not otherwise specified. The response MUST NOT include the `Upload-Incomplete` header.

If the request completes successfully but the file is not complete yet indicated by the `Upload-Incomplete` header, the server MUST acknowledge it by responding with the `201 (Created)` status code with the `Upload-Incomplete` header set to true.

```
:method: POST
:scheme: https
:authority: example.com
:path: /upload
upload-token: :SGVs…SGU=:
[file content]

:status: 104

:status: 201
```

```
:method: POST
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

The client MAY automatically attempt upload resumption when the connection is terminated unexpectedly, or if a server error status code between 500 and 599 (inclusive) is received. The client SHOULD NOT automatically retry if a client error status code between 400 and 499 (inclusive) is received.

### Feature Detection

If the client has no knowledge of whether the server supports resumable upload, the Upload Transfer Procedure MAY be used with some additional constraints. In particular, the `Upload-Offset` header and the `Upload-Incomplete` header MUST NOT be sent in the request if the server support is unclear. This allows the upload to function as if it is a regular upload.

If the server detects the Upload Transfer Procedure with neither the `Upload-Offset` header nor the `Upload-Incomplete` header, and it supports resumable upload, an informational response with `104 (Upload Resumption Supported)` status MAY be sent to the client while the request body is being uploaded.

The client MUST NOT attempt to resume an upload if it did not receive the `104 (Upload Resumption Supported)` informational response, and it does not have other signals of whether the server supporting resumable upload.

If the client is aware of the server support, it SHOULD start an upload with the `Upload-Offset` header set to 0 in order to prevent the unnecessary informational response.

## Offset Retrieving Procedure

If an upload is interrupted, the client MAY attempt to fetch the offset of the incomplete upload by sending a `HEAD` request to the server with the same `Upload-Token`. The client MUST NOT initiate this procedure without the knowledge of server support.

The request MUST use the `HEAD` method and include the `Upload-Token` header. The request MUST NOT include the `Upload-Offset` header or the `Upload-Incomplete` header. The server MUST reject the request with the `Upload-Offset` header or the `Upload-Incomplete` header by sending a `400 (Bad Request)` response.

The client MUST NOT perform the Offset Retrieving Procedure while the Upload Transfer Procedures is in progress.

If the server has resources allocated for this token, it MUST send back a `204 (No Content)` response with a header `Upload-Offset` which indicates the resumption offset for the client.

The server MUST terminate any ongoing Upload Transfer Procedure for the same token before generating the offset. This ensures that the offset is accepted by a subsequent Upload Transfer Procedure. The server MAY terminate an ongoing Upload Transfer Procedure by abruptly terminating the HTTP connection or stream.

The response SHOULD include `Cache-Control: no-store` header to prevent HTTP caching.

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

The client MAY automatically start uploading from the beginning using Upload Transfer Procedure if `404 (Not Found)` status code is received. The client SHOULD NOT automatically retry if a status code other than 204 and 404 is received.

## Upload Cancellation Procedure

If the client wants to terminate the transfer without the ability to resume, it MAY send a `DELETE` request to the server along with the `Upload-Token` which is an indication that the client is no longer interested in uploading this body and the server can release resources associated with this token. The client MUST NOT initiate this procedure without the knowledge of server support.

The request MUST use the `DELETE` method and include the `Upload-Token` header. The request MUST NOT include the `Upload-Offset` header or the `Upload-Incomplete` header. The server MUST reject the request with the `Upload-Offset` header or the `Upload-Incomplete` header by sending a `400 (Bad Request)` response.

If the server has successfully released the resources allocated for this token, it MUST send back a `204 (No Content)` response.

The server MAY terminate any ongoing Upload Transfer Procedure for the same token before sending the response by abruptly terminating the HTTP connection or stream.

If the server has no record of the token in `Upload-Token`, it MUST respond with `404 (Not Found)` status code.

```
:method: DELETE
:scheme: https
:authority: example.com
:path: /upload
upload-token: :SGVs…SGU=:

:status: 204
```

# Header Fields

## Upload-Token

`Upload-Token` is an Item Structured Header. Its value MUST be either a byte sequence, a string, or a token, and its ABNF is

```
Upload-Token = sf-binary / sf-string / sf-token
```

If not otherwise specified by the server, the client is RECOMMENDED to use 256-bit (32 bytes) cryptographically-secure random binary data as the value of the `Upload-Token`, in order to ensure that it is globally unique and non-guessable.

A conforming implementation MUST be able to handle a `Upload-Token` field value of at least 128 octets.

## Upload-Offset

`Upload-Offset` is an Item Structured Header. Its value MUST be an integer. Its ABNF is

```
Upload-Offset = sf-integer
```

## Upload-Incomplete

`Upload-Incomplete` is an Item Structured Header. Its value MUST be a boolean. Its ABNF is

```
Upload-Incomplete = sf-boolean
```

The value of the `Upload-Incomplete` header MUST be true.

# Redirection

The 301 (Moved Permanently) status code and the 302 (Found) status code MUST NOT be used in Offset Retrieving Procedure and Upload Cancellation Procedure responses. A 308 (Permanent Redirect) response MAY be persisted for all subsequent procedures. If client receives a 307 (Temporary Redirect) response in the Offset Retrieving Procedure, it MAY apply the redirection directly in the immediate subsequent Upload Transfer Procedure.

# Security Considerations

`Upload-Token` can be selected by the client which has no knowledge of tokens picked by other client, so uniqueness cannot be guaranteed. If the token is guessable, an attacker can append malicious data to ongoing uploads. To mitigate these issues, 256-bit cryptographically-secure random binary data is recommended for the token.

It is OPTIONAL for the server to partition upload tokens based on client identity established through other channels, such as Cookie or TLS client authentication. The client MAY relax the token strength if it is aware of server-side partitioning.

# IANA Considerations

This specification registers the following entry in the Permanent Message Header Field Names registry established by [RFC3864]:

Header field name: Upload-Token, Upload-Offset, Upload-Incomplete

Applicable protocol: http

Status: standard

Author/change controller: IETF

Specification: This document

Related information: n/a

This specification registers the following entry in the "HTTP Status Codes" registry:

Code: 104

Description: Upload Resumption Supported

Specification: This document

--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge.
