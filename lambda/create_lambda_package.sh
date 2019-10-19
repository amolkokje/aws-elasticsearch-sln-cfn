# REF: https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html
# TODO: create a lambda layer with all the dependencies

VENV="lambda_venv"
CWD=$(pwd)
LAMBDA_FUNCTION=$1
LAMBDA_PACKAGE=$(echo $LAMBDA_FUNCTION | sed 's/.py/.zip/g')

LAMBDA_FUNCTION_FULL_PATH=$CWD/functions/$LAMBDA_FUNCTION
LAMBDA_PACKAGE_FULL_PATH=$CWD/packages/$LAMBDA_PACKAGE

echo "VENV=$VENV"
echo "FUNCTION=$LAMBDA_FUNCTION_FULL_PATH"
echo "PACKAGE=$LAMBDA_PACKAGE_FULL_PATH"




#!/bin/bash


# --------------------------
# Utils
# --------------------------

log()
{
    echo "$(date +"%T.%3"): [$1] $2"
}

cmd()
{
    CMD="$@"
    log "CMD" "$CMD"
    $CMD
}


# --------------------------
# Main
# --------------------------

####

log "MAIN" "delete old package"
cmd "rm $LAMBDA_PACKAGE_FULL_PATH"

log "MAIN" "remove existing and create new virtualenv"
cmd "rm -rf $VENV"
virtualenv $VENV

####

log "MAIN" "activate virtualenv, install python modules"

cd $VENV
source bin/activate

pip install -r $CWD/requirements.txt
#pip install boto3
#pip install requests
#pip install requests-aws4auth
#pip install Elasticsearch
#pip install urllib3
pip freeze

####

log "MAIN" "add python package dependencies from the virtualenv to a zip"

cmd "cd lib/python2.7/site-packages/"
cmd "zip -r9 $LAMBDA_PACKAGE_FULL_PATH ."

####

log "MAIN" "add function file to zip"

# have to be in the folder where the function exists, or else it will package with the whole folder
cmd "cd $CWD/functions"
cmd "zip -g ../packages/$LAMBDA_PACKAGE $LAMBDA_FUNCTION"

####

log "MAIN" "copy the lambda function to S3 bucket"

aws s3 cp $LAMBDA_PACKAGE_FULL_PATH s3://elasticsearch-lambda-functions

#aws lambda update-function-code --function-name test-function --zip-file fileb://function.zip
# aws lambda update-function-code --function-name <AWS_LAMBDA_FUNCTION_NAME> --zip-file fileb://<LAMBDA_ZIP>