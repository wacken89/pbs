# Fluentd for parsing logs
##### Application for generating logs

In directory `application/codebase` created simple application for generating random logs

```python
import random
import time

user = ("John Sonner", "Adam Walker", "Frank Sinatra", "Alex Baldwin", "Stefany Frizzell")
level = ("INFO", "WARNING", "FAIL", "CRITICAL", "DISASTER") 
message = ("User parameters updating fails", "Something goes wrong with server", "Payment disabled for user", "Connection lost", "API not availiable")

while True:
    num = random.randrange(0,5)
    print(level[num] + ' \"' + user[num] + '\" \"' + message[num] + '\"')
    time.sleep(10)
```

Output:

>INFO "John Sonner" "User parameters updating fails"
>INFO "John Sonner" "User parameters updating fails"
>WARNING "Adam Walker" "Something goes wrong with server"
>CRITICAL "Alex Baldwin" "Connection lost"
>FAIL "Frank Sinatra" "Payment disabled for user"

###### Build application and deploy it to K8s

Go to directory application and build docker container

```sh
$ cd application
$ docker build --no-cache --rm -t <imagename:tag> .
$ docker push <imagename:tag>
```

In `kube` directory change image name on your own

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: logs-generator-app
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: logs-generator
  namespace: logs-generator-app
  labels:
    app: logs
    version: beta
spec:
  replicas: 3
  selector:
    matchLabels:
      app: logs
  template:
    metadata:
      labels:
        app: logs
        version: beta
    spec:
      containers:
      - name: logs-generator
        image:  <imagename:tag>
```

Deploy application to K8s:

```sh
$ kubectl apply -f kube/deployment.yaml
```


##### Configuring Fluentd

In directory `fluentd-kubernetes` 3 files: 

*  `fluentd-deployment.yaml` - creates ServiceAccount/ClusterRole/ClusterRoleBinding/DaemonSet
*  `fluetnd-cm-app.yaml` - creates config map with regexp for application and K8s metedata
*  `fluentd-cm-nginx.yaml` - creates onfig map with regexp for nginx and K8s metedata


In `fluentd-cm-application.yaml` in `<source>` section:

```
    <source>
      @type tail
      @id in_tail_container_logs
      path /var/log/containers/logs-generator-*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      read_from_head true
      <parse>
        @type json
        time_format %Y-%m-%dT%H:%M:%S.%NZ
      </parse>
    </source>
```

Using module `tail` which parsing logs in file. In example it parsing only logs from pods `logs-generator`

First `filter` section using module `parser`  which parsing and transofrom string in key `log` to `json` :

```
    <filter kubernetes.**>
      @type parser
      key_name log
      <parse>
        @type regexp
        expression /^(?<level>[A-Z]*) "(?<user>[^\"]*)" "(?<message>[^\"]*)"$/
        time_format %d/%b/%Y:%H:%M:%S %z
      </parse>
    </filter>
```

Second `filter` section using module `kubernetes_metadata` for getting K8s metadata:

```
    <filter kubernetes.**>
      @type kubernetes_metadata
      @id filter_kube_metadata
    </filter>
```

In `fluentd-deployment.yaml` need to change environments in env section:

| Environments | Description |
| ------ | ------ | 
| FLUENT_ELASTICSEARCH_HOST | Elasticsearch url |
| FLUENT_ELASTICSEARCH_PORT | Elasticsearch port |
| FLUENT_ELASTICSEARCH_SCHEME | Elasticsearch scheme (http, https) |
| FLUENT_ELASTICSEARCH_LOGSTASH_INDEX_NAME| | Elasticsearch Index Name |
| FLUENT_ELASTICSEARCH_LOGSTASH_PREFIX | Elasticsearch Prefix |

In this example we using docker image `fluent/fluentd-kubernetes-daemonset:v1.3-debian-elasticsearch-1`. This image built with kubernets plugin for K8s


##### Deploying Fluentd

Go to directory `fluentd-kubernetes`:

```sh
$ cd fluentd-kubernetes
$ kubectl apply -f fluentd-cm-application.yaml -f fluentd-deployment.yaml
```


Check `fluentd` pods:

```sh
$ kubectl get pods
```


>NAME            READY   STATUS    RESTARTS   AGE
>fluentd-54v2f   1/1     Running   0          98m
>fluentd-knvl5   1/1     Running   0          98m
>fluentd-mw6fq   1/1     Running   0          98m
>fluentd-nwrbc   1/1     Running   0          98m



##### Configuring Indexes in Kibana

Go to your `kibana url` -> `Management` -> `Index Patterns`. Add our index from `FLUENT_ELASTICSEARCH_LOGSTASH_INDEX_NAME`

![Elasticsearch Add Index](/readme_files/addindex.png)

![Elasticsearch Add Index2](/readme_files/addindex2.png)

Go to `discover` and select our index. Now we get all `Documents` in our `Index`


![Elasticsearch Add Parsed](/readme_files/parsedapp.png)



For NGINX use file `fluentd-cm-nginx.yaml` same as `application` but chaged only regexp in `filter` on

```
    <filter kubernetes.**>
      @type parser
      key_name log
      <parse>
        @type regexp
        expression /^(?<remote>[^ ]*) (?<host>[^ ]*) (?<user>[^ ]*) \[(?<time>[^\]]*)\] "(?<method>\S+)(?: +(?<path>[^\"]*?)(?: +\S*)?)?" (?<code>[^ ]*) (?<size>[^ ]*)(?: "(?<referer>[^\"]*)" "(?<agent>[^\"]*)"(?:\s+(?<http_x_forwarded_for>[^ ]+))?)?$/
        time_format %d/%b/%Y:%H:%M:%S %z
      </parse>
    </filter>
```

In `kibana` will see:

![Elasticsearch Add Parsed](/readme_files/parsednginx.png)




