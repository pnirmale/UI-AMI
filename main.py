from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
import json
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

@app.route("/aws")
def aws():
	#DropDown in web page contains the name of ami that user can choose 
	ami_list_filename = 'images.txt'  #loading the name of file
	ami_names = []                    #list of name of ami names
	with open(ami_list_filename) as file:
		ami_names=file.readlines()                       #reading txt file line by line
	return render_template("aws.html", title="Aws",opt=ami_names)   





@app.route("/aws", methods=['POST'])
def aws_post():

	terraform_command_variables_and_value={}
	
	#Receving file input form the user for the credentials
	file = request.files['file']
	filename = secure_filename(file.filename) 
	file.save(filename)
	lines_in_file =[]
	with open(filename) as f:
		lines_in_file = f.readlines()

	line_number_in_txt_file = 0
	num_of_line_in_txt_file=len(lines_in_file)
	for line in lines_in_file:
		if line_number_in_txt_file!=num_of_line_in_txt_file-1:
			contents_of_line_after_removing_newline_character=line[:-1]
			result = contents_of_line_after_removing_newline_character.find('=')
			terraform_command_variables_and_value[contents_of_line_after_removing_newline_character[0:result]]=contents_of_line_after_removing_newline_character[result+1:]

		else:	
		    result = line.find('=')
		    contents_of_line_after_removing_newline_character[line[0:result]]=line[result+1:]
		
	prefix=request.form['vmname']
	terraform_command_variables_and_value['prefix']=prefix
	
	user=request.form['user']
	terraform_command_variables_and_value['user']=user
	
	password=request.form['Password']
	#pairs['password']=password
	
	region=request.form['region']
	terraform_command_variables_and_value['region']=region
	
	subnet_cidr_block=request.form['scidr']
	terraform_command_variables_and_value['subnet_cidr_block']=subnet_cidr_block
	
	vpc_cidr_block=request.form['vcidr']
	terraform_command_variables_and_value['vpc_cidr_block']=vpc_cidr_block
	#os=request.form['os']
	#pairs['os']=os
	ami=request.form['ami']

	#pairs['ami']=ami
	
	#Generate the command to execute in terraform directory
	cmd=generateApplyCommand(terraform_command_variables_and_value)
	print(cmd)
	
	#change the directory to respective folder of the aws terraform
	os.chdir("aws")
	
	#initial command of terraform to get .terraform directory and providers
	os.system("terraform init")
	#run the command 
	os.system (cmd)

	#remove the other resources except the ami creation from state file
	os.system("terraform state rm \"aws_ami_from_instance.ami\" ")

	#gene
	destory =generateApplyCommand(pairs,"destory")
	os.system(destory)
	return render_template("aws.html", title="Aws")

@app.route("/azure",methods=['GET'])
def azure():
	try:
		data = json.loads(open("input.json").read())
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
		data = json.loads(open("input.json").read())
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
	data2=[]
	try:
		data2 = json.loads(open("azure_credentials.json").read())
	except:
		print("Please provide azure_credentials.json")
	credentials=[]
	for i in data2['azure_credentials']:
		if cred==i['client_id']:
			terraform_command_variables_and_value['subscription_id']=i['subscription_id']
			terraform_command_variables_and_value['tenant_id']=i['tenant_id']
			terraform_command_variables_and_value['client_id']=cred
			
			
			terraform_command_variables_and_value['client_secret']=i['client_secret']
		
    	
	cmd=generateApplyCommand(terraform_command_variables_and_value)
	print(cmd)
	
	os.chdir("azure")
	os.system("terraform init")
	os.system (cmd)
	#os.system("terraform state rm \"aws_ami_from_instance.ami\" ")
	destory =generateApplyCommand(pairs,"destory")
	os.system(destory)
	return render_template("azure.html", title="Azure")

@app.route("/gcp")
def gcp():

	#DropDown in web page contains the name of ami that user can choose 
	ami_list_filename = 'images.txt'  #loading the name of file
	ami_names = []                    #list of name of ami names
	with open(ami_list_filename) as file:
		ami_names=file.readlines()                       #reading txt file line by line
	return render_template("gcp.html", title="Aws",opt=ami_names)   



@app.route("/gcp",methods=["POST"])
def gcp_post():
	terraform_command_variables_and_value={}

	prefix=request.form['vmname']
	terraform_command_variables_and_value['prefix']=prefix
	
	boot_image=request.form['ami']
	
	file=request.files['file']
	#boot image name contain space in and we need to append that to sub-parts using  / eg. (windows-cloud/windows-2019)
	words=boot_image.split( )
	boot_image=words[0]+"/"+words[1]
	print(boot_image)
	
	terraform_command_variables_and_value['boot_image']=boot_image
	filename=secure_filename(file.filename)
	
	cwd = os.getcwd()
	print(cwd)
	
	if(boot_image.find('Windows')!=-1 or boot_image.find('windows')!=-1 or boot_image.find('WINDOWS')!=-1):
		cwd+="/gcp-win"
	else:
	    cwd+='/gcp'	
	#saving the creadentials file in respective gcp terraform directory
	file.save(os.path.join(cwd, secure_filename(file.filename)))
	terraform_command_variables_and_value['service_account_credentials_file_location']=filename
	
	#Generate the command terraform apply and variable 
	cmd=generateApplyCommand(terraform_command_variables_and_value)
	print(cmd)
    

	if(boot_image.find('Windows')!=-1 or boot_image.find('windows')!=-1 or boot_image.find('WINDOWS')!=-1):
		os.chdir("gcp-win")
	else:
		os.chdir("gcp")
	
	os.system('terraform init')
	
	os.system(cmd)
	
	os.chdir("..")
	
	return render_template("gcp.html",title="gcp")








if __name__ == '__main__':
   app.run(debug = True ,port=2000)