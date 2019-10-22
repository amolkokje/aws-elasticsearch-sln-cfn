import os
import requests
from elasticsearch import Elasticsearch, RequestsHttpConnection

from requests_aws4auth import AWS4Auth
import boto3


def es_init():
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, os.environ['REGION'],
                       service, session_token=credentials.token)

    es_client = Elasticsearch( hosts=[{'host': os.environ['ES_ENDPOINT_HOST'],
                                       'port': int(os.environ['ES_ENDPOINT_PORT'])}],
                               http_auth=awsauth,
                               use_ssl=True,
                               verify_certs=True,
                               connection_class=RequestsHttpConnection)
    print 'AMOL-: SIGN: ES Init Done! Instance={}'.format(es_client)

    try:
        print 'AMOL-: SIGN: Indices={}'.format(es_client.indices.get_alias().keys())
        print 'AMOL-: SIGN: Indice Query PASS'
    except:
        print 'AMOL-: SIGN: Indice Query FAIL'

    document = {
        "title": "Moneyball",
        "director": "Bennett Miller",
        "year": "2011"
    }
    print 'AMOL: SIGN: Index Document={}'.format(es_client.index(index="movies", doc_type="doc", id="5", body=document))
    print 'AMOL: SIGN: Indexed Document={}'.format(es_client.get(index="movies", doc_type="doc", id="5"))


def lambda_handler(event, context):
    print 'AMOL: event={}'.format(event)
    print 'AMOL: context={}'.format(context)
    print 'AMOL: ---> INDEX <---'

    print 'ENVIRONMENT VARS:'
    for k, v in os.environ.iteritems():
        print '{}: [{}]'.format(k, v)

    es_init()


if __name__ == '__main__':
    lambda_handler(None, None)