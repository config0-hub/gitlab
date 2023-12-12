#{
#  "concurrent": 4,
#  "check_interval": 0,
#  "runners": [
#    {
#      "name": "gitlab-runner-autoscaler",
#      "url": "https://gitlab.com",
#      "token": "",
#      "executor": "docker+machine",
#      "limit": 4,
#      "docker": {
#        "tls_verify": false,
#        "image": "node:12",
#        "privileged": true,
#        "disable_cache": true,
#        "shm_size": 0
#      },
#      "cache": {
#        "Type": "s3",
#        "Shared": true,
#        "s3": {
#          "ServerAddress": "s3.amazonaws.com",
#          "AccessKey": "your-access-key",
#          "SecretKey": "your-secret-key",
#          "BucketName": "s3-cache-bucket-name",
#          "BucketLocation": "s3-cache-bucket-name-location"
#        }
#      },
#      "machine": {
#        "MachineDriver": "amazonec2",
#        "MachineName": "gitlab-ci-machine-%s",
#        "OffPeakTimezone": "",
#        "OffPeakIdleCount": 0,
#        "OffPeakIdleTime": 0,
#        "IdleCount": 0,
#        "MachineOptions": [
#          "amazonec2-access-key=your-access-key",
#          "amazonec2-secret-key=your-secret-key",
#          "amazonec2-region=us-east-2",
#          "amazonec2-vpc-id=vpc-0175846a",
#          "amazonec2-subnet-id=subnet-dbb6afb3",
#          "amazonec2-zone=a",
#          "amazonec2-use-private-address=true",
#          "amazonec2-tags=gitlab-runner-autoscaler,gitlab,group-runner",
#          "amazonec2-security-group=launch-wizard-1",
#          "amazonec2-instance-type=t2.medium",
#          "amazonec2-request-spot-instance=true",
#          "amazonec2-spot-price=0.05",
#          "amazonec2-block-duration-minutes=60"
#        ],
#        "autoscaling": [
#          {
#            "Periods": [
#              "* * 9-17 * * mon-fri *"
#            ],
#            "IdleCount": 50,
#            "IdleTime": 3600,
#            "Timezone": "UTC"
#          },
#          {
#            "Periods": [
#              "* * * * * sat,sun *"
#            ],
#            "IdleCount": 5,
#            "IdleTime": 60,
#            "Timezone": "UTC"
#          }
#        ]
#      }
#    }
#  ]
#}
#

def _get_cache_config(stack):

    s3 = { "ServerAddress": "s3.amazonaws.com",
           "AccessKey": stack.gitlab_runner_aws_access_key,
           "SecretKey": stack.gitlab_runner_aws_secret_key,
           "BucketName": stack.s3_bucket,
           "BucketLocation": stack.aws_default_region
           }

    cache = { "Type": "s3",
              "Shared": True,
              "s3": s3
              }

    return cache

def _get_machine_options(stack):

    MachineOptions = [ "amazonec2-access-key={}".format(stack.gitlab_runner_aws_access_key),
                       "amazonec2-secret-key={}".format(stack.gitlab_runner_aws_secret_key),
                       "amazonec2-region={}".format(stack.aws_default_region),
                       "amazonec2-vpc-id={}".format(stack.vpc_id),
                       "amazonec2-subnet-id={}".format(stack.subnet_id),
                       "amazonec2-zone={}".format(stack.aws_zone),
                       "amazonec2-use-private-address=true",
                       "amazonec2-tags=gitlab-runner-autoscaler,gitlab,group-runner",
                       "amazonec2-security-group={}".format(stack.sg_id),
                       "amazonec2-instance-type=t2.medium",
                       "amazonec2-request-spot-instance=true",
                       "amazonec2-spot-price={}".format(int(stack.spot_price)),
                       "amazonec2-block-duration-minutes={}".format(int(stack.block_duration_minutes))
                       ]

    machine = { "MachineDriver": "amazonec2",
                "MachineName": "gitlab-ci-machine-%s",
                "OffPeakTimezone": "",
                "OffPeakIdleCount": 0,
                "OffPeakIdleTime": 0,
                "IdleCount": 0,
                "MachineOptions": MachineOptions
                }

    return machine

def _get_autoscaling(stack):

    autoscaling = None

    if stack.get_attr("gitlab_runner_autoscaling_hash"):
        try:
            autoscaling = stack.b64_decode(stack.gitlab_runner_autoscaling_hash)
        except:
            autoscaling = None

    if autoscaling: return autoscaling

    autoscaling = [ { "Periods": [ "* * 9-17 * * mon-fri *"],
                      "IdleCount": 5,
                      "IdleTime": 3600,
                      "Timezone": "UTC"
                      },
                    { "Periods": [ "* * * * * sat,sun *" ],
                      "IdleCount": 1,
                      "IdleTime": 60,
                      "Timezone": "UTC"
                      }
                    ]

    return autoscaling

def _get_gitlab_runner_toml(stack):
    
    import toml

    runner = { "name": "gitlab-runner-autoscaler",
               "url": "https://gitlab.com",
               "token": stack.gitlab_token,
               "executor": "docker+machine",
               "limit": 4,
               "docker": { "tls_verify": False,
                           "image": stack.gitlab_docker_image,
                           "privileged": True,
                           "disable_cache": True,
                           "shm_size": 0
                           },
               "cache": stack._get_cache_config(stack),
               "machine": stack._get_machine_options(stack),
               }

    autoscaling = stack._get_autoscaling(stack)

    if autoscaling: runner["autoscaling"] = autoscaling

    values = { "concurrent": int(stack.runner_concurrent),
               "check_interval": 0,
               "runners": [ runner ]
               }

    with open(stack.gitlab_runner_config_file,"w") as _f:
        toml.dump(values,_f )

    toml_str_b64 = stack.b64_encode(open(stack.gitlab_runner_config_file,"r").read())

    return toml_str_b64

def _get_user_data_ubuntu(stack):

    toml_str_b64 = _get_gitlab_runner_toml(stack)

    _data = '''
apt-get update
apt-get install apt-transport-https ca-certificates curl gnupg-agent software-properties-common -y

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

base=https://github.com/docker/machine/releases/download/v0.16.0 &&
curl -L $base/docker-machine-$(uname -s)-$(uname -m) >/tmp/docker-machine &&
sudo mv /tmp/docker-machine /usr/local/bin/docker-machine &&
chmod +x /usr/local/bin/docker-machine

curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | sudo bash
apt-get install gitlab-runner -y 

echo {} | base64 -d > /etc/gitlab-runner/config.toml

systemctl daemon-reload
systemctl restart gitlab-runner.service

# to do manually
#gitlab-runner register
    '''.format(toml_str_b64)

    user_data = _data + "\n"

    return stack.b64_encode(user_data.encode('utf-8')).decode('ascii')

def run(stackargs):

    import os
    import json

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="gitlab_group_name")  # gitlab group name

    stack.parse.add_required(key="runner_docker_image",default="alpine")
    stack.parse.add_required(key="runner_concurrent",default="4")
    stack.parse.add_required(key="s3_bucket",default="4")
    stack.parse.add_required(key="aws_default_region",default="us-east-1")
    stack.parse.add_required(key="aws_zone",default="a")
    stack.parse.add_required(key="spot_price",default="0.05")
    stack.parse.add_required(key="block_duration_minutes",default="60")
    stack.parse.add_required(key="vpc_id")  # we can query this resources through selector
    stack.parse.add_required(key="subnet_ids")  # we can query this resources through selector
    stack.parse.add_required(key="sg_id")  # we can query this resources through selector

    stack.parse.add_required(key="gitlab_token")
    stack.parse.add_required(key="gitlab_runner_aws_access_key")
    stack.parse.add_required(key="gitlab_runner_aws_secret_key")
    stack.parse.add_optional(key="gitlab_runner_autoscaling_hash",default="null")

    stack.parse.add_optional(key="stateful_id",default="_random")
    stack.parse.add_optional(key="docker_exec_env",default="elasticdev/terraform-run-env:1.3.7")

    # Add execgroup
    stack.add_execgroup("config0-hub:::gitlab::subgroup")

    # Initialize Variables in stack
    stack.init_variables()
    stack.init_execgroups()
    stack.init_substacks()

    stack.set_variable("subnet_id",stack.subnet_ids.split(",")[0])

    # temp file
    stack.set_variable("gitlab_runner_config_file",os.path.join("/tmp",stack.random_id()))
