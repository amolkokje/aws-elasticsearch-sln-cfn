import os
import requests
from elasticsearch import Elasticsearch, RequestsHttpConnection

from requests_aws4auth import AWS4Auth
import boto3

aws_es_endpoint = 'search-ipesdomain-e2x7tyfwfiqxxmwy7a5s34ksqe.us-east-1.es.amazonaws.com'


def lambda_handler(event, context):
    print 'AMOL: event={}'.format(event)
    print 'AMOL: context={}'.format(context)
    print 'AMOL: ---> DELETE <---'


if __name__ == '__main__':
    lambda_handler(None, None)