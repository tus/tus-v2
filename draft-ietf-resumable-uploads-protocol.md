title: tus - Resumable Uploads Protocol
abbrev: TODO - Abbreviation
docname: draft-ietf-resumable-uploads-protocol-latest
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

normative:
  RFC2119:

informative:


--- abstract

This document describes a mechanism which allows HTTP endpoints to add support for resumable uploads. It aims to address the issues around clients having to upload content from the start in case the original upload fails. HTTP servers to maintain stateful sessions with HTTP user agents. It aims to address some of the security and privacy considerations which have been identified in existing state management mechanisms, providing developers with a well-lit path towards our current understanding of best practice


--- middle

# Introduction

HTTP already provides resumable downloads using the `Range` header. However, on its own HTTP does not contain a standardized mechanism for resumable uploads. This has lead to a situation where many web services implement a proprietary solution for handling connection issues during file uploads. Such a scattered landscape makes it impossible to develop clients with resumable upload capabilities in a generic approach without focusing on specific, proprietary solutions. It also limits the benefits of resumable uploads to web services that can free up the resources to implement this.

Resuming a previously interrupted upload continues the data transfer where it left off, without the need to transfer the first part again. This capability is especially important in applications handling large files or operating in areas with unreliable network infrastructure. Upload interruptions can occur voluntarily, i.e. the end-user wants to pause the upload, or involuntarily, i.e. the network connection drops.

This protocol specifies an approach for clients and servers to implement resumable uploads on top of HTTP/1.1, HTTP/2 and HTTP/3, allowing the reuse of existing infrastructure.

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
     | POST (with Client-Upload-Token = foo)      |                                                 
     |------------------------------------------->|                                                 
     |                                            |                                                 
     |                                            | Reserve resources for Client-Upload-Token = foo 
     |                                            |------------------------------------------------ 
     |                                            |                                               | 
     |                                            |<----------------------------------------------- 
     |                                            |                                                 
     | Flow Interrupted                           |                                                 
     |------------------------------------------->|                                                 
     |                                            |                                          
          
```

 

2) If the connection to the server gets intrrupted during the Upload Creation Procedure or the Upload Appending Procedure, the client may want to resume the upload. Before this is possible, the client must know the amount of data that the server was able to receive before the connection got interrupted. To achieve this, the client uses the Offset Retriving Procedure to obtain the upload's offset.

```
+---------+                                      +---------+
| Client  |                                      | Server  |
+---------+                                      +---------+
     |                                                |
     | HEAD with Client-Upload-Token = foo            |
     |----------------------------------------------->|
     |                                                |
     |      200 OK with Upload-Resumption-Offset = 20 |
     |<-----------------------------------------------|
     |                                                |
```

3) After the Offset Retriving Procedure completes, the client can resume the upload by sending the remaining file content to the server, appending to the already stored data in the upload.

```
+---------+                                 +---------+
| Client  |                                 | Server  |
+---------+                                 +---------+
     |                                           |
     | PATCH with Client-Upload-Token = foo      |
     |------------------------------------------>|
     |                                           |
```

4) If the client is not interesting in completing the upload anymore, it can instruct the server to delete the upload and free all related resources using the Upload Cancellation Procedure.

```
+---------+                                  +---------+
| Client  |                                  | Server  |
+---------+                                  +---------+
     |                                            |
     | DELETE with Client-Upload-Token = foo      |
     |------------------------------------------->|
     |                                            |
     |                       200 OK on completion |
     |<-------------------------------------------|
     |                                            |
```


## Upload Creation Procedure

In order to initiate a resumable upload, the client MUST send a `POST` request to a known upload URL, under which endpoint the server supports resumable uploads as laid out in this document. Possible approaches for the client to obtain this upload URL as presented in the section Service Discovery. This `POST` request MUST include the `Client-Upload-Token` header and have it set to a unique value (TODO: More constraint to ensure its uniqueness).

The client SHOULD include the file's content in the request body and the server MUST attempt to store as much data as possible to minimize the data loss if the connection between the client and server get interrupted.

If the request completes successfully, the server MUST acknowledge it by responding with the `200 OK` status code.

```
POST /uploads HTTP/1.1
Host: example.org
Client-Upload-Token: abcdef
Content-Length: …

[file content]

HTTP/1.1 200 OK
```

## Offset Retriving Procedure

If an upload is interrupted, the client can attempt to fetch the offset of the incomplete upload by sending a HEAD request to the server with the same `Client-Upload-Token`. If the server has resources allocated for this token, it will send back a `200` status response with a header `Upload-Resumption-Offset` which indicates the resumption offset for the client. 

TODO: Request details
TODO: Should interrupt other running PATCH requests

```
HEAD /uploads HTTP/1.1
Host: example.org
Client-Upload-Token: abcdef
Content-Length: 0


HTTP/1.1 200 OK
Upload-Resumption-Offset: 100
```

## Upload Appending Procedure

Once the client gets the `Upload-Resumption-Offset` it can resume the orignal upload by starting the transfer from the value indicated in the `Upload-Resumption-Offset` header. The client must use the verb `PATCH` as an indication to the server that it is trying to append bytes to an existing file.

TODO: Request details
TODO: Should interrupt other running PATCH requests

```
PATCH /uploads HTTP/1.1
Host: example.org
Client-Upload-Token: abcdef
Upload-Resumption-Offset: 100

[file content]

HTTP/1.1 200 No Content
Upload-Offset: 200
```

## Upload Cancellation Procedure

If the client wants to stop the transfer before completion, it can optionally send a `DELETE` request to the server along with the `Client-Upload-Token` which is an indication that the client is no longer interested in uploading this body and the server can release resources associated with this token.

TODO: Request details
TODO: Should interrupt other running PATCH requests

```
DELETE /uploads HTTP/1.1
Host: example.org
Client-Upload-Token: abcdef
Content-Length: 0


HTTP/1.1 200 OK
```

# Header Fields

## The Client-Upload-Token Header Field

TODO - decide structured header format

The `Client-Upload-Token` is a new HTTP header being introduced as a part of this proposal. This header carries the token which uniquely identifies a resource that is being transferred. This token is generated by the client at the time of starting a new upload to a server. This token acts like a cookie in order to identify this transfer and will be helpful in cases when the client wants to retrieve the offset or delete the upload all together.

## The Upload-Resumption-Offset Header Field

TODO - decide structured header format

The `Upload-Resumption-Offset` is a new HTTP header being introduced as a part of this proposal. This header is calculated by the server in response to a `HEAD` request to get the upload offset for upload resumption.

If the server finds a resource associated with the given `Client-Upload-Token`, it returns the offset that the client needs to resume it's upload. 

If the server does not find a resources with the given `Client-Upload-Token`, it returns `0` in the header value indicating that the client must start the upload from scratch.

# Service Discovery


TODO Discovery using the `Alt-Svc` header and/or `HTTPSSVC` DNS record

(jmehta- I can't remember but I think from our last discussion we decided that we need to make this protocol client opt in. If so, we probably don't need this ?)


# Security Considerations

TODO Recommendation for HTTPS
(jmehta - from our previous conversation, I believe we are not going to talk about this since it is no different than POSTs happening on cleartext today)

TODO Recommendation for Authentication
TODO Recommendation for ensuring unique tokens

# IANA Considerations

This document has no IANA actions.


--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge.
