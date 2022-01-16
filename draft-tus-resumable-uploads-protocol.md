---
title: tus - Resumable Uploads Protocol
abbrev: Resumable Uploads
docname: draft-tus-resumable-uploads-protocol-latest
category: std

ipr: trust200902
area: ART
workgroup: HTTP
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
  -
    ins: J. Mehta
    name: Jiten Mehta
    organization: Apple Inc.
    email: jmehta@apple.com
  -
    ins: G. Zhang
    name: Guoye Zhang
    organization: Apple Inc.
    email: guoye_zhang@apple.com
  -
    ins: L. Pardue
    name: Lucas Pardue
    organization: Cloudflare
    email: lucaspardue.24.7@gmail.com

  -
    ins: S. Matsson
    name: Stefan Matsson
    organization: JellyHive
    email: s.matsson@gmail.com

normative:
  RFC2119:

informative:


--- abstract

This document describes a mechanism which allows HTTP endpoints to add support for resumable uploads. It aims to address the issues around clients having to upload content from the start in case the original upload fails.

--- middle

# Introduction

HTTP {{!HTTP=I-D.ietf-httpbis-semantics}} already provides resumable downloads using the `Range` header. However, on its own HTTP does not contain a standardized mechanism for resumable uploads. This has lead to a situation where many web services implement a proprietary solution for handling connection issues during file uploads. Such a scattered landscape makes it impossible to develop clients with resumable upload capabilities in a generic approach without focusing on specific, proprietary solutions. It also limits the benefits of resumable uploads to web services that can free up the resources to implement this.

Resuming a previously interrupted upload continues the data transfer where it left off, without the need to transfer the first part again. This capability is especially important in applications handling large files or operating in areas with unreliable network infrastructure. Upload interruptions can occur voluntarily, i.e. the end-user wants to pause the upload, or involuntarily, i.e. the network connection drops.

This protocol specifies an approach for clients and servers to implement resumable uploads on top of HTTP/1.1, HTTP/2 and HTTP/3, allowing the reuse of existing infrastructure. It also allows clients to upgrade regular uploads automatically to resumable uploads.

# Conventions and Definitions

{::boilerplate bcp14-tagged}

The terms byte sequence, Item, string, sf-binary, sf-boolean, sf-integer, sf-string, and sf-token are imported from
{{!STRUCTURED-FIELDS=RFC8941}}.

The terms client and server are imported from {{HTTP}}.

# Uploading Overview

The uploading of a file using the Resumable Uploads Protocol consists of multiple procedures:

1) The Upload Transfer Procedure ({{upload-transfer}}) can be used to notify the server that the client wants to begin an upload. The server should then reserve the required resources to accept the upload from the client. The client also begins transferring the file in the request body. An informational response can be sent to the client to signal the support of resumable upload on the server.

~~~
Client                                  Server
|                                            |
| POST with Upload-Token                     |
|------------------------------------------->|
|                                            |
|                                            | Reserve resources
|                                            | for Upload-Token
|                                            |------------------
|                                            |                 |
|                                            |<-----------------
|                                            |
|            104 Upload Resumption Supported |
|<-------------------------------------------|
|                                            |
| Flow Interrupted                           |
|------------------------------------------->|
|                                            |
~~~
{: #fig-upload-transfer-procedure-init title="Upload Transfer Procedure Initiation"}

2) If the connection to the server gets interrupted during the Upload Transfer Procedure, the client may want to resume the upload. Before this is possible, the client must know the amount of data that the server was able to receive before the connection got interrupted. To achieve this, the client uses the Offset Retrieving Procedure to obtain the upload's offset.

~~~
Client                                      Server
|                                                |
| HEAD with Upload-Token                         |
|----------------------------------------------->|
|                                                |
|              204 No Content with Upload-Offset |
|<-----------------------------------------------|
|                                                |
~~~
{: #fig-offset-retrieving-procedure title="Offset Retrieving Procedure"}

3) After the Offset Retrieving Procedure ({{offset-retrieving}}) completes, the client can resume the upload by sending the remaining file content to the server, appending to the already stored data in the upload.

~~~
Client                                      Server
|                                                |
| POST with Upload-Token and Upload-Offset       |
|----------------------------------------------->|
|                                                |
|                      201 Created on completion |
|<-----------------------------------------------|
|                                                |
~~~
{: #fig-resuming-upload title="Resuming Upload"}

4) If the client is not interesting in completing the upload anymore, it can instruct the server to delete the upload and free all related resources using the Upload Cancellation Procedure ({{upload-cancellation}}).

~~~
Client                                      Server
|                                                |
| DELETE with Upload-Token                       |
|----------------------------------------------->|
|                                                |
|                   204 No Content on completion |
|<-----------------------------------------------|
|                                                |
~~~
{: #fig-upload-cancellation-procedure title="Upload Cancellation Procedure"}

For advanced use cases, the client is allowed to upload incomplete chunks of a file to the server sequentially.

1) If the client is aware that the server supports resumable upload, it can use the Upload Transfer Procedure with the `Upload-Incomplete` header to start an upload.

~~~
Client                                      Server
|                                                |
| POST with Upload-Token, Upload-Offset,         |
| and Upload-Incomplete                          |
|----------------------------------------------->|
|                                                |
|             201 Created with Upload-Incomplete |
|              on completion                     |
|<-----------------------------------------------|
|                                                |
~~~
{: #fig-upload-cancellation-procedure-usage title="Upload Transfer Procedure Usage"}


2) The last chunk of the upload does not have the `Upload-Incomplete` header.

~~~
Client                                      Server
|                                                |
| POST with Upload-Token and Upload-Offset       |
|----------------------------------------------->|
|                                                |
|                      201 Created on completion |
|<-----------------------------------------------|
|                                                |
~~~
{: #fig-upload-cancellation-procedure-last-chunk title="Upload Transfer Procedure Last Chunk"}


# Upload Transfer Procedure {#upload-transfer}

The Upload Transfer Procedure is intended for transferring the data chunk. As such, it can be used for either resuming an existing upload, or starting a new upload. A limited form of this procedure MAY be used by the client to start a new upload without the knowledge of server support.

This procedure is designed to be compatible with a regular upload. Therefore all methods are allowed with the exception of `GET`, `HEAD`, `DELETE`, and `OPTIONS`. All response status codes are allowed. The client is RECOMMENDED to use the `POST` method if not otherwise intended. The server MAY only support a limited number of methods.

The client MUST use the same method throughout an entire upload. The server SHOULD reject the attempt to resume an upload with a different method with `400 (Bad Request)` response.

The request MUST include the `Upload-Token` header field ({{upload-token}}) which uniquely identifies an upload. The client MUST NOT reuse the token for a different upload.

When resuming an upload, the `Upload-Offset` header field ({{upload-offset}}) MUST be set to the resumption offset. The resumption offset 0 indicates a new upload. The absence of the `Upload-Offset` header field implies the resumption offset of 0.

If the end of the request body is not the end of the upload, the `Upload-Incomplete` header field ({{upload-incomplete}}) MUST be set to true.

The client MAY send the metadata of the file using headers such as `Content-Type` (see {{Section 8.3 of HTTP}} and `Content-Disposition` {{!RFC6266}} when starting a new upload. It is OPTIONAL for the client to repeat the metadata when resuming an upload.

If the server does not consider the upload associated with the token in the `Upload-Token` header field active, but the resumption offset is non-zero, it MUST respond with 404 (Not Found) status code.

The client MUST NOT perform multiple Upload Transfer Procedures ({{upload-transfer}}) for the same token in parallel to avoid race conditions and data loss or corruption. The server is RECOMMENDED to take measures to avoid parallel Upload Transfer Procedures: The server MAY terminate any ongoing Upload Transfer Procedure ({{upload-transfer}}) for the same token. Since the client is not allowed to perform multiple transfers in parallel, the server can assume that the previous attempt has already failed. Therefore, the server MAY abruptly terminate the previous HTTP connection or stream.

If the offset in the `Upload-Offset` header field does not match the value 0, the offset provided by the immediate previous Offset Retrieving Procedure ({{offset-retrieving}}), or the end offset of the immediate previous incomplete transfer, the server MUST respond with `400 (Bad Request)` status code.

If the request completes successfully and the entire upload is complete, the server MUST acknowledge it by responding with a successful status code between 200 and 299 (inclusive). Server is RECOMMENDED to use `201 (Created)` response if not otherwise specified. The response MUST NOT include the `Upload-Incomplete` header with the value of true.

If the request completes successfully but the entire upload is not yet complete indicated by the `Upload-Incomplete` header, the server MUST acknowledge it by responding with the `201 (Created)` status code and the `Upload-Incomplete` header set to true.

~~~ example
:method: POST
:scheme: https
:authority: example.com
:path: /upload
upload-token: :SGVs…SGU=:
[content]

:status: 104

:status: 201
~~~

~~~ example
:method: POST
:scheme: https
:authority: example.com
:path: /upload
upload-token: :SGVs…SGU=:
upload-offset: 0
upload-incomplete: ?1
[partial content]

:status: 201
upload-incomplete: ?1
~~~

The client MAY automatically attempt upload resumption when the connection is terminated unexpectedly, or if a server error status code between 500 and 599 (inclusive) is received. The client SHOULD NOT automatically retry if a client error status code between 400 and 499 (inclusive) is received.

## Feature Detection

If the client has no knowledge of whether the server supports resumable upload, the Upload Transfer Procedure MAY be used with some additional constraints. In particular, the `Upload-Offset` header field ({{upload-offset}}) and the `Upload-Incomplete` header field ({{upload-incomplete}}) MUST NOT be sent in the request if the server support is unclear. This allows the upload to function as if it is a regular upload.

If the server detects the Upload Transfer Procedure with neither the `Upload-Offset` header nor the `Upload-Incomplete` header, and it supports resumable upload, an informational response with `104 (Upload Resumption Supported)` status MAY be sent to the client while the request body is being uploaded.

The client MUST NOT attempt to resume an upload if it did not receive the `104 (Upload Resumption Supported)` informational response, and it does not have other signals of whether the server supporting resumable upload.

If the client is aware of the server support, it SHOULD start an upload with the `Upload-Offset` header set to 0 in order to prevent the unnecessary informational response.

# Offset Retrieving Procedure {#offset-retrieving}

If an upload is interrupted, the client MAY attempt to fetch the offset of the incomplete upload by sending a `HEAD` request to the server with the same `Upload-Token` header field ({{upload-token}}). The client MUST NOT initiate this procedure without the knowledge of server support.

The request MUST use the `HEAD` method and include the `Upload-Token` header. The request MUST NOT include the `Upload-Offset` header or the `Upload-Incomplete` header. The server MUST reject the request with the `Upload-Offset` header or the `Upload-Incomplete` header by sending a `400 (Bad Request)` response.

If the server considers the upload associated with this token active, it MUST send back a `204 (No Content)` response with a header `Upload-Offset` which indicates the resumption offset for the client.

The client MUST NOT perform the Offset Retrieving Procedure ({{offset-retrieving}}) while the Upload Transfer Procedures ({{upload-transfer}}) is in progress.

The offset MUST be accepted by a subsequent Upload Transfer Procedure ({{upload-transfer}}). Due to network delay and reordering, the server might still be receiving data from an ongoing transfer for the same token, which in the client perspective has failed. The server MAY terminate any transfers for the same token before sending the response by abruptly terminating the HTTP connection or stream. Alternatively, the server MAY keep the ongoing transfer alive but ignore further bytes received past the offset.

The client MUST NOT start more than one Upload Transfer Procedures ({{upload-transfer}}) based on the resumption offset from a single Offset Retrieving Procedure ({{offset-retrieving}}).

The response SHOULD include `Cache-Control: no-store` header to prevent HTTP caching.

If the server does not consider the upload associated with this token active, it MUST respond with `404 (Not Found)` status code.

~~~
:method: HEAD
:scheme: https
:authority: example.com
:path: /upload
upload-token: :SGVs…SGU=:

:status: 204
upload-offset: 100
cache-control: no-store
~~~

The client MAY automatically start uploading from the beginning using Upload Transfer Procedure ({{upload-transfer}}) if `404 (Not Found)` status code is received. The client SHOULD NOT automatically retry if a status code other than 204 and 404 is received.

# Upload Cancellation Procedure {#upload-cancellation}

If the client wants to terminate the transfer without the ability to resume, it MAY send a `DELETE` request to the server along with the `Upload-Token` which is an indication that the client is no longer interested in uploading this body and the server can release resources associated with this token. The client MUST NOT initiate this procedure without the knowledge of server support.

The request MUST use the `DELETE` method and include the `Upload-Token` header. The request MUST NOT include the `Upload-Offset` header or the `Upload-Incomplete` header. The server MUST reject the request with the `Upload-Offset` header or the `Upload-Incomplete` header by sending a `400 (Bad Request)` response.

If the server has successfully deactivated this token, it MUST send back a `204 (No Content)` response.

The server MAY terminate any ongoing Upload Transfer Procedure ({{upload-transfer}}) for the same token before sending the response by abruptly terminating the HTTP connection or stream.

If the server does not consider the upload associated with this token active, it MUST respond with `404 (Not Found)` status code.

If the server does not support cancellation, it MUST respond with `405 (Method Not Allowed)` status code.

~~~ example
:method: DELETE
:scheme: https
:authority: example.com
:path: /upload
upload-token: :SGVs…SGU=:

:status: 204
~~~

# Header Fields

## Upload-Token

The `Upload-Token` request header field is an Item Structured Header (see {{Section 3.3 of STRUCTURED-FIELDS}}). Its value MUST be a byte sequence. Its ABNF is

~~~ abnf
Upload-Token = sf-binary
~~~

If not otherwise specified by the server, the client is RECOMMENDED to use 256-bit (32 bytes) cryptographically-secure random binary data as the value of the `Upload-Token`, in order to ensure that it is globally unique and non-guessable.

A conforming implementation MUST be able to handle a `Upload-Token` field value of at least 128 octets.

## Upload-Offset

The `Upload-Offset` request and response header field is an Item Structured Header. Its value MUST be an integer. Its ABNF is

~~~ abnf
Upload-Offset = sf-integer
~~~

## Upload-Incomplete

The `Upload-Incomplete` request and response header field is an Item Structured Header. Its value MUST be a boolean. Its ABNF is

~~~ abnf
Upload-Incomplete = sf-boolean
~~~

The value of the `Upload-Incomplete` header MUST be true.

# Redirection

The `301 (Moved Permanently)` status code and the `302 (Found)` status code MUST NOT be used in Offset Retrieving Procedure ({{offset-retrieving}}) and Upload Cancellation Procedure ({{upload-cancellation}}) responses. A `308 (Permanent Redirect)` response MAY be persisted for all subsequent procedures. If client receives a `307 (Temporary Redirect)` response in the Offset Retrieving Procedure ({{offset-retrieving}}), it MAY apply the redirection directly in the immediate subsequent Upload Transfer Procedure ({{upload-transfer}}).

# Security Considerations

The tokens inside the `Upload-Token` header field can be selected by the client which has no knowledge of tokens picked by other client, so uniqueness cannot be guaranteed. If the token is guessable, an attacker can append malicious data to ongoing uploads. To mitigate these issues, 256-bit cryptographically-secure random binary data is recommended for the token.

It is OPTIONAL for the server to partition upload tokens based on client identity established through other channels, such as Cookie or TLS client authentication. The client MAY relax the token strength if it is aware of server-side partitioning.

# IANA Considerations

This specification registers the following entry in the Permanent Message Header Field Names registry established by {{!RFC3864}}:

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
