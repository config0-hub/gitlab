**Description**

  - The creates a subgroup in Gitlab SaaS.  Note, you can only create parent groups on the UI.

**Required**

| argument           | description                            | var type |  default      |
| ------------- | -------------------------------------- | -------- | ------------ |
| group_name   | name of the subgroup | string   | None         |
| parent_id   | parent_id of the parent group | string   | None         |
| visibility_level   | visibility_level of the subgroup | string   | public         |

**Optional**

| argument           | description                            | var type |  default      |
| ------------- | -------------------------------------- | -------- | ------------ |
| group_path   | path of the subgroup | string   | None         |

**Sample entry**

```
labels:
   general: 
     environment: dev
     purpose: ci
infrastructure:
   subgroup:
       stack_name: config0-hub:::gitlab_subgroup
       arguments:
          group_name: gitlabci-101
          visibility_level: private
       inputvars:
           - reference: gitlab-parent-group
             orchestration: true
           - reference: gitlab-token
             orchestration: true
       labels:
           - general
```
