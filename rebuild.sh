#! /bin/sh
pip3 install -r lambda/requirements.txt -t skill_env3
cp lambda/lambda_function.py skill_env3/lambda_function.py
cd skill_env3
zip lambda.zip -r *
cd ..
mv skill_env3/lambda.zip lambda.zip
rm -r skill_env3
python3 rebuild.py
rm lambda.zip