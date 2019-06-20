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


Same output in json:

```json
{
  "_index": "pbs-app-2019.06.20",
  "_type": "fluentd",
  "_id": "Pq1sdWsBIUk8DCg7Kilo",
  "_version": 1,
  "_score": null,
  "_source": {
    "level": "DISASTER",
    "user": "Stefany Frizzell",
    "message": "API not availiable",
    "docker": {
      "container_id": "41c0fadf4d0bd43ebb443316a82a838d5e543e4d53da94d2687cd501748fc514"
    },
    "kubernetes": {
      "container_name": "logs-generator",
      "namespace_name": "logs-generator-app",
      "pod_name": "logs-generator-d489555f9-jwswb",
      "container_image": "wacken/logs-generator:beta-2",
      "container_image_id": "docker-pullable://wacken/logs-generator@sha256:a9eac59fac4d93e8273cdf16d05b1b90d3a7d8966bcd4b2c7967644e22827394",
      "pod_id": "8dcdca6c-934a-11e9-b7d8-96000028f204",
      "labels": {
        "app": "logs",
        "pod-template-hash": "d489555f9",
        "version": "beta"
      },
      "host": "kc-fluentd-app-worker4",
      "master_url": "https://10.43.0.1:443/api",
      "namespace_id": "f61ff9e8-9346-11e9-b7d8-96000028f204",
      "namespace_labels": {
        "field_cattle_io/projectId": "p-tnvtx"
      }
    },
    "@timestamp": "2019-06-20T15:05:46.561534572+00:00",
    "tag": "kubernetes.var.log.containers.logs-generator-d489555f9-jwswb_logs-generator-app_logs-generator-41c0fadf4d0bd43ebb443316a82a838d5e543e4d53da94d2687cd501748fc514.log"
  },
  "fields": {
    "@timestamp": [
      "2019-06-20T15:05:46.561Z"
    ]
  },
  "sort": [
    1561043146561
  ]
}
```


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




