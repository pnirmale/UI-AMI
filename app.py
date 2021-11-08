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

	if re.search("windows",input_data["os_name"]):
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
			if re.search("access",line) and re.search("key",line) and re.search("secret",line) == None:
				result = tmp.find('=')
				access_key=tmp[result+1:]
			if re.search("key",line) and re.search("secret",line):
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
	try:
		data = json.loads(open("input.json").read())
	except:
		print("Please provide input.json")
		exit(0)
	lines=[]
	for i in data['CentOS']:
		print(i['urn'])
		lines.append(i['urn'])
	data2=[]
	try:
		data2 = json.loads(open("azure_credentials.json").read())
	except:
		print("Please provide azure_credentials.json")
	credentials=[]
	for i in data2['azure_credentials']:
		print(i['client_id'])
		credentials.append(i['client_id'])
		
	return render_template("azure.html", title="Azure",opt=lines,credential=credentials)
@app.route("/azure", methods=['POST'])
def azure_post():

	pairs={}
	

	prefix=request.form['vmname']
	pairs['prefix']=prefix
	user=request.form['user']
	pairs['user']=user
	password=request.form['Password']
	#pairs['password']=password
	region=request.form['region']
	pairs['location']=region
	os1=request.form['os']
	#pairs['os']=os
	ami=request.form['ami']
	cred=request.form['cred']
	#pairs['ami']=ami
	sku=""
	publisher=""
	version=""
	try:
		data = json.loads(open("input.json").read())
	except:
		print("Please provide input.json")
		exit(0)
	for i in data['CentOS']:
		if i['urn']==ami:
			pairs['offer']=i['offer']
			pairs['sku']=i['sku']
			pairs['publisher']=i['publisher']
			pairs['image_version']=i['version']
	data2=[]
	try:
		data2 = json.loads(open("azure_credentials.json").read())
	except:
		print("Please provide azure_credentials.json")
	credentials=[]
	for i in data2['azure_credentials']:
		if cred==i['client_id']:
			pairs['subscription_id']=i['subscription_id']
			pairs['tenant_id']=i['tenant_id']
			pairs['client_id']=cred
			
			
			pairs['client_secret']=i['client_secret']
		
    	
	cmd=generateApplyCommand(pairs)
	print(cmd)
	
	os.chdir("azure")
	
	os.system("terraform init")
	os.system (cmd)
	#os.system("terraform state rm \"aws_ami_from_instance.ami\" ")
	#destory =generateApplyCommand(pairs,"destory")
	#os.system(destory)
	return render_template("azure.html", title="Azure")

@app.route("/gcp")
def gcp():
    filename = 'images.txt'
    lines = []
    with open(filename) as f:
    	lines = f.readlines()
    return render_template("gcp.html", title="GCP",opt=lines)      

@app.route("/gcp",methods=["POST"])
def gcp_post():
	pairs={}
	boot_image=request.form['ami']
	file=request.files['file']

	filename=secure_filename(file.filename)
	cwd = os.getcwd()
	print(cwd)
	cwd+="/gcp"
	file.save(os.path.join(cwd, secure_filename(file.filename)))
	cmd=generateApplyCommand(pairs)
	os.chdir("gcp")
	os.system('terraform init')
	os.system(cmd)
	os.chdir("..")
	return render_template("gcp.html",title="gcp")


if __name__ == '__main__':
   app.run(debug = True ,port=2000)