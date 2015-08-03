import logging
import limiters

logger = logging.getLogger('grafanizer.models')


class Check(object):
    """
    Models a check. Differs from driver check in that metrics are fetched
    when instance is created.

    """
    def __init__(self, driver, driver_check, entity_id):
        """
        Inits the check instance.

        @param driver - Instance of Rackspace Cloud Monitoring Driver
        @param driver_check - Instance of the Rackspace Cloud Monitoring
            Check
        @param entity_id - String id of parent entity

        """
        self.driver = driver
        self.driver_check = driver_check
        self.entity_id = entity_id
        self.load_metrics()

    @property
    def id(self):
        """
        Returns the check id

        @returns - String

        """
        return self.driver_check.id

    @property
    def label(self):
        """
        Returns the check label

        @returns - String

        """
        return self.driver_check.label

    def load_metrics(self):
        """
        Loads the metrics for the check.

        """
        limiters.get_limiter('api').get_token()
        self.metrics = \
            [m for m in self.driver.list_metrics(self.entity_id, self.id)]


class Entity(object):
    """
    Models an entity. Differs from the driver entity in that
    all entity checks are fetched when instance is created.

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
        self.load_checks()

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

    def load_checks(self):
        """
        Gets all checks for this entity.

        """
        self.checks = []
        limiters.get_limiter('api').get_token()
        for c in self.driver.list_checks(self.driver_entity):
            self.checks.append(Check(self.driver, c, self.id))


class Context(object):
    """
    Simple data structure for remembering data as a template is created.

    """
    def __init__(self):
        self._valid_keys = set([
            'entity_id', 'entity_label',
            'check_id', 'check_label',
            'metric_name'
        ])
        self.entities = set()
        self.checks = set()
        self.metrics = set()
        self.current_entity = None
        self.current_check = None
        self.current_metric = None

    def update(self, entity=None, check=None, metric=None):
        """
        Updates the context.

        @param entity - Entity instance
        @param check - Check instance
        @param metric - Metric instance

        """
        if entity:
            self.entities.add(entity)
            self.current_entity = entity
        if check:
            self.checks.add(check)
            self.current_check = check
        if metric:
            self.metrics.add(metric)
            self.current_metric = metric

    def entity_id(self):
        """
        Return current entity's id

        @return - String | None

        """
        if self.current_entity:
            return self.current_entity.id
        return None

    def entity_label(self):
        """
        Return the current entity's label

        @return - String | None

        """
        if self.current_entity:
            return self.current_entity.label
        return None

    def check_id(self):
        """
        Return the current check's id

        @return - String | None

        """
        if self.current_check:
            return self.current_check.id
        return None

    def check_label(self):
        """
        Return the current check's label

        @return - String | None

        """
        if self.current_check:
            return self.current_check.label
        return None

    def metric_name(self):
        """
        Return the current metric's name

        @return - String | None

        """
        if self.current_metric:
            return self.current_metric.name
        return None

    def __getitem__(self, key):
        """
        Allows the context to be passed into a python string template.

        @param key - String
        @return - String | None

        """
        if key in self._valid_keys:
            return getattr(self, key)()
        return None
