**Description**

  - The creates a project in Gitlab SaaS.  It assumes must be in the subgroup.

**Required**

| argument           | description                            | var type |  default      |
| ------------- | -------------------------------------- | -------- | ------------ |
| gitlab_project_name   | the name of the project | string   | None         |
| group_id   | group id of subgroup | string   | None         |

**Optional**

| argument           | description                            | var type |  default      |
| ------------- | -------------------------------------- | -------- | ------------ |
| visibility_level   | visibility_level of the subgroup | string   | public         |

**Sample entry**

```
infrastructure:
   project:
       stack_name: config0-hub:::gitlab_project
       arguments:
          gitlab_project_name: test101
          group_id: 5432522
          visibility_level: private
       inputvars:
           - reference: gitlab-token
             orchestration: true
```
