import cerberus
import copy
import json
import logging
import os
from string import Template
import schema
import pprint
from models import Context

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
        rm = [m.lower() for m in data.get('required-metrics', [])]
        self.required_metrics = set(rm)
        self.ctx = Context()

    def canuse(self, entity):
        """
        Returns whether or not an entity fits within this template.
        Ensures that the entity has some metrics and that this template's
        set of required metrics is a subset of the entity's metrics.

        @param entity - Entity object
        @returns - Boolean

        """
        # Check if the entity has ANY metrics.
        if not entity.has_metrics():
            logger.debug("Entity %s has no metrics" % entity.label)
            return False

        # Check if the entity has the required metrics
        if not entity.has_metrics(self.required_metrics):
            logger.debug(
                "Entity %s does not have the required metrics" % entity.label
            )
            return False
        return True

    def substitute(self, _str, ctx):
        """
        Treats _str as a template and does a safe substitute passing
        ctx as the mapping.

        @param _str - String template
        @param ctx - Dictionary containing the mapping.
        @returns - String

        """
        if isinstance(_str, str) or isinstance(_str, unicode):
            _str = Template(_str).safe_substitute(ctx)
        return _str

    def clean(self, doc):
        """
        Cleans fields leftover from templating from the final document.
        Removes the 'type' field.
        Removes the 'required-metrics' field.
        Removes all 'metrics' fields.

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
        Templates a target from a metric specification if the entity
        has the metric.

        @param panel - Dictionary representation of the panel.
        @param metric - Dictionary representation of the metric.
        @param entity - Entity model instance.

        """
        metric['name'] = metric['name'].lower()
        if entity.has_metric(metric['name']):
            self.ctx.add_check(entity.get_check(metric['name']))
            target = self.substitute(metric['target'], self.ctx)
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

    def panel_text(self, panel, entity):
        """
        Applies a context to the content section of a text type panel.

        @param panel - Dictionary representation of a text type panel
        @param entity - Entity model instance

        """
        super(SingleEntityTemplate, self).panel_text(panel, entity)
        panel['content'] = self.substitute(panel['content'], self.ctx)

    def panel(self, panel, entity):
        """
        Applies a context to the title field of a panel.

        @param panel - Dictionary representation of a panel.
        @param entity - Entity model instance.

        """
        super(SingleEntityTemplate, self).panel(panel, entity)
        panel['title'] = self.substitute(panel['title'], self.ctx)

    def row(self, row, entity):
        """
        Applies a context to the title field of a row.

        @param row - Dictionary representation of a row.
        @param entity - Entity model instance.

        """
        super(SingleEntityTemplate, self).row(row, entity)
        row['title'] = self.substitute(row['title'], self.ctx)

    def consume(self, entity):
        """
        Templates a dashboard if the entity is usuable.

        @param entity - Entity instance

        """
        if not self.canuse(entity):
            return

        # Make copy. This template can produce multiple documents.
        doc = copy.deepcopy(self.data)

        self.ctx = Context()
        self.ctx.add_entity(entity)

        # Apply context to ids
        id_ = doc['dashboard'].get('id')
        if id_:
            id_ = self.substitute(id_, self.ctx).replace(' ', '-').lower()
            doc['dashboard']['id'] = id_
            doc['_id'] = id_

        # Apply context to titles
        title = doc['dashboard'].get('title')
        if title:
            title = self.substitute(title, self.ctx)
            doc['title'] = title
            doc['dashboard']['title'] = title

        # Apply context to original title
        title = doc['dashboard'].get('originalTitle')
        if title:
            title = self.substitute(title, self.ctx)
            doc['dashboard']['originalTitle'] = title

        # Iterate over rows
        for r in doc['dashboard'].get('rows', []):
            self.row(r, entity)

        doc['tags'] = list(set(doc.get('tags', []) + self.ctx.tags))
        self.docs.append(self.clean(doc))


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
        self.doc = self.clean(self.doc)

        title = self.doc['dashboard'].get('title')
        if title:
            self.doc['dashboard']['title'] = self.substitute(title, self.ctx)

        title = self.doc['dashboard'].get('originalTitle')
        if title:
            self.doc['dashboard']['originalTitle'] = self.substitute(title,
                                                                     self.ctx)

        self.doc.update({
            "_op_type": "index",
            "_index": "grafana-dash",
            "_type": "dashboard",
            "_id": self.doc['dashboard'].get('id'),
            "title": self.doc['dashboard']['title'],
            "tags": list(set(self.doc.get('tags', []) + self.ctx.tags)),
            "dashboard": json.dumps(self.doc['dashboard']),
        })
        return [self.doc]

    def consume(self, entity):
        """
        Consumes an entity,

        @param entity - Entity instance

        """
        # Check if entity fits this template
        if not self.canuse(entity):
            logger.debug("Can't use entity: %s" % entity.label)
            return

        self.ctx.add_entity(entity)

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
