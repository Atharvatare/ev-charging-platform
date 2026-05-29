import pydantic
import uuid
from typing import Optional, Any, List

# Sentinel for Field default
_sentinel = object()

class QueryExpression:
    def __init__(self, attr_name, op, value):
        self.attr_name = attr_name
        self.op = op
        self.value = value

    def evaluate(self, item):
        val = getattr(item, self.attr_name, None)
        # Convert UUID to string if comparing UUID with string
        if isinstance(val, uuid.UUID) and isinstance(self.value, str):
            try:
                val_str = str(val)
                val_value = self.value
                if self.op == '==': return val_str == val_value
                if self.op == '!=': return val_str != val_value
            except ValueError:
                pass
        if isinstance(self.value, uuid.UUID) and isinstance(val, str):
            try:
                val_value = str(self.value)
                val_str = val
                if self.op == '==': return val_str == val_value
                if self.op == '!=': return val_str != val_value
            except ValueError:
                pass

        if self.op == '==':
            return val == self.value
        elif self.op == '!=':
            return val != self.value
        elif self.op == '<':
            return val < self.value
        elif self.op == '<=':
            return val <= self.value
        elif self.op == '>':
            return val > self.value
        elif self.op == '>=':
            return val >= self.value
        return False

class QueryAttribute:
    def __init__(self, model_class, attr_name):
        self.model_class = model_class
        self.attr_name = attr_name
        self.descending = False

    def desc(self):
        self.descending = True
        return self

    def __eq__(self, other):
        return QueryExpression(self.attr_name, '==', other)

    def __ne__(self, other):
        return QueryExpression(self.attr_name, '!=', other)

    def __lt__(self, other):
        return QueryExpression(self.attr_name, '<', other)

    def __le__(self, other):
        return QueryExpression(self.attr_name, '<=', other)

    def __gt__(self, other):
        return QueryExpression(self.attr_name, '>', other)

    def __ge__(self, other):
        return QueryExpression(self.attr_name, '>=', other)

class SQLModel(pydantic.BaseModel):
    # Enable field assignment validation and compatibility
    model_config = pydantic.ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True
    )

    def __init_subclass__(cls, table: bool = False, **kwargs):
        super().__init_subclass__(**kwargs)
        # Create class-level query attributes for all defined fields
        for field_name in cls.model_fields:
            setattr(cls, field_name, QueryAttribute(cls, field_name))

def Field(
    default: Any = _sentinel,
    *,
    default_factory: Any = None,
    primary_key: bool = False,
    index: bool = False,
    unique: bool = False,
    nullable: bool = True,
    foreign_key: str = None,
    **kwargs
):
    p_kwargs = {}
    if default is not _sentinel:
        p_kwargs["default"] = default
    if default_factory is not None:
        p_kwargs["default_factory"] = default_factory
    
    # Keep only recognized Pydantic Field arguments
    allowed = {
        'alias', 'title', 'description', 'examples', 'exclude', 'include',
        'repr', 'init', 'init_var', 'kw_only', 'pattern', 'strict',
        'gt', 'ge', 'lt', 'le', 'multiple_of', 'min_length', 'max_length'
    }
    for k, v in kwargs.items():
        if k in allowed:
            p_kwargs[k] = v
            
    # Add metadata for extra db-related attributes in json_schema_extra
    extra = {}
    if primary_key: extra["primary_key"] = True
    if index: extra["index"] = True
    if unique: extra["unique"] = True
    if nullable is not None: extra["nullable"] = nullable
    if foreign_key: extra["foreign_key"] = foreign_key
    p_kwargs["json_schema_extra"] = extra
    
    return pydantic.Field(**p_kwargs)

def Relationship(*args, **kwargs):
    return pydantic.Field(default=None)

class SelectQuery:
    def __init__(self, model_class):
        self.model_class = model_class
        self.filters = []
        self.order_by_attr = None

    def where(self, *expressions):
        self.filters.extend(expressions)
        return self

    def order_by(self, expression):
        self.order_by_attr = expression
        return self

    def execute(self):
        from app.core.database import db_store, _link_relationships
        name = self.model_class.__name__.lower()
        items = []
        if name == "user":
            items = list(db_store.users.values())
        elif name == "station":
            items = list(db_store.stations.values())
        elif name == "port":
            items = list(db_store.ports.values())
        elif name == "solarinsight":
            items = list(db_store.solar_insights.values())
        elif name == "reservation":
            items = list(db_store.reservations.values())
        elif name == "wallettransaction":
            items = list(db_store.wallet_transactions)
        elif name == "routetrip":
            items = list(db_store.route_trips)

        # Apply filters
        filtered_items = []
        for item in items:
            match = True
            for f in self.filters:
                if hasattr(f, 'evaluate'):
                    if not f.evaluate(item):
                        match = False
                        break
                elif callable(f):
                    if not f(item):
                        match = False
                        break
            if match:
                filtered_items.append(item)

        # Link relationships
        for item in filtered_items:
            _link_relationships(item)

        # Apply sorting
        if self.order_by_attr:
            attr_name = getattr(self.order_by_attr, 'attr_name', None)
            desc = getattr(self.order_by_attr, 'descending', False)
            if attr_name:
                filtered_items.sort(key=lambda x: getattr(x, attr_name, None) or 0, reverse=desc)

        class QueryResult:
            def __init__(self, res_list):
                self.res_list = res_list
            def all(self):
                return self.res_list
            def first(self):
                return self.res_list[0] if self.res_list else None
        return QueryResult(filtered_items)

def select(model_class):
    return SelectQuery(model_class)

class text:
    def __init__(self, query_string):
        self.query_string = query_string

class Session:
    # Expose Session class that delegates to InMemorySession or acts as a placeholder
    def __init__(self, engine=None):
        from app.core.database import InMemorySession
        self.session = InMemorySession()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
