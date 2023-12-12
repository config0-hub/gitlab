def run(stackargs):

    import json

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="group_name")
    stack.parse.add_required(key="parent_id",default="null")
    stack.parse.add_required(key="visibility_level",default="public")

    stack.parse.add_optional(key="group_path",default='null')
    stack.parse.add_optional(key="stateful_id",default="_random")
    stack.parse.add_optional(key="docker_exec_env",default="elasticdev/terraform-run-env:1.3.7")
    stack.parse.add_optional(key="publish_to_saas",default="null")

    # Add execgroup
    stack.add_execgroup("config0-hub:::gitlab::subgroup")
    stack.add_substack('config0-hub:::config0-core::publish_resource')

    # Initialize Variables in stack
    stack.init_variables()
    stack.init_execgroups()
    stack.init_substacks()

    stack.set_variable("resource_type","gitlab_group")

    if not stack.get_attr("group_path"):
        stack.set_variable("group_path",stack.group_name)

    if not stack.get_attr("parent_id") and stack.inputvars.get("parent_id"):
        stack.logger.debug_highlight("parent_id found in inputvars")
        stack.set_variable("parent_id",stack.inputvars["parent_id"])

    env_vars = {"stateful_id".upper(): stack.stateful_id }
    env_vars["resource_type".upper()] = stack.resource_type
    env_vars["docker_exec_env".upper()] = stack.docker_exec_env
    env_vars["TF_VAR_group_name"] = stack.group_name
    env_vars["TF_VAR_group_path"] = stack.group_path
    env_vars["TF_VAR_parent_id"] = stack.parent_id
    env_vars["TF_VAR_visibility_level"] = stack.visibility_level

    env_vars["METHOD"] = "create"
    env_vars["RESOURCE_TAGS"] = "{}".format(stack.resource_type)

    docker_env_fields_keys = env_vars.keys()
    docker_env_fields_keys.append("GITLAB_TOKEN")
    docker_env_fields_keys.remove("METHOD")

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)

    inputargs = {"display":True}
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["display"] = True
    inputargs["stateful_id"] = stack.stateful_id
    inputargs["human_description"] = 'Creating subgroup "{}"'.format(stack.group_name)
    stack.subgroup.insert(**inputargs)

    if not stack.get_attr("publish_to_saas"): 
        return stack.get_results()

    # publish the info
    keys_to_publish = [ "id",
                        "name",
                        "full_name",
                        "full_path",
                        "visibility_level",
                        "resource_type",
                        "parent_id" ]

    overide_values = { "name":stack.name }
    default_values = { "resource_type":stack.resource_type }
    default_values["publish_keys_hash"] = stack.b64_encode(keys_to_publish)

    inputargs = { "default_values":default_values,
                  "overide_values":overide_values }

    inputargs["automation_phase"] = "infrastructure"
    inputargs["human_description"] = 'Publish resource info for {}'.format(stack.resource_type)
    stack.publish_resource.insert(display=True,**inputargs)

    return stack.get_results()
