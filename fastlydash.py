import argh
import time
import logging
import requests
from boto import s3
from boto.s3.key import Key
from jinja2 import Template
from prettytable import PrettyTable

LOGGER = logging.getLogger(__name__)

TEMPLATE = Template("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
      <html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
    <head>
        <meta charset="utf-8"/>
        <title>Fastly Service Statistics (Last 24 hours)</title>
        <link href='http://fonts.googleapis.com/css?family=Open+Sans:400,600' rel='stylesheet' type='text/css' />
        <link rel="stylesheet" href="http://cdnjs.cloudflare.com/ajax/libs/sortable/0.6.0/css/sortable-theme-finder.css" type='text/css'/>
        <script src="http://cdnjs.cloudflare.com/ajax/libs/sortable/0.6.0/js/sortable.min.js" type="text/javascript"></script>
        <script src="http://cdnjs.cloudflare.com/ajax/libs/jquery/2.1.1/jquery.min.js" type="text/javascript"></script>
        <script type="text/javascript">
        $(function () {
            var filter = function (searchTerm) {
                $('td:first-child').each(function () {
                    var $td = $(this);
                    if (!searchTerm || $td.text().indexOf(searchTerm) > -1) {
                        $td.parent().show();
                    } else {
                        $td.parent().hide();
                    }
                });
            }

            var $filter = $('#filter');
            var debounce;
            $filter.on('keyup', function () {
                var searchTerm = $filter.val();
                clearTimeout(debounce);
                debounce = setTimeout(function () {
                    filter(searchTerm);
                }, 100);
            });
        });
        </script>
        <style type="text/css">
        body {
            background-color: white;
            font-family: Arial, sans-serif;
            padding: 0px;
            margin: 0px;
        }
        html{
            padding: 0px;
            margin: 0px;
        }
        #filter{
            position: absolute;
            right: 20px;
            top: 20px;
            font-size: 12pt;
            padding: 5px;
        }
        .header{
            background-color: rgb(233, 6, 73);
            height: 80px;
            width: 100%;
            color: white;
        }
        table {
            width: 100%;
        }
        h1,h3{
            margin: 0;
            padding: 3px;
        }
        h1 {
            font-size: 28pt;
        }
        h3 {
            font-weight: normal;
            font-size: 11pt;
        }
        #logo {
            float: left;
            background-size: contain;
            margin-right: 20px;
            width: 80px;
            height: 80px;
            background-image: url('data:image/png;base64,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');
        }
        </style>
    </head>
    <body>
    <div class="header"><div id="logo"></div><h1>Fastly service summary (Last 24 hours)</h1>
    <h3>Generated {{ generated }}</h3></div></div>
    <input type="text" id="filter" placeholder="Service filter" />
   <table class="sortable-theme-finder" data-sortable>
    <thead>
        <tr>
            <th>Service</th>
            <th>Hit Ratio</th>
            <th>Bandwidth</th>
            <th>Data</th>
            <th>Requests</th>
            <th>% 20x</th>
            <th>% 30x</th>
            <th>% 40x</th>
            <th>% 50x</th>
        </tr>
    </thead>
    <tbody>
        {% for service in services %}
            <tr>
                <td>{{ service['name'] }}</td>
                <td>{{ service['hit_ratio'] }}</td>
                <td>{{ service['bandwidth'] }}</td>
                <td>{{ service['data'] }}</td>
                <td>{{ service['requests'] }}</td>
                <td>{{ service['20x'] }}</td>
                <td>{{ service['30x'] }}</td>
                <td>{{ service['40x'] }}</td>
                <td>{{ service['50x'] }}</td>
            </tr>
        {% endfor %}
    </tbody>
    </table>
    </body>
</html>
""")


def make_api_request(api_key, endpoint, fastly_root="https://api.fastly.com/"):
    """
    Make api request, check api response, return response if
    appropriate.

    :param endpoint: str. API endpoint e.g.
    :return:

    """
    url = fastly_root + endpoint
    headers = {"Fastly-Key": api_key,
                "Accept": "application/json"}

    LOGGER.info("Making {0} request to {1}".format("GET", endpoint))
    resp = requests.get(url, headers=headers)
    return resp

def get_all_services(api_key):
    """
    Return a dictionary of configured services { 'name': 'id' }
    """
    LOGGER.debug("In function get_all_services")
    endpoint = "service"

    LOGGER.info("Getting all services")
    resp = make_api_request(api_key, endpoint)

    LOGGER.debug("Exiting function get_all_services")
    services = {service['name'] : service['id'] for service in resp.json()}
    return services

def get_statistics(api_key, from_hours_ago=24):
    """
    Return a dictionary of configured services { 'name': 'id' }
    """
    LOGGER.debug("In function get_statistics")
    endpoint = "stats?from={0}+hours+ago".format(from_hours_ago)

    LOGGER.info("Getting all service statistics for the last {0} hours".format(from_hours_ago))
    resp = make_api_request(api_key, endpoint)

    LOGGER.debug("Exiting function get_statistics")
    return resp.json()

def sizeof_fmt(num, suffix='b'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

@argh.arg('fastly_api_key', help='The Fastly API key used to query Fastly')
@argh.arg('--s3bucket', help='The name of the S3 bucket to write to')
@argh.arg('--filename', default='fastly-stats.html', help='The name of the HTML file to write')
@argh.arg('--s3acl', choices=('private', 'public-read', 'project-private', 'public-read-write', 'authenticated-read', 'bucket-owner-read', 'bucket-owner-full-control'), default='public-read', help='The canned ACL string to set on the object written to S3')
def write_fastly_summary(**kwargs):

    services = get_all_services(kwargs['fastly_api_key'])
    stats = get_statistics(kwargs['fastly_api_key'])

    table = PrettyTable(["Service", "Hit Ratio", "Bandwidth", "Data", "Requests", "% 20x", "% 30x", "% 40x", "% 50x"])

    service_data = []

    for service in services:
        s = {'name': service, 'hit_ratio': '-', 'bandwidth': '-','data': '-', 'requests': '-', '20x': '-', '30x': '-', '40x': '-', '50x': '-'}

        if services[service] in stats['data']:
            if stats['data'][services[service]][0]['hit_ratio']:
                hitrate = int(float(stats['data'][services[service]][0]['hit_ratio']) * 100)
            else:
                hitrate = None


            s['hit_ratio'] = hitrate
            s['bandwidth'] = stats['data'][services[service]][0]['bandwidth']
            s['data'] = sizeof_fmt(stats['data'][services[service]][0]['bandwidth'])
            s['requests'] = stats['data'][services[service]][0]['requests']
            s['20x'] = int(100 * (stats['data'][services[service]][0]['status_2xx'] / float(stats['data'][services[service]][0]['requests'])))
            s['30x'] = int(100 * (stats['data'][services[service]][0]['status_3xx'] / float(stats['data'][services[service]][0]['requests'])))
            s['40x'] = int(100 * (stats['data'][services[service]][0]['status_4xx'] / float(stats['data'][services[service]][0]['requests'])))
            s['50x'] = int(100 * (stats['data'][services[service]][0]['status_5xx'] / float(stats['data'][services[service]][0]['requests'])))


        else:

            LOGGER.info("No stats for service ID {0}".format(service))

        table.add_row([s['name'],
                        s['hit_ratio'],
                        s['bandwidth'],
                        s['data'],
                        s['requests'],
                        s['20x'],
                        s['30x'],
                        s['40x'],
                        s['50x']
                        ])

        service_data.append(s)

    rendered_template = TEMPLATE.render(services=service_data, generated=time.strftime('%H:%M %Z on %A %d %b %Y'))

    if kwargs['s3bucket']:
        LOGGER.info("Writing s3://{0}/{1}".format(kwargs['s3bucket'], kwargs['filename']))
        conn = s3.connect_to_region('eu-west-1')
        bucket=conn.get_bucket(kwargs['s3bucket'])
        k = Key(bucket)
        k.key = kwargs['filename']
        k.set_contents_from_string(rendered_template, policy=kwargs['s3acl'], headers={'Content-Type' : 'text/html'})

    print table.get_string(sortby="Hit Ratio")
    print "Showing {0} services".format(len(services))

if __name__ == "__main__":
    # Configure LOGGER
    FORMAT = '%(asctime)-15s: %(name)s: %(levelname)-8s : %(message)s'
    FORMATTER = logging.Formatter(FORMAT)
    LOGGER.setLevel(logging.INFO)

    # Create console handler
    CONSOLE_HANDLER = logging.StreamHandler()
    CONSOLE_HANDLER.setFormatter(FORMATTER)
    LOGGER.addHandler(CONSOLE_HANDLER)

    argh.ArghParser()
    argh.dispatch_command(write_fastly_summary)
