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

# Upload Procedure

In order to initiate a resumable upload, the client MUST send a `POST` request to a known upload URL, under which endpoint the server supports resumable uploads as laid out in this document. Possible approaches for the client to obtain this upload URL as presented in the section Service Discovery.

TODO: Request details

# Service Discovery

TODO Discovery using the `Alt-Svc` header and/or `HTTPSSVC` DNS record

# Security Considerations

TODO Security


# IANA Considerations

This document has no IANA actions.



--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge.
