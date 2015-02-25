Description
===========

A small python library for templating entities into useful Grafana dashboard.

Dependencies
============
* [Cerberus](https://cerberus.readthedocs.org/en/latest/)
* [Elasticsearch Client](https://elasticsearch-py.readthedocs.org/en/master/)
* [Eventlet](http://eventlet.net/)
* [Rackspace monitoring driver](https://github.com/racker/rackspace-monitoring)
* [libcloud](https://libcloud.apache.org/)

Installation
============

Download this repo by cloning it with git or by downloading the archive.

Create a directory for logging.
```shell
mkdir /var/log/grafanizer
```

Edit ~/.grafanizerrc
```yaml
datasource:
  username: <your username>
  api_key: <your api key>
  url: https://monitoring.api.rackspacecloud.com/v1.0
pool_size: 100
template_dir: ~/templates
```

Make grafanizer executable
```shell
chmod +x grafanizer
```

Running Grafanizer
==================

Run all templates in the configured template directory:

```shell
./grafanizer
```

Validate all templates in the configured template directory:
```shell
./grafanizer --validate
```

Run just one specific template:
```shell
./grafanizer --file special.json
```

Configuration
=============
Grafanizer will look to ~/.grafanizerrc by default for configuration.
The format of this file should be either yaml or json. The path to the configuration file can be specified by either:

setting the environment variable 'G_CONFIG_FILE'
```shell
export G_CONFIG_FILE=/somedir/somefile
```

or by providing the path to the command line
```shell
./grafanizer --g-config-file /somedir/somefile
```

In addition, individual configuration parameters can be overridden by either environment variables or by providing values to the command line.

| config parameter    | environment variable  | command line argument   | description |
| ----------------    | --------------------  | ---------------------   | ----------- |
| pool_size           | G_POOL_SIZE           | --g-pool-size           | Integer number of green thread workers. Defaults to 100 |
| template_dir        | G_TEMPLATE_DIR        | --g-template-dir        | Path to directory containing templates. Defaults to ~/templates |
| retries             | G_RETRIES             | --g-retries             | Number of times to retry if error occurs. |
| datasource:url      | G_DATASOURCE_URL      | --g-datasource_url      | Url |
| datasource:username | G_DATASOURCE_USERNAME | --g-datasource-username | Username |
| datasource:api_key  | G_DATASOURCE_API_KEY  | --g-datasource-api-key  | Api key |
