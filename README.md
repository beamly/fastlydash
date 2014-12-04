fastlydash
==========

A simple python script that produces a summary of all Fastly services over the past 24 hours, including:

- Service Name
- Hit Ratio
- Bandwidth
- Number of requests
- Percent of 20X, 30X, 40X, and 50X responses

Features
--------

- Filter by service name
- Clickable column headers to sort on an field

And optionally writes a pretty HTML page to S3.

![Screenshot](docs/screenshot.png)

Usage
=====

    usage: fastlydash.py [-h] [--s3bucket S3BUCKET] [--filename FILENAME]
                         [--s3acl {private,public-read,project-private,public-read-write,authenticated-read,bucket-owner-read,bucket-owner-    full-control}]
                         fastly_api_key
    
    Output a summary of all fastly distributions on stdout, and optionally write
    it as an HTML file to S3
    
    positional arguments:
      fastly_api_key        The Fastly API key used to query Fastly
    
    optional arguments:
      -h, --help            show this help message and exit
      --s3bucket S3BUCKET   The name of the S3 bucket to write to (default: None)
      --filename FILENAME   The name of the HTML file to write (default: fastly-
                            stats.html)
      --s3acl {private,public-read,project-private,public-read-write,authenticated-read,bucket-owner-read,bucket-owner-full-control}
                            The canned ACL string to set on the object written to
                            S3 (default: public-read)    
                            
Install all required dependancies in to a virtualenv:

    pip install -r requirements.txt
    
Run providing a Fastly API key, and optionally the name of an S3 bucket:

    python fastlydash.py <FASTLY_API_KEY> --s3bucket beamly-dashboards

By default the resulting stored HTML file will be publically readable - Use the --s3acl option to specify another canned ACL (Options shown above)

