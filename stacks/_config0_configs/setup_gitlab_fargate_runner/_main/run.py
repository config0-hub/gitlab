class Main(newSchedStack):

    def __init__(self,stackargs):

        newSchedStack.__init__(self,stackargs)

        # Add default variables
        self.parse.add_required(key="ci_environment")
        self.parse.add_required(key="parent_id",default="null")
        self.parse.add_required(key="visibility_level",default="public")

        self.parse.add_required(key="vpc_id")
        self.parse.add_required(key="vpc_name")
        self.parse.add_required(key="subnet_ids")
        self.parse.add_required(key="sg_id")
        self.parse.add_required(key="bastion_sg_id",default="null")
        self.parse.add_required(key="instance_type",default="t3.micro") 
        self.parse.add_required(key="disksize",default="20") 

        self.parse.add_required(key="docker_host") 
        self.parse.add_required(key="src_build_groups",default="config0-hub:::gitlab::runner,config0-hub:::gitlab::runner-autoscaling")
        self.parse.add_required(key="docker_repo_name")

        self.parse.add_required(key="gitlab_runners_token_hash")
        self.parse.add_required(key="gitlab_runner_aws_access_key")
        self.parse.add_required(key="gitlab_runner_aws_secret_key")

        self.parse.add_optional(key="suffix_id",default="null")
        self.parse.add_optional(key="suffix_length",default="4")  

        self.parse.add_optional(key="aws_default_region",default="us-west-1")
        self.parse.add_optional(key="aws_account_id",default="null")  # use inputvars if possible

        self.parse.add_optional(key="cloud_tags_hash",default="null")
        self.parse.add_optional(key="bucket_acl",default="private")

        # Add substack
        self.stack.add_substack('config0-hub:::gitlab_subgroup')
        self.stack.add_substack('config0-hub:::aws_s3_bucket')
        self.stack.add_substack('config0-hub:::new_ec2_ssh_key')
        self.stack.add_substack('config0-hub:::aws_iam_role')
        self.stack.add_substack('config0-hub:::ec2_ubuntu_admin')
        self.stack.add_substack('config0-hub:::docker_build_ssh')
        self.stack.add_substack('config0-hub:::delete_resource')

        self.stack.init_substacks()
    
    def _get_gitlab_group_name(self):

        suffix_id = self._determine_suffix_id()
        return "{}-{}".format(self.stack.ci_environment,suffix_id)

    def _determine_suffix_id(self):

        if self.stack.get_attr("suffix_id"): 
            return str(self.stack.suffix_id).lower()

        return self.stack.b64_encode(self.stack.ci_environment)[0:int(self.stack.suffix_length)].lower()

    def _set_cloud_tag_hash(self):

        try:
            cloud_tags = self.stack.b64_decode(self.stack.cloud_tags_hash)
        except:
            cloud_tags = {}

        cloud_tags["ci_environment"] = self.stack.ci_environment
        cloud_tags["aws_default_region"] = self.stack.aws_default_region

        return self.stack.b64_encode(cloud_tags)

    def _get_bucket_name(self):

        suffix_id = self._determine_suffix_id()

        # cache shared bucket
        s3_bucket = "gitlab-runner-{}-{}".format(self.stack.ci_environment,suffix_id)

        return s3_bucket

    def _set_ec2_params(self):

        self.stack.set_variable("ssh_key_name","{}-ssh_key".format(self.stack.docker_host))
        self.stack.set_variable("role_name","{}-role".format(self.stack.docker_host))
        self.stack.set_variable("iam_instance_profile","{}-profile".format(self.stack.docker_host))
        self.stack.set_variable("iam_role_policy_name","{}-policy".format(self.stack.docker_host))

    def run_sshkey(self):

        self.stack.init_variables()

        self._set_ec2_params()

        overide_values = { "key_name":self.stack.ssh_key_name }
        default_values = { "aws_default_region":self.stack.aws_default_region }

        inputargs = {"default_values":default_values,
                     "overide_values":overide_values}
    
        inputargs["automation_phase"] = "infrastructure"
        inputargs["human_description"] = 'Create and upload ssh key name {}'.format(self.stack.ssh_key_name)
    
        return self.stack.new_ec2_ssh_key.insert(display=True,**inputargs)

    def run_s3(self):

        self.stack.init_variables()
        self.stack.set_parallel()

        cloud_tags_hash = self._set_cloud_tag_hash()
        s3_bucket = self._get_bucket_name()

        default_values = { "aws_default_region":self.stack.aws_default_region }

        overide_values = { "bucket": s3_bucket,
                           "acl": self.stack.bucket_acl,
                           "cloud_tags_hash":cloud_tags_hash,
                           "force_destroy": "true" }

        inputargs = { "default_values":default_values,
                      "overide_values":overide_values }
    
        inputargs["automation_phase"] = "infrastructure"
        inputargs["human_description"] = 'Create s3 bucket {}'.format(s3_bucket)
    
        return self.stack.aws_s3_bucket.insert(display=True,**inputargs)

    def run_subgroup(self):

        self.stack.init_variables()

        default_values = {}

        overide_values = { "group_name": self._get_gitlab_group_name(),
                           "visibility_level":self.stack.visibility_level }

        inputargs = { "default_values":default_values,
                      "overide_values":overide_values }

        inputargs["automation_phase"] = "infrastructure"
        inputargs["human_description"] = 'Add subgroup {}'.format(overide_values["group_name"])
    
        return self.stack.gitlab_subgroup.insert(display=True,**inputargs)

    def _get_gitlab_runner_toml(self):

        '''
LogLevel = "info"
LogFormat = "text"

[Fargate]
 Cluster = "acme-gitlab-RUNNER-TAGS-cluster"
 Region = "eu-west-1"
 Subnet = "SUBNET"
 SecurityGroup = "SECURITY_GROUP_ID"
 TaskDefinition = "gitlab-runner-RUNNER_TAGS-task"
 EnablePublicIP = false

[TaskMetadata]
 Directory = "/opt/gitlab-runner/metadata"

[SSH]
 Username = "root"
 Port = 22
        '''
        
        import toml

        #ecs_task_definition
        #enable_public_ip
        #ecs_name
    
        values = { "LogLevel": "info",
                   "LogFormat": "text" }

        values["TaskMetadata"] = { "Directory":"/opt/gitlab-runner/metadata"}

        values["SSH"] = { "Username":"root",
                          "Port": 22 }

        values["Fargate"] = { "Cluster": self.stack.ecs_name,
                              "Region": self.stack.aws_default_region,
                              "Subnet": self.stack.subnet_ids.split(",")[0],
                              "SecurityGroup": self.stack.ecs_task_definition,
                              "EnablePublicIP": self.stack.enable_public_ip }
    
        with open(_config_file,"w") as _f:
            toml.dump(values,_f )
    
        toml_str_b64 = self.stack.b64_encode(open(self.stack.gitlab_runner_config_file,"r").read())
    
        return toml_str_b64

    def _cleanup(self):

        overide_values = {"must_exists":True}
        overide_values["hostname"] = self.stack.docker_host
        overide_values["resource_type"] = "server"

        inputargs = {"overide_values":overide_values}

        human_description = "Destroying docker_host docker_host {}".format(self.stack.docker_host)
        inputargs["automation_phase"] = "infrastructure"
        inputargs["human_description"] = human_description

        return self.stack.delete_resource.insert(display=True,**inputargs)

    def _get_aws_account_id(self):

        if self.stack.get_attr("aws_account_id"):
            return self.stack.aws_account_id

        aws_account_id = self.stack.inputvars.get("aws_account_id")

        if aws_account_id:
            return aws_account_id

        if not aws_account_id:
            raise Exception("aws_account_id must be provided")

    def run_build(self):

        import json

        self.stack.init_variables()
        self._set_ec2_params()

        default_values = { "aws_default_region":self.stack.aws_default_region,
                           "docker_host":self.stack.docker_host,
                           "docker_repo_name":self.stack.docker_repo_name }  # update repo_name  # testtest110

        overide_values = { "ssh_key_name":self.stack.ssh_key_name,
                           "aws_account_id":self._get_aws_account_id(),
                           "overide_order_timeout":600 }

        add_env_vars = { "GITLAB_TOKEN": self.stack.b64_decode(self.stack.gitlab_runners_token_hash),
                         "SECURITY_GROUP_ID":self.stack.bastion_sg_id,
                         "SUBNET":self.stack.subnet_ids.split(",")[0],
                         "GITLAB_URL":"https://gitlab.com",
                         "DOCKER_ENV_FIELDS":"GITLAB_TOKEN,SECURITY_GROUP_ID,SUBNET,GITLAB_URL,RUNNER_TAGS" }

        for src_group in self.stack.to_list(self.stack.src_build_groups):

            docker_image_tag = src_group.split("::")[-1]

            add_env_vars["RUNNER_TAGS"] = "gitlab,elastidev,{}".format(docker_image_tag)

            overide_values["add_env_vars"] = json.dumps(add_env_vars)
            overide_values["build_src_group"] = src_group
            overide_values["docker_image_tag"] = docker_image_tag

            inputargs = { "default_values":default_values,
                          "overide_values":overide_values}

            self.stack.docker_build_ssh.insert(display=True,**inputargs)

        return self._cleanup()

    def run_iam_role(self):

        self.stack.init_variables()
        self._set_ec2_params()

        overide_values = { "role_name":self.stack.role_name,
                           "iam_instance_profile":self.stack.iam_instance_profile,
                           "iam_role_policy_name":self.stack.iam_role_policy_name
                           }

        default_values = { "aws_default_region":self.stack.aws_default_region }

        inputargs = {"default_values":default_values,
                     "overide_values":overide_values}
    
        inputargs["automation_phase"] = "infrastructure"
        inputargs["human_description"] = 'Create IAM role for {}'.format(self.stack.docker_host)
    
        return self.stack.aws_iam_role.insert(display=True,**inputargs)

    def run_docker_host(self):

        self.stack.init_variables()

        self._set_ec2_params()

        user_data_hash = self.stack.b64_encode('echo "cloud-init done"')

        overide_values = { "hostname":self.stack.docker_host,
                           "spot": True,
                           "ip_key": "public_ip",
                           "user_data_hash": user_data_hash,
                           "ssh_key_name":self.stack.ssh_key_name,
                           "iam_instance_profile":self.stack.iam_instance_profile,
                           "publish_to_saas":True }

        default_values = { "vpc_name":self.stack.vpc_name,
                           "vpc_id":self.stack.vpc_id,
                           "subnet_ids":self.stack.subnet_ids,
                           "size": self.stack.instance_type,
                           "disksize": self.stack.disksize,
                           "aws_default_region":self.stack.aws_default_region,
                           "sg_id":self.stack.bastion_sg_id,
                           }

        inputargs = {"default_values":default_values,
                     "overide_values":overide_values}
    
        inputargs["automation_phase"] = "infrastructure"
        inputargs["human_description"] = 'Create EC2 admin {}'.format(self.stack.docker_host)
    
        return self.stack.ec2_ubuntu_admin.insert(display=True,**inputargs)

    #def run_fargate_runner_manager(self):
    #    self.stack.init_variables()

    def run(self):
    
        self.stack.unset_parallel()
        self.add_job("sshkey")
        self.add_job("iam_role")
        self.add_job("s3")
        self.add_job("subgroup")
        self.add_job("docker_host")
        self.add_job("build")
        #self.add_job("fargate_runner_manager")

        return self.finalize_jobs()

    def schedule(self):

        sched = self.new_schedule()
        sched.job = "subgroup"
        sched.archive.timeout = 1800
        sched.archive.timewait = 120
        sched.conditions.retries = 1 
        sched.automation_phase = "infrastructure"
        sched.human_description = 'Create Gitlab subgroup'
        sched.on_success = [ "s3" ]
        self.add_schedule()

        sched = self.new_schedule()
        sched.job = "s3"
        sched.archive.timeout = 1200
        sched.archive.timewait = 120
        sched.automation_phase = "infrastructure"
        sched.human_description = "Create s3 buckets"
        sched.on_success = [ "iam_role" ]
        self.add_schedule()

        sched = self.new_schedule()
        sched.job = "iam_role"
        sched.archive.timeout = 1800
        sched.archive.timewait = 120
        sched.automation_phase = "infrastructure"
        sched.human_description = "Create IAM credentials"
        sched.on_success = [ "sshkey" ]
        self.add_schedule()

        sched = self.new_schedule()
        sched.job = "sshkey"
        sched.archive.timeout = 1200
        sched.archive.timewait = 120
        sched.automation_phase = "infrastructure"
        sched.on_success = [ "docker_host" ]
        sched.human_description = "Upload user public ssh key"
        self.add_schedule()

        sched = self.new_schedule()
        sched.job = "docker_host"
        sched.archive.timeout = 1200
        sched.archive.timewait = 120
        sched.automation_phase = "infrastructure"
        sched.on_success = [ "build" ]
        sched.human_description = "Create temp docker_host"
        self.add_schedule()

        sched = self.new_schedule()
        sched.job = "build"
        sched.archive.timeout = 3600
        sched.archive.timewait = 300
        sched.automation_phase = "infrastructure"
        sched.human_description = "Build docker images"
        self.add_schedule()

        return self.get_schedules()
