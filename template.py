import cerberus
import copy
import json
import logging
import os
from string import Template
import schema
import pprint
from models import Context
from query import Query

logger = logging.getLogger('grafanizer.template')


class BaseTemplate(object):
    """
    Base Template class. Actual templates should extend this class.

    """
    def __init__(self, data):
        """
        Initializes the base template.

        @param data - Dictionary representing template.

        """
        self.data = data
        self.ctx = Context()

    def substitute(self, _str, ctx):
        """
        Treats _str as a template and does a safe substitute passing
        ctx as the mapping.

        @param _str - String template
        @param ctx - Dictionary or dictionary like object
            containing the mapping.
        @returns - String

        """
        if isinstance(_str, str) or isinstance(_str, unicode):
            _str = Template(_str).safe_substitute(ctx)
        return _str

    def finalize(self, doc):
        """
        Performs a few post templating takes.
        Removes the following:
            - type field of root level document
            - removes the metric fields from graph level documents.
        Performs the final templating of complex multi entity metrics.
        @returns - Dictionary

        """
        # Remove type
        if 'type' in doc:
            del doc['type']

        # Remove required metrics
        if 'required-metrics' in doc:
            del doc['required-metrics']

        # Remove metric specification
        for r in doc['dashboard'].get('rows', []):
            for p in r.get('panels', []):
                if 'metrics' in p:
                    for m in p['metrics']:
                        self.post_template_metric(p, m)
                    del p['metrics']
        return doc

    def row(self, row, entity):
        """
        Handles templating of the row. Mainly iterates over all panels
        in the row.

        @param row - Dictionary with row representation.
        @param entity - Entity model instance

        """
        # Iterate over panels
        for p in row.get('panels', []):
            self.panel(p, entity)

    def panel_text(self, panel, entity):
        """
        Handles templating of a text type panel.
        Does nothing for now but may be extended by subclasses.

        @param panel - Dictionary containing panel representation.
        @param entity - Entity model instance

        """
        pass

    def panel_graph(self, panel, entity):
        """
        Handles templating of a graph type panel.
        Ensures the graph has a target field that is a list.
        Iterates over the metrics specification and adds targets
        for the metrics that the entity has.

        @param panel - Dictionary panel representation.
        @param entity - Entity model instance.

        """
        # Init targets to list if not set
        if panel.get('metrics', []) and 'targets' not in panel:
            panel['targets'] = []

        # Iterate over metrics
        for m in panel.get('metrics', []):
            self.metric(panel, m, entity)

    def panel(self, panel, entity):
        """
        Handles templating of a panel.
        Mainly determines the type of the panel and delegates.

        @param panel - Dictionary representation of the panel
        @param entity - Entity model instance

        """
        if panel.get('type') == 'text':
            self.panel_text(panel, entity)
        elif panel.get('type') == 'graph':
            self.panel_graph(panel, entity)

    def metric(self, panel, metric, entity):
        """
        Branches on the type field of a metric dictionary.

        @param panel - Dictionary representation of the panel.
        @param metric - Dictionary representation of the metric.
        @param entity - Entity model instance.

        """
        if metric['type'] == "simple":
            self.simple_metric(panel, metric, entity)
        elif metric['type'] == 'complex' and metric.get('multi-entity'):
            self.complex_metric_multi(panel, metric, entity)
        elif metric['type'] == 'complex':
            self.complex_metric(panel, metric, entity)

    def complex_metric(self, panel, metric, entity):
        """
        Complex metrics involve multiple metrics.
        An example is one metric as a percentage of another metrics.
        The idea is to temporarily store each individual target by a name
        that can then be used when creating the final complex target.

        @param panel - Dictionary representation of the panel
        @param metric - Dictionary representation of the metric
        @param entity - Entity model instance.

        """
        # Template the named targets
        named_targets = {}
        for name, m in metric['named-metrics'].iteritems():
            query = Query(m['query'])
            result = query.query(entity)
            if not result:
                return
            entity, check, metric_obj = result
            self.ctx.update(entity=entity, check=check, metric=metric_obj)
            named_targets[name] = self.substitute(m['target'], self.ctx)

        # Apply named targets to the final target
        target = self.substitute(metric['target'], named_targets)

        # Apply the context to the final target
        target = self.substitute(target, self.ctx)
        panel['targets'].append({'target': target})

    def complex_metric_multi(self, panel, metric, entity):
        """
        Complex multi entity metrics involve similar metrics on multiple
        entities.
        An example would be taking the average response time of an api on
        all entities that serve the api.

        The targets of each entity are stored in a targets field for each
        named metric. These can then be referenced later to create the final
        complex target in a final pass of the document.

        @param panel - Dictionary representation of the panel
        @param metric - Dictionary representation of the metric.
        @param entity - Entity model instance.

        """
        # Iterate over named targets. Only add to aggregation if
        # all named targets are present
        named_targets = {}
        for name, m in metric['named-metrics'].iteritems():
            query = Query(m['query'])
            result = query.query(entity)
            if not result:
                return
            entity, check, metric_obj = result
            self.ctx.update(entity=entity, check=check, metric=metric_obj)
            named_targets[name] = self.substitute(m['target'], self.ctx)

        # We have a target for each query - save them
        for name, t in named_targets.iteritems():
            if not metric['named-metrics'][name].get('targets'):
                metric['named-metrics'][name]['targets'] = []
            metric['named-metrics'][name]['targets'].append(t)

    def simple_metric(self, panel, metric, entity):
        """
        Generates a simple target for a simple metrics.

        @param panel - Dictionary representation of a panel
        @param metric - Dictionary representation of a metric
        @param entity - Entity model instance

        """
        query = Query(metric['query'])
        result = query.query(entity)
        if not result:
            return
        entity, check, metric_obj = result
        self.ctx.update(entity=entity, check=check, metric=metric_obj)
        target = self.substitute(metric['target'], self.ctx)
        panel['targets'].append({'target': target})

    def post_template_metric(self, panel, metric):
        """
        Templates final results of multi entity metrics.
        Such as in averages.

        @param panel - Dictionary representation of a panel
        @param metric - Dictionary representation of a metric

        """
        if metric['type'] == 'complex' and metric.get('multi-entity'):
            named_ctx = {}
            for name, m in metric['named-metrics'].iteritems():
                # Check for empty aggregated targets. Return if even one
                # is empty
                if not m.get('targets'):
                    return
                named_ctx[name] = ','.join(m['targets'])
            target = self.substitute(metric['target'], named_ctx)
            panel['targets'].append({'target': target})


class SingleEntityTemplate(BaseTemplate):
    """
    Dashboard template for a single entity dashboard.
    Will produce one dashboard doc per entity that contains
    the required metrics.

    """
    def __init__(self, data):
        """
        Inits the SingleEntityTemplate.

        @param data - Dictionary definining the template

        """
        super(SingleEntityTemplate, self).__init__(data)
        self.docs = []

    def es_ops(self):
        """
        Produces the operations needed to store the dashboards created by this
        template in elastic search.

        @returns - List of dictionaries

        """
        ops = []
        for d in self.docs:
            d.update({
                "_op_type": "index",
                "_index": "grafana-dash",
                "_type": "dashboard",
                "dashboard": json.dumps(d['dashboard'])
            })
            ops.append(d)
        return ops

    def consume(self, entity):
        """
        Templates a dashboard if the entity is usuable.

        @param entity - Entity instance

        """
        # Make copy. This template can produce multiple documents.
        doc = copy.deepcopy(self.data)

        self.ctx = Context()

        # Iterate over rows
        for r in doc['dashboard'].get('rows', []):
            self.row(r, entity)

        if not self.ctx.current_entity:
            return

        # Apply context to ids
        id_ = doc['dashboard'].get('id')
        if id_:
            id_ = self.substitute(id_, self.ctx).replace(' ', '-').lower()
            doc['dashboard']['id'] = id_
            doc['_id'] = id_

        # Add entity label to tags
        tags = doc.get('tags', [])
        tags.append(self.ctx.entity_label())
        doc['tags'] = list(set(tags))

        # Apply context to title
        title = doc['dashboard'].get('title')
        if title:
            title = self.substitute(title, self.ctx)
            doc['dashboard']['title'] = title
            doc['title'] = title

        self.docs.append(doc)


class MultiEntityTemplate(BaseTemplate):
    """
    Dashboard template for a multi entity dashboard.
    Will produce only a single template.

    """
    def __init__(self, data):
        """
        Inits the multi entity template.

        @param data - Dictionary representing the template

        """
        super(MultiEntityTemplate, self).__init__(data)
        self.doc = self.data

    def es_ops(self):
        """
        Produces the operations needed to store the dashboards created by this
        template in elastic search.

        @returns - List of dictionaries

        """
        # Clean the dashboard
        self.doc = self.finalize(self.doc)

        # Add tag for each entity
        tags = self.doc.get('tags', []) + [e.label for e in self.ctx.entities]
        self.doc['tags'] = list(set(tags))

        self.doc.update({
            "_op_type": "index",
            "_index": "grafana-dash",
            "_type": "dashboard",
            "_id": self.doc['dashboard'].get('id'),
            "title": self.doc['dashboard']['title'],
            "dashboard": json.dumps(self.doc['dashboard']),
        })
        return [self.doc]

    def consume(self, entity):
        """
        Consumes an entity,

        @param entity - Entity instance

        """
        # Iterate over rows
        for r in self.doc['dashboard'].get('rows', []):
            self.row(r, entity)


class TemplateValidationError(Exception):
    """
    Error for when a template definition does not validate against the
    template schema.

    """
    def __init__(self, filename, validator):
        """
        Inits the error.

        @param filename - String name of the file containing the error.
        @param validator - Cerberus validator with validation errors.

        """
        self.errors = validator.errors
        self.filename = filename
        msg = "Unable to load template from %s.\n%s"
        msg = msg % (filename, pprint.pformat(validator.errors))
        super(TemplateValidationError, self).__init__(msg)


dashboard_classes = {
    'SingleEntity': SingleEntityTemplate,
    'MultiEntity': MultiEntityTemplate
}


def get_templates(path, file_=None):
    """
    Iterates over directory tree at path. If a file contains json
    that is a valid template, the the template is loaded.

    @param path - String path of the directory tree
    @param file_ - String file name - if set will load/validate just the
        specified file
    @return - List of templates

    """
    logger.debug("Getting templates")
    templates = []
    validate_header = "Validating %s: %s"
    ignore = set(['entity_types', 'entity_types.json'])

    # If file_ alone doesn't exist, try joining it with the template path
    if file_ and not os.path.isfile(file_):
        file_ = os.path.join(path, file_)

    # Create list of files to iterate over
    if file_:
        files = [file_]
    else:
        files = []
        for root, dirs, walk_files in os.walk(path):
            files += [os.path.join(root, f) for f in walk_files]

    # Iterate over the files.
    for f in files:
        try:
            # Read the file
            if os.path.basename(f) in ignore:
                logger.debug("Ignoring %s" % f)
                continue

            with open(f, 'r') as infile:
                json_data = json.loads(infile.read())

            # Validata the json against the template schema
            v = cerberus.Validator(schema.template)
            if not v.validate(json_data):
                raise TemplateValidationError(f, v)

            # Append the new template
            t = dashboard_classes[json_data['type']](json_data)
            templates.append(t)
            logger.info(validate_header % (f, 'Passed'))
        except IOError as e:
            logger.info(
                validate_header % (f, 'Failed - Unable to open file')
            )
        except ValueError as e:
            logger.info(validate_header % (f, 'Failed - Invalid JSON'))
        except TemplateValidationError as e:
            logger.info(validate_header % (f, 'Failed - Invalid template'))
            logger.info(pprint.pformat(e.errors))
    return templates
