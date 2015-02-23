class Entity(object):
    """
    Models an entity. Differs from the driver entity in that
    check to metric relationships are also modeled as a graph.

    Edges are strings with the content of {check.id}.{metric.name}.
    Metrics are stored in a dictionary keyed by the edge.
    Checks are stored in a dictionary keyed by the edge.

    """

    def __init__(self, driver, driver_entity):
        """
        Initializes the entity object.

        @param driver - Instance of the Rackspace Cloud Monitoring Driver.
        @param driver-entity - Intance of the Rackspace Cloud Monitoring
            Entity

        """
        self.driver = driver
        self.driver_entity = driver_entity
        self.load_metrics()

    @property
    def id(self):
        """
        Returns the entity id.

        @returns - String

        """
        return self.driver_entity.id

    @property
    def label(self):
        """
        Returns the entity label

        @returns - String

        """
        return self.driver_entity.label

    def has_metric(self, metric):
        """
        Returns whether or not this entity has the specified metric.

        @param metric - String should be of the format
            {check.label}.{metric name}. Example: cpu.max_cpu_usage.
        @returns Boolean

        """
        return metric.lower() in self.metric_set

    def has_metrics(self, metrics=None):
        """
        If the set of metrics is None, Returns whether or not the entity
        has any metrics.

        If the set of metrics is a set, returns wheter or not the set of
        metrics is a subset of the entity's set of metrics.

        @param metrics - Set of metric specifications.
            Example: set(['cpu.max_cpu_usage', 'memory.total'])
        @returns Boolean

        """
        if metrics is None:
            return len(self.metric_set) > 0
        return metrics.issubset(self.metric_set)

    def get_check(self, metric):
        """
        Returns the check object in the check dict corresponding to the
        specified metric.

        @param metric - String should be of the format
            {check.label}.{metric name}. Example: cpu.max_cpu_usage.
        @returns - Check object

        """
        return self.check_dict.get(metric)

    def load_metrics(self):
        """
        Gets all checks and all metrics per check for this entity.
        Builds the graph.

        """
        # Init the relationship model
        self.check_dict = {}
        self.metric_set = set()
        self.metric_dict = {}

        # Iterate over checks
        for c in self.driver.list_checks(self.driver_entity):
            # Iterate over metrics
            for m in self.driver.list_metrics(self.driver_entity.id, c.id):
                edge_str = "%s.%s" % (c.label.lower(), m.name.lower())
                self.metric_set.add(edge_str)
                self.check_dict[edge_str] = c
                self.metric_dict[edge_str] = m


class Context(dict):
    """

    """
    def __init__(self, *args, **kwargs):
        super(Context, self).__init__(*args, **kwargs)
        self.tags = []

    def add_entity(self, entity):
        self.tags.append(entity.label)
        self['entity_id'] = entity.id
        self['entity_label'] = entity.label

        if not self.get('entity_ids'):
            self['entity_ids'] = entity.id
        else:
            self['entity_ids'] = ', '.join([self['entity_ids'], entity.id])

        if not self.get('entity_labels'):
            self['entity_labels'] = entity.label
        else:
            self['entity_labels'] = ', '.join([self['entity_labels'],
                                               entity.label])

    def add_check(self, check):
        self['check_id'] = check.id
        self['check_label'] = check.label
