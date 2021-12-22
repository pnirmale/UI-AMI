from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
import json
import re
import flask
from shelljob import proc
import subprocess as sp

app = Flask(__name__)

MIME_TYPE = 'text/javascript'

awsDefaultUsers = {
	'centos' : 'ec2-user',
	'debian' : 'admin',
	'fedora' : 'fedora',
	'rhel' : 'ec2-user',
	'suse' : 'ec2-user',
	'ubuntu' : 'ubuntu',
	'oracle' : 'ec2-user',
	'bitnami' : 'bitnami'
}

def getAwsDefaultUser(os_name):
	for key, value in awsDefaultUsers.items():
		if re.search(key,os_name,re.IGNORECASE):
			return value
	return None

def getAnsibleList():
	return {
		'windows' : ['Python3','NotepadPlusPlus','GoogleChrome'],
		'unix' : ['Git','Python3']
	}

@app.route("/", methods=['GET','POST'])
def view_home():
    return render_template("index.html", title="Home Page")

@app.route("/aws")
def aws():
	lines = json.loads(open("data/aws_images.json").read())
	regions = open("regions/aws.txt")
	return render_template("aws.html", title="Aws",opt=lines,ansibleList = getAnsibleList(),regions=regions)   

def show_real_time_output(directory,initialize_proc,terraform_apply_proc,terraform_state_rm_proc,demo_proc,terraform_destroy_proc,applyCommand,remove_image_from_state_file_command,destroyCommand,alreadyConfigured=False):
		
		os.chdir(directory)
		initialize_proc.run('terraform init')

		while initialize_proc.is_pending():
			lines = initialize_proc.readlines()
			for proc, line in lines:
				yield line+"\n".encode("utf-8")

		terraform_apply_proc.run(applyCommand)

		while terraform_apply_proc.is_pending():
			lines = terraform_apply_proc.readlines()
			for proc, line in lines:
				yield line

		terraform_state_rm_proc.run(remove_image_from_state_file_command)

		while terraform_state_rm_proc.is_pending():
			lines = terraform_state_rm_proc.readlines()
			for proc,line in lines:
				yield line

		if re.search('azure',directory,re.IGNORECASE):
			demo_proc.run('terraform state rm "azurerm_resource_group.for_image_storage"')

			while demo_proc.is_pending():
				lines = demo_proc.readlines()
				for proc,line in lines:
					yield line
		
		terraform_destroy_proc.run(destroyCommand)

		while terraform_destroy_proc.is_pending():
			lines = terraform_destroy_proc.readlines()
			for proc, line in lines:
				yield line

		if re.search("aws",directory,re.IGNORECASE) and alreadyConfigured:
			del os.environ['AWS_ACCESS_KEY_ID']
			del os.environ['AWS_SECRET_ACCESS_KEY']
				
		os.chdir('..')

def generateApplyCommand(terraform_command_variables_and_value,st="apply"):
	str = "terraform " + st +" --auto-approve  -lock=false "
	for key,value in terraform_command_variables_and_value.items():
		str += " -var "+key+"=\""+value+"\""	
	return str

def generateAnsibleCommand(list_of_vars):
	cmd = "--extra-vars '"
	for key,value in list_of_vars.items():
			cmd += key + "=true "
	return cmd + "'"

@app.route("/aws", methods=['POST'])
def aws_post():
	directory = "aws"

	list_softwares = json.loads(json.dumps(request.form))
	alreadyConfigured = request.form.getlist('alreadyConfigured')[0]

	try:
		list_softwares.pop('ami')
	except:
		print('a')
		
	input_data = eval(request.form.getlist('ami')[0])
	region = request.form.getlist('region')[0]

	print(region)

	if re.search("windows",input_data["os_name"],re.IGNORECASE):
		directory = "aws-win"
	
	terraform_command_variables_and_value={}
	terraform_command_variables_and_value['ansible_command'] = generateAnsibleCommand(list_softwares) 
	terraform_command_variables_and_value['user'] = getAwsDefaultUser(input_data['os_name'])
	terraform_command_variables_and_value['region'] = region

	for key,v in input_data.items():
		if key == 'os_name':
			continue
		terraform_command_variables_and_value[key] = v

	applyCommand=generateApplyCommand(terraform_command_variables_and_value)
	destroyCommand= generateApplyCommand(terraform_command_variables_and_value,"destroy")
	remove_image_from_state_file_command = 'terraform state rm "aws_ami_from_instance.ami"'

	print(applyCommand,destroyCommand)

	return flask.Response( show_real_time_output(directory,proc.Group(),proc.Group(),proc.Group(),proc.Group(),proc.Group(),applyCommand,remove_image_from_state_file_command,destroyCommand,alreadyConfigured), mimetype= MIME_TYPE )

@app.route("/azure",methods=['GET'])
def azure():
	data = json.loads(open("data/azure_images.json").read())
	regions = open("regions/azure.txt")

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
		
	return render_template("azure.html", title="Azure",opt=lines,credential=credentials,ansibleList = getAnsibleList(),regions=regions)

@app.route('/location',methods=['POST'])
def location():
	print("req received...")
	regions = open("regions/aws.txt")
	
	alreadyConfigured = len(request.form.getlist('AlreadyConfigured'))

	region = request.form.getlist('region')[0].rstrip()
	vmname = request.form.getlist('vmname')[0].rstrip()
	vmname = vmname.replace(' ','*')
	vmname = vmname + '*'

	print(region,vmname)

	# configures AWS Keys to ENV variables	
	if alreadyConfigured == 0:
		file = request.files['file']
		filename = secure_filename(file.filename) 
		file.save(filename)

		lines =[]
		with open(filename) as f:
			lines = f.readlines()

		access_key = None 
		secret_key = None

		for line in lines:
			tmp = line.replace(' ','')[:-1]
			if re.search("access",line,re.IGNORECASE) and re.search("key",line,re.IGNORECASE) and re.search("secret",line,re.IGNORECASE) == None:
				result = tmp.find('=')
				access_key=tmp[result+1:]
			if re.search("key",line,re.IGNORECASE) and re.search("secret",line,re.IGNORECASE):
				result = tmp.find('=')
				secret_key=tmp[result+1:]

		if access_key == None or secret_key == None:
			return render_template("aws.html",error='Unable to configure aws keys', title="Aws",ansibleList = getAnsibleList(),regions=regions,selectedRegion=region,vmname=vmname) 

		os.environ["AWS_ACCESS_KEY_ID"] = access_key
		os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key

		os.remove(filename)

	images = sp.getoutput('aws ec2 describe-images --region '+ region +' --filters "Name=name,Values='+ vmname +'"')

	try:
		images  = json.loads(images)
	except:
		file1 = open("logs.txt",'w')
		file1.write(images)
		file1.close()
		return render_template("aws.html",error='Error Occured while fetching AMI\'s ...Please check logs.txt file for error details', title="Aws",ansibleList = getAnsibleList(),regions=regions,selectedRegion=region,vmname=vmname)   

	finalData = []

	for ami in images['Images']:
		finalData.append({
			'ami_id' : ami['ImageId'],
			'os_name' : ami['Name'] + ' PlatFormDetails : ' + ami['PlatformDetails']
		})

	return render_template("aws.html", title="Aws",ansibleList = getAnsibleList(),regions=regions,selectedRegion=region,vmname=vmname,opt=finalData,alreadyConfigured=alreadyConfigured)   


@app.route('/az_location',methods=['POST'])
def az_location():
	print("req received...")
	region = request.form.getlist('region')[0].rstrip()
	vmname = request.form.getlist('vmname')[0].rstrip()

	images = sp.getoutput('az vm image list --all --output json --location '+region+' --offer '+vmname)
	images = eval(images)

	print(len(images))
	for a in images:
		print(a)
		break

	data = json.loads(open("data/azure_images.json").read())
	regions = open("regions/azure.txt")

	credentials=[]
	try:
		data2 = json.loads(open("data/azure_credentials.json").read())
		for i in data2['azure_credentials']:
			credentials.append(i['client_id'])
	except:
		print("Please provide azure_credentials.json")
		
	return render_template("azure.html", title="Azure",selectedRegion=region,vmname=vmname,opt=images,credential=credentials,ansibleList = getAnsibleList(),regions=regions)

@app.route("/azure", methods=['POST'])
def azure_post():
	directory = 'azure'

	list_softwares = json.loads(json.dumps(request.form))
	try:
		list_softwares.pop('ami')
		list_softwares.pop('cred')
	except:
		print('a')

	terraform_command_variables_and_value={}
	terraform_command_variables_and_value['ansible_command'] = generateAnsibleCommand(list_softwares) 

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
			
		applyCommand=generateApplyCommand(terraform_command_variables_and_value)
		destroyCommand=generateApplyCommand(terraform_command_variables_and_value,"destroy")
		remove_image_from_state_file_command = 'terraform state rm "azurerm_image.my-image"'
		print(applyCommand,destroyCommand)

		return flask.Response(show_real_time_output(directory,proc.Group(),proc.Group(),proc.Group(),proc.Group(),proc.Group(),applyCommand,remove_image_from_state_file_command,destroyCommand), mimetype= MIME_TYPE )
	except:
		print("Please provide azure_credentials.json")
		return render_template('error.html')

@app.route("/gcp")
def gcp():
	regions = open('regions/gcp.txt')
	standardVms = sp.getoutput('gcloud compute images list --format="json"')
	standardVms = eval(standardVms)

	finalData = []
	for image in standardVms:
		txt = image['selfLink']
		finalData.append(txt[txt.index("projects/") + 9:txt.index("/", txt.index("projects/") + 9 )] + txt[txt.rfind("/"):len(txt)])

	return render_template("gcp.html",title="gcp",opt=finalData,ansibleList = getAnsibleList(),regions=regions)

@app.route("/gcp_location",methods=['POST'])
def gcp_location():
	error = None
	finalData = []

	regions = open('regions/gcp.txt')
	project = request.form.getlist('projectToSearch')[0]

	vms = sp.getoutput('gcloud compute images list --project="'+project+'" --format="json"')

	try:
		vms = eval(vms)
	except:
		error = "The resource 'projects/" + project+ " was not found"

	if error is None:
		for image in vms:
			txt = image['selfLink']
			finalData.append(txt[txt.index("projects/") + 9:txt.index("/", txt.index("projects/") + 9 )] + txt[txt.rfind("/"):len(txt)])

	return render_template("gcp.html",title="gcp",error=error,selectedProject=project,opt=finalData,ansibleList = getAnsibleList(),regions=regions)


@app.route("/gcp",methods=["POST"])
def gcp_post():
	directory = "gcp"
	filename = None

	boot_image = request.form['ami']
	project = request.form['project']

	list_softwares = json.loads(json.dumps(request.form))
	try:
		list_softwares.pop('project')
		list_softwares.pop('ami')
		list_softwares.pop('AlreadyConfigured')
	except:
		print('a')

	if re.search('windows',boot_image,re.IGNORECASE):
		directory = "gcp-win"

	terraform_command_variables_and_value={}
	terraform_command_variables_and_value["boot_image"] = boot_image
	terraform_command_variables_and_value['ansible_command'] = generateAnsibleCommand(list_softwares) 

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
	
	applyCommand=generateApplyCommand(terraform_command_variables_and_value)
	destroyCommand= generateApplyCommand(terraform_command_variables_and_value,"destroy")
	remove_image_from_state_file_command = 'terraform state rm "google_compute_machine_image.image"'
	print(applyCommand,destroyCommand)

	return flask.Response( show_real_time_output(directory,proc.Group(),proc.Group(),proc.Group(),proc.Group(),proc.Group(),applyCommand,remove_image_from_state_file_command,destroyCommand), mimetype= MIME_TYPE )

if __name__ == '__main__':
   app.config["TEMPLATES_AUTO_RELOAD"] = True
   app.run(debug = True ,port=2000)