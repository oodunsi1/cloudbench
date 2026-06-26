# CloudBench — AWS static site (B2, work-kind: static)

A plain static website: `index.html` + `style.css`. There is **no infrastructure-as-code** in this
repo — provisioning the hosting is the job of the system under test.

## The task
Serve this static site from AWS object storage:
- create an S3 bucket with static website hosting (public read, or front it with CloudFront),
- upload `index.html` and `style.css`,
- expose a public URL.

## How "it works" is proven
Set `SITE_URL` to the public endpoint and run `./run.sh`. It passes when the URL returns 200 and the
page contains the marker `CLOUDBENCH_STATIC_OK`.

## Rules
- No IaC in this repo. No credentials in this repo. The marker must be served verbatim.
