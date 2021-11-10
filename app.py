from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
import json
import re
app = Flask(__name__)


@app.route("/", methods=['GET','POST'])
def view_home():
    return render_template("index.html", title="Home Page")

@app.route("/aws")
def aws():
	lines = json.loads(open("data/aws_images.json").read())
	return render_template("aws.html", title="Aws",opt=lines)   


def generateApplyCommand(pairs,st="apply"):
    str = "terraform " + st +" --auto-approve"
    for key,value in pairs.items():
    	str += " -var "+key+"=\""+value+"\""	
    return str

@app.route("/aws", methods=['POST'])
def aws_post():
	directory = "aws"

	input_data = eval(request.form.getlist('ami')[0])
	region = input_data.get("region")

	if re.search("windows",input_data["os_name"],re.IGNORECASE):
		directory = "aws-win"
	
	pairs={} 
	for key,v in input_data.items():
		if key == 'os_name':
			continue
		pairs[key] = v

	# configures providers.tf	
	if len(request.form.getlist("AlreadyConfigured")) == 0:
		file = request.files['file']
		filename = secure_filename(file.filename) 
		file.save(filename)

		lines =[]
		with open(filename) as f:
			lines = f.readlines()

		access_key=None 
		secret_key=None

		for line in lines:
			tmp = line.replace(' ','')[:-1]
			if re.search("access",line,re.IGNORECASE) and re.search("key",line,re.IGNORECASE) and re.search("secret",line,re.IGNORECASE) == None:
				result = tmp.find('=')
				access_key=tmp[result+1:]
			if re.search("key",line,re.IGNORECASE) and re.search("secret",line,re.IGNORECASE):
				result = tmp.find('=')
				secret_key=tmp[result+1:]

		if access_key == None or secret_key == None:
			print("Unable to configure aws keys")
			return render_template("aws.html",title="Aws")
		
		content = '''
			provider "aws" {{
				access_key = "{access_key}"
				secret_key = "{secret_key}"
				region = "{region}"
			}}
		'''
		os.chdir(directory)
		provider_file = open("providers.tf", "w")
		provider_file.write(content.format(access_key=access_key,secret_key=secret_key,region=region))
		provider_file.close()
		os.chdir("..")
		os.remove(filename)
	else:
		content = '''
			provider "aws" {{
				region = "{region}"
			}}
		'''
		os.chdir(directory)
		provider_file = open("providers.tf", "w")
		provider_file.write(content.format(region=region))
		provider_file.close()
		os.chdir("..")
		
	cmd=generateApplyCommand(pairs)
	print(cmd)
	
	os.chdir(directory)
	os.system("terraform init -upgrade")
	os.system (cmd)
	os.system("terraform state rm \"aws_ami_from_instance.ami\" ")
	cmd += " -destroy" # destroys infrastructure
	print(cmd)
	os.system(cmd)
	return render_template("aws.html", title="Aws")

@app.route("/azure",methods=['GET'])
def azure():
	data = json.loads(open("data/azure_images.json").read())

	lines=[]
	for i in data:
		lines.append({ 'offer' : i['offer'] + i['sku'], 'urn' : i['urn']})

	credentials=[]
	try:
		data2 = json.loads(open("data/azure_credentials.json").read())
		for i in data2['azure_credentials']:
			credentials.append(i['client_id'])
	except:
		print("Please provide azure_credentials.json")
		
	return render_template("azure.html", title="Azure",opt=lines,credential=credentials)

@app.route("/azure", methods=['POST'])
def azure_post():
	directory = 'azure'
	terraform_command_variables_and_value={}

	ami=eval(request.form.getlist('ami')[0])['urn']
	cred=request.form['cred']

	if re.search('windows',ami,re.IGNORECASE):
		directory = 'azure-win'

	urn_list = ami.split(':')

	terraform_command_variables_and_value['publisher'] = urn_list[0]
	terraform_command_variables_and_value['offer'] = urn_list[1]
	terraform_command_variables_and_value['sku'] = urn_list[2]
	terraform_command_variables_and_value['image_version'] = urn_list[3]
	
	try:
		data2 = json.loads(open("data/azure_credentials.json").read())
	except:
		print("Please provide azure_credentials.json")

	for i in data2['azure_credentials']:
		if cred==i['client_id']:

			subscription_id = i['subscription_id'].replace(' ','')
			client_id = i['client_id'].replace(' ','')
			client_secret = i['client_secret'].replace(' ','')
			tenant_id = i['tenant_id'].replace(' ','')

			terraform_command_variables_and_value['client_id'] = client_id
			terraform_command_variables_and_value['client_secret'] = client_secret
			terraform_command_variables_and_value['tenant_id'] = tenant_id

			content = '''
				provider "azurerm" {{
					features {{}}
					subscription_id   =  "{subscription_id}"
					client_id         =  "{client_id}"
					client_secret     =  "{client_secret}"
					tenant_id         =  "{tenant_id}"
				}}
			'''
			str = content.format(subscription_id =subscription_id,tenant_id=tenant_id,client_id =client_id,client_secret=client_secret)

			os.chdir(directory)
			provider_file = open('providers.tf','w')
			provider_file.write(str)
			provider_file.close()
			os.chdir('..')
    	
	cmd=generateApplyCommand(terraform_command_variables_and_value)
	print(cmd)
	
	os.chdir(directory)
	os.system("terraform init -upgrade")
	os.system (cmd)
	os.system("terraform state rm \"azurerm_image.my-image\" ")
	cmd += ' -destroy'
	os.system(cmd)
	return render_template("azure.html", title="Azure")


@app.route("/gcp")
def gcp():
	with open("data/gcp_images.txt") as f:
		lines=[]
		for line in f.readlines():
			lines.append(line[:-1])
	return render_template("gcp.html",title="gcp",opt=lines)

@app.route("/gcp",methods=["POST"])
def gcp_post():
	directory = "gcp"
	filename = None

	boot_image = request.form['ami']
	project = request.form['project']

	if re.search('windows',boot_image,re.IGNORECASE):
		directory = "gcp-win"

	pairs={}
	pairs["boot_image"] = boot_image

	if len(request.form.getlist("AlreadyConfigured")) == 0:
		file=request.files['file']
		filename = secure_filename(file.filename)
		file.save(os.path.join(os.getcwd() ,directory,filename))
		content = '''
			provider "google" {{
				project     = "{project}"
				credentials = "{filename}"
				region      = "asia-south1"
				zone        = "asia-south1-a"
			}}

			provider "google-beta" {{
				project     = "{project}"
				credentials = "{filename}"
				region      = "asia-south1"
				zone        = "asia-south1-a"
			}}
		'''
		print(content.format(project=project,filename=filename))
		os.chdir(directory)
		provider_file = open("providers.tf", "w")
		provider_file.write(content.format(project=project,filename=filename))
		provider_file.close()
		os.chdir("..")
	else:
		content = '''
			provider "google" {}

			provider "google-beta" {}
		'''
		os.chdir(directory)
		provider_file = open("providers.tf", "w")
		provider_file.write(content)
		provider_file.close()
		os.chdir("..")
	
	cmd=generateApplyCommand(pairs)
	print(cmd)
	os.chdir(directory)
	os.system('terraform init -upgrade')
	os.system(cmd)
	os.system("terraform state rm \"google_compute_machine_image.image\" ")
	cmd += " -destroy" # destroys infrastructure
	print(cmd)
	os.system(cmd)

	if len(request.form.getlist("AlreadyConfigured")) == 0:
		os.remove(filename)
		
	os.chdir("..")
	return render_template("gcp.html",title="gcp")


if __name__ == '__main__':
   app.run(debug = True ,port=2000)