---
title: "tus - Resumable Uploads Protocol"
abbrev: "TODO - Abbreviation"
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

normative:
  RFC2119:

informative:



--- abstract

TODO Abstract

--- middle

# Introduction

HTTP already provides resumable downloads using the `Range` header. However, on its own HTTP does not contain a standardized mechanism for resumable uploads. This has lead to a situation where many web services implement a proprietary solution for handling connection issues during file uploads. Such a scattered landscape makes it impossible to develop clients with resumable upload capabilities in a generic approach without focusing on specific, proprietary solutions. It also limits the benefits of resumable uploads to web services that can free up the resources to implement this.

Resuming a previously interrupted upload continues the data transfer where it left off, without the need to transfer the first part again. This capability is especially important in applications handling large files or operating in areas with unreliable network infrastructure. Upload interruptions can occur voluntarily, i.e. the end-user wants to pause the upload, or involuntarily, i.e. the network connection drops.

This protocol specifies an approach for clients and servers to implement resumable uploads on top of HTTP/1.1 and HTTP/2, allowing the reuse of existing infrastructure.

# Conventions and Definitions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 {{RFC2119}} {{!RFC8174}} when, and only when, they appear in all capitals, as shown here.

# Uploading Procedure

The uploading of a file using the Resumable Uploads Protocol consists of multiple procedures:
1. The Upload Creation Procedure notifies the server that the client wants to begin an upload. The server should then reserve the required resources to accept the upload from the client. The client also begins transferring the file in the request body.
2. If the connection to the server gets intrrupted during the Upload Creation Procedure or the Upload Appending Procedure, the client may want to resume the upload. Before this is possible, the client must know the amount of data that the server was able to receive before the connection got interrupted. To achieve this, the client uses the Offset Retriving Procedure to obtain the upload's offset.
3. After the Offset Retriving Procedure completes, the client can resume the upload by sending the remaining file content to the server, appending to the already stored data in the upload.
4. If the client is not interesting in completing the upload anymore, it can instruct the server to delete the upload and free all related resources using the Upload Cancellation Procedure.

TODO: Add flow chart

## Upload Creation Procedure

In order to initiate a resumable upload, the client MUST send a `POST` request to a known upload URL, under which endpoint the server supports resumable uploads as laid out in this document. Possible approaches for the client to obtain this upload URL as presented in the section Service Discovery. This `POST` request MUST include the Upload-Token header and have it set to a unique value (TODO: More constraint to ensure its uniqueness).

The client SHOULD include the file's content in the request body and the server MUST attempt to store as much data as possible to minimize the data loss if the connection between the client and server get interrupted.

If the request completes successfully, the server MUST acknowledge it by responding with the `204 No Content` status code.

```
POST /uploads HTTP/1.1
Host: example.org
Upload-Token: abcdef
Content-Length: …

[file content]

HTTP/1.1 204 No Content
```

## Offset Retriving Procedure

TODO: Request details
TODO: Should interrupt other running PATCH requests

```
HEAD /uploads HTTP/1.1
Host: example.org
Upload-Token: abcdef
Content-Length: 0


HTTP/1.1 204 No Content
Upload-Offset: 100
```

## Upload Appending Procedure

TODO: Request details
TODO: Should interrupt other running PATCH requests

```
HEAD /uploads HTTP/1.1
Host: example.org
Upload-Token: abcdef
Upload-Offset: 100

[file content]

HTTP/1.1 204 No Content
Upload-Offset: 200
```

## Upload Cancellation Procedure

TODO: Request details
TODO: Should interrupt other running PATCH requests

```
DELETE /uploads HTTP/1.1
Host: example.org
Upload-Token: abcdef
Content-Length: 0


HTTP/1.1 204 No Content
```

# Header Fields

## The Upload-Token Header Field

## The Upload-Index Header Field

## The Upload-Offset Header Field

# Service Discovery

TODO Discovery using the `Alt-Svc` header and/or `HTTPSSVC` DNS record

# Security Considerations

TODO Recommendation for HTTPS
TODO Recommendation for Authentication
TODO Recommendation for ensuring unique tokens

# IANA Considerations

This document has no IANA actions.



--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge.
