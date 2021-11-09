from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
import json
import re
app = Flask(__name__)

#function to generate the terraform apply command with parameters
def generateApplyCommand(pairs,st="apply"):
    str = "terraform " + st +" --auto-approve"
    for key,value in pairs.items():
    	str += " -var "+key+"=\""+value+"\""	
    return str;


#home page route 
@app.route("/", methods=['GET','POST'])
def view_home():
    return render_template("index.html", title="Home Page")

#Aws route
@app.route("/aws")
def aws():
	list_of_ami_for_dropdown = json.loads(open("data/aws_images.json").read())
	return render_template("aws.html", title="Aws",opt=list_of_ami_for_dropdown)  

@app.route("/aws", methods=['POST'])
def aws_post():

    #default directory for unix system
	directory = "aws"

    #Form input for the ami
	input_data = eval(request.form.getlist('ami')[0])
	
	region = input_data.get("region")

    #Regular expression search for operating system name 
	if re.search("windows",input_data["os_name"]):
		directory = "aws-win"
	
	terraform_command_variables_and_value={} 

	for key,value in input_data.items():
		if key == 'os_name':
			continue
		terraform_command_variables_and_value[key] = value

	# configures providers.tf as user don't configured locally all the settings	
	if len(request.form.getlist("AlreadyConfigured")) == 0:
		file = request.files['file']
		filename = secure_filename(file.filename) 
		file.save(filename)

		contents_of_file =[]
		with open(filename) as f:
			contents_of_file = f.readlines()

		access_key=None 
		secret_key=None

        #extracting access_key and secret_key for aws credientials
		for line in contents_of_file:
			line_content_after_removing_newline_and_space= line.replace(' ','')[:-1]
			if re.search("access",line) and re.search("key",line) and re.search("secret",line) == None:
				result = line_content_after_removing_newline_and_space.find('=')
				access_key=line_content_after_removing_newline_and_space[result+1:]
			if re.search("key",line) and re.search("secret",line):
				result = line_content_after_removing_newline_and_space.find('=')
				secret_key=line_content_after_removing_newline_and_space[result+1:]

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
	
	#generate the command terraform apply 	
	cmd=generateApplyCommand(terraform_command_variables_and_value)
	print(cmd)

	#execute the terraform commands in respective directory
	"""
	os.chdir(directory)
	os.system("terraform init -upgrade")
	os.system (cmd)
	os.system("terraform state rm \"aws_ami_from_instance.ami\" ")
	cmd += " -destroy" # destroys infrastructure
	print(cmd)
	os.system(cmd)"""
	return render_template("aws.html", title="Aws")    




@app.route("/azure",methods=['GET'])
def azure():
	try:
		data = json.loads(open("data/azure_images.json").read())
	except:
		print("Please provide input.json")
		exit(0)
	lines=[]
	for key in data:
		for i in data[key]:
			print(i['urn'])
			lines.append(i['urn'])
	data2=[]
	try:
		data2 = json.loads(open("data/azure_credentials.json").read())
	except:
		print("Please provide azure_credentials.json")
	credentials=[]
	for i in data2['azure_credentials']:
		print(i['client_id'])
		credentials.append(i['client_id'])
		
	return render_template("azure.html", title="Azure",opt=lines,credential=credentials)
@app.route("/azure", methods=['POST'])
def azure_post():

	terraform_command_variables_and_value={}
	
    
	prefix=request.form['vmname']
	terraform_command_variables_and_value['prefix']=prefix
	
	
	ami=request.form['ami']
	cred=request.form['cred']
	
	sku=""
	publisher=""
	version=""
	#loading the ami name and publisher file for finding out sku publisher offer for azure image
	try:
		data = json.loads(open("data/azure_images.json").read())
	except:
		print("Please provide input.json")
		exit(0)
	#finding out which operating systenm is selected by the user comparing through the key in json file
	operating_system_selected_by_user=""	
	for key in data:
	    if ami.find(key)!=-1:
	       operating_system_selected_by_user=key
	       break
	print(operating_system_selected_by_user)

	for i in data[operating_system_selected_by_user]:
		if i['urn']==ami:
			terraform_command_variables_and_value['offer']=i['offer']
			terraform_command_variables_and_value['sku']=i['sku']
			terraform_command_variables_and_value['publisher']=i['publisher']
			terraform_command_variables_and_value['image_version']=i['version']
	
	try:
		data2 = json.loads(open("data/azure_credentials.json").read())
	except:
		print("Please provide azure_credentials.json")

	
	for i in data2['azure_credentials']:
		if cred==i['client_id']:
			terraform_command_variables_and_value['subscription_id']=i['subscription_id']
			terraform_command_variables_and_value['tenant_id']=i['tenant_id']
			terraform_command_variables_and_value['client_id']=cred
			
			
			terraform_command_variables_and_value['client_secret']=i['client_secret']
		
    	
	cmd=generateApplyCommand(terraform_command_variables_and_value)
	print(cmd)
	"""
	os.chdir("azure")
	os.system("terraform init")
	os.system (cmd)
	#os.system("terraform state rm \"aws_ami_from_instance.ami\" ")
	destory =generateApplyCommand(pairs,"destory")
	os.system(destory)"""
	return render_template("azure.html", title="Azure")



@app.route("/gcp")
def gcp():

	#DropDown in web page contains the name of ami that user can choose 
	ami_list_filename = 'data/gcp_images.txt'  #loading the name of file
	ami_names = []                    #list of name of ami names
	with open(ami_list_filename) as file:
		ami_names=file.readlines()                       #reading txt file line by line
	return render_template("gcp.html", title="Aws",opt=ami_names)   



@app.route("/gcp",methods=["POST"])
def gcp_post():
	directory = "gcp"
	filename = None

	boot_image = request.form['ami']
	words=boot_image.split( )
	boot_image=words[0]+"/"+words[1]

	project = request.form['project']

	if re.search('windows',boot_image):
		directory = "gcp-win"

	terraform_command_variables_and_value={}
	terraform_command_variables_and_value["boot_image"] = boot_image

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
	
	cmd=generateApplyCommand(terraform_command_variables_and_value)
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