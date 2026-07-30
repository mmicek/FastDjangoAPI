# Common Features (mostly ASYNC FastAPI)

This package provides a collection of utilities and abstractions inspired by Django and Django REST Framework using SQLAlchemy,
designed to make FastAPI development faster, more structured, and easier to maintain.

## Configuration
#### 1. Environment-based configuration
   A simple settings system that allows loading configuration values from environment variables with support for sensible defaults.
   This provides a centralized place for managing application settings across development, testing, and production environments.
#### 2. Application setup and lifespan management
   Provides a streamlined application bootstrap process with built-in support for FastAPI lifespan events.
   - Run main.py directly during development (with uvicorn included).
   - Deploy in production by exposing get_app() and running uvicorn separately.
   - Easily extend startup and shutdown logic for custom integrations.
#### 3. Unified exception handling
   Built-in exception handlers that convert framework and application errors into a consistent JSON response format.
  
   Included handlers:
   - http_exception_handler
   - request_validation_exception_handler
   - internal_server_error_handler

   Features:
   - Standardized error responses across the entire API.
   - Base exception class for defining custom application exceptions.
   - Support for attaching detailed validation and business error information.
#### 4. Context variables for request and database access
   Request and database session objects are automatically stored in context variables.
   This enables accessing the current request or database session from anywhere in the application, including asynchronous code,
   without explicitly passing them through function parameters.

   Benefits:
   - Similar developer experience to Django's thread-local request patterns.
   - Reduces dependency injection boilerplate.
   - Simplifies service-layer implementations.

## Database Features
#### 5. SQLAlchemy integration with session management
   Comprehensive SQLAlchemy integration with FastAPI.

   Features include:
   - Database session manager.
   - Automatic session lifecycle handling.
   - FastAPI dependency integration.
   - Support for synchronous and asynchronous workflows.
#### 6. Base entity model with common CRUD helpers
   A reusable SQLAlchemy base model (BaseEntity) providing convenience methods commonly needed by application entities.

   Examples include:
   - Create, update, save, and delete helpers.
   - Common query utilities.
   - Reduced boilerplate when working with models.
#### 7. get_object_or_404
   Utility method for retrieving database objects by arbitrary conditions.
   If no matching object exists, a 404 Not Found exception is automatically raised and transformed into a standardized API response.
   Inspired by Django's get_object_or_404.
#### 8. Transaction management with nested transaction support
   Advanced transaction handling implemented as both decorators and context managers.
   Inspired by Django's transaction.atomic.

   Features:
   - Automatic transaction management.
   - Support for nested transactions using SQL SAVEPOINTs.
   - Easy definition of atomic operations.
#### 9. Alembic integration
   Seamless integration with Alembic migrations.

   Features:
   - Automatic support for the provided BaseEntity.
   - Simplified migration generation workflow.
   - Consistent database schema evolution process.

## Endpoint Definitions
#### 10. DRF-like ViewSets
   Implementation of Django REST Framework-inspired ViewSets that significantly reduce the amount of code required to build REST APIs.

   Built-in support for:
   - CRUD operations.
   - Pagination.
   - Filtering.
   - Automatic route generation.
   - Serializer integration.
#### 11. Django-style ViewSet lifecycle methods
   ViewSets expose familiar extension points inspired by Django REST Framework.
   These hooks make endpoint behavior highly customizable while maintaining a clean structure.

   Available features include:
   - get_queryset()
   - get_object()
   - self.action
   - self.pk
   - perform_create()
   - perfrom_update()
   - perform_destroy()
   - create_from_serializer
   - serialize_from_object
#### 12. Custom actions
   Support for defining custom endpoints directly on ViewSets.

   Features:
   - DRF-like @action pattern.
   - Reuse of ViewSet functionality.
   - Access to ViewSet context and helper methods.
   - Ability to create entity-specific business operations without introducing additional controllers.

   Examples:
   - /users/{id}/activate
   - /orders/{id}/cancel
   - /projects/{id}/archive
#### 13. BaseSerializer
   Serializer abstraction for request validation and response serialization.

   Features:
   - Input validation.
   - Output transformation.
   - Computed and custom fields.
   - Clear separation between API contracts and persistence models.
#### 14. Advanced serializer fields
   Additional serializer field implementations that simplify working with relationships and custom conversions.

   * ConvertableField:
       Allows automatic transformation between external representations and internal values.
  
       Useful for:
       - Enum conversions.
       - Formatting values.
       - Custom serialization logic.

   * PrimaryKeyRelation:
       Automatically resolves related entities using primary keys or custom lookup conditions.
  
       Benefits:
       - Eliminates repetitive lookup code.
       - Simplifies handling of foreign key relationships in API payloads.
#### 15. Advanced filtering support
   Flexible filtering system supporting multiple query styles.

   Supported approaches:
   a) MUI X Grid filters - Native support for GridFilterModel, making integration with Material UI data grids straightforward.
   b) Django-style filtering - Query parameter syntax inspired by Django ORM lookups:
       - name__icontains=john
       - email__iexact=test@example.com
       - created_at__gte=2024-01-01

   Implemented on top of fastapi-filter.
#### 16. Trailing slash normalization
   TrailingSlashRedirectMiddleware automatically normalizes incoming request URLs by removing trailing slashes.

## Testing
#### 17. Testcontainers integration
   Built-in support for Testcontainers to simplify database testing in local and CI/CD environments.
   You need to have Docker installed for that.

   Features:
   - Automatic container lifecycle management.
   - Integration with the database manager.
   - Option to connect directly to an existing database without Docker.
#### 18. Automatic test database integration
   Testing fixtures automatically configure and prepare the test database environment.

   Capabilities include:
   - Database initialization.
   - Schema preparation.
   - Automatic entity setup.
#### 19. Transactional tests
   Each test runs inside its own database transaction that is rolled back after execution.

   Benefits:
   - No manual cleanup required.
   - Faster test execution.
   - Reliable test isolation.
#### 20. Testing helper utilities
   Common utilities designed to reduce repetitive testing code.
   These helpers simplify API and database testing.

   Included helpers:
   - create_entity_factory
   - assert_status
   - convert_dict_to_query_params
   - get_body_from_entity
#### 21. Factory-based object creation
   Enhanced support for generating test data through factories using Faker and factory-boy.

   Features:
   - Flexible object creation.
   - Customizable default values.
   - Integration with create_entity_factory.
#### 22. Automatic CRUD test generation
   Generate standard CRUD test suites for ViewSets automatically.
   This helps ensure consistency across endpoints while significantly reducing the amount of repetitive test code.

   Verifies behaviors such as:
   - List operations.
   - Retrieve operations.
   - Object creation.
   - Updates.
   - Deletion.
  
   Implementation:
   crud_view_set_test(client: TestClient, entity: BaseEntity, view_set: type[GenericViewSet])

# EXAMPLES:

#### 1. Environment-based configuration
Running the application:
- Development - From the '/backend' directory, start the application using one of the following methods:
  * fastapi dev
  * uv run fastapi dev --entrypoint hive.main:get_app
  * python main.py  ->  inside /backend/hive
- For production development, run Uvicorn directly using the application factory:
  * uvicorn hive.main:get_app --factory

#### 2. Application setup and lifespan management
Application settings are defined in 'config.py' using a centralized settings class (BaseSettings from pydantic_settings).
  
    DATABASE_HOST: str = "localhost"

The value will be automatically loaded from corresponding environment variable ('DATABASE_HOST') if it exits.
Otherwise, the default value specified in the configuration class will be used.

The settings class also exposes several computed properties, including:
- `database_connection_string` – generates the full database connection URL based on the configured database settings.
- `environment` – determines the currently active application environment using the `SPRING_PROFILES_ACTIVE` environment variable.
This approach provides a single source of truth for application configuration while keeping environment-specific settings external to the codebase.
#### 3. Unified exception handling
The framework provides a common exception handling mechanism that automatically converts application and FastAPI exceptions into a standardized JSON response format.

    class ForeignKeyViolationException(ApiBaseException):
       error_code = ApiErrorCode.FOREIGN_KEY_VIOLATION_EXCEPTION
       default_message = "Update or delete on table violates foreign key constraint."
    

Registered exception handlers will automatically catch the exception and convert it into the common API error response format.
Additional details can be attached dynamically when raising the exception. These values will be included in the serialized error response:

    raise ForeignKeyViolationException(fk=object.relation_fk)

#### 4. Context variables for request and database access
Request and database session objects can be automatically stored in context variables, making them accessible from anywhere in the application without explicitly passing them through function parameters.
To enable this functionality for a router, register the provided dependencies:

    router = APIRouter(
       prefix="...",
       dependencies=[Depends(set_database_session_context), Depends(set_request_session_context)],
    )

Once configured, you can access the current database session or request object from any layer of the application:

    session: AsyncSession = get_request_db_session()
    request: Reuqest = get_request_session()

#### 5. SQLAlchemy integration with session management
The framework provides a `DatabaseSessionManager` responsible for managing database connections and SQLAlchemy `AsyncSession` instances.
`DatabaseSessionManager` is initialized once during application startup as part of the FastAPI lifespan. It manages the underlying database engine and provides utilities for creating sessions and connections when needed.
For HTTP requests, database sessions are created automatically and attached to the request context. This means you do not need to manually create or inject a database session into every endpoint.

#### 6. Base entity model with common CRUD helpers
All models/entities must inherit from BaseEntity. This enables consistent behavior across the ORM layer and allows tests to automatically generate or populate schemas from entity definitions.
For this to work properly, all entities must be imported at runtime. This is handled via imports.py, which is imported in env.py.

    class Book(BaseEntity):
       id: int
       name: str
    
    
       pages: Mapped[list["Page"]] = relationship("Page", back_populates="book")  # sqlalchemy
    
    class Page(BaseEntity):
       id: int
       chapter: int | None
       content: str
       book_id: Mapped[int] = mapped_column(ForeignKey("book", nullable=False)
    
    
       book: Mapped[Book] = relationship("Book", back_populates="pages")  # sqlalchemy

In the example above:
* Book maps to the book table
* Page maps to the page table
* A Book can have multiple Page records
* Each Page belongs to a single Book via book_id

#### 7. get_object_or_404
This method returns an object matching the given condition or raises a 404 Not Found error with a specific message.
The for_update option can be used to apply a transaction-level lock on the selected row.

    obj = get_object_or_404(select(Entity), Entity.id == pk, for_update=for_update)

#### 8. Transaction management with nested transaction support
A context manager or decorator that manages database transactions automatically. It ensures a commit on successful execution, or a rollback if an exception occurs.

    @atomic
    async def function():
       # Some busineess logic here
    
    
    OPEN TRANSACTION
    function()
    COMMIT (if no exception)
    ROLLBACK (if exception occurs)

#### 9. Alembic integration
Alembic uses configuration loaded from config.py, specifically the BaseSettings class.
The database connection string is taken from 'settings.database_connection_string'.
This ensures the migration environment is aligned with the application configuration.

To generate a new migration inside '/backend' run:

    alembic revision --autogenerate -m "your_message"

To apply all pending migrations:
  
    alembic upgrade head

#### 10. DRF-like ViewSets
You can easily define CRUD endpoints for your entities using ViewSets.
To implement HTTP methods, create a class that inherits from GenericViewSet and add the appropriate mixins for the methods you want to expose.

Those mixins are:
- ListMixin      -> GET /books (supports pagination ?page=10&page_size=20)
- RetrieveMixin  -> GET with pk /books/{pk}
- CreateMixin    -> POST /books
- UpdateMixin    -> PATCH /books/{pk}
- DestroyMixin   -> DELTE /books/{pk}

If all methods are required, you can simply use "ModelViewSet". This includes all mixins by default.
GenericViewSet supports generics for typing purposes. This is optional.
  
    class BookViewSet(ModelViewSet[Book]):
       ...

The GET list endpoint for list of object supports pagination (page/page_size) and advanced filtering via filter_class.

Each ViewSet must define:
- **url_prefix**: URL segment used during registration
- **model**: entity the ViewSet operates on
- **serializer_class**: output schema for GET endpoints (see point 13. for serializers)
- **create_serializer_class**: input schema for POST
- **update_serliazer_class**: (optional) intput schema for PATCH. If not provided it is auto-generated from 'create_serializer_class'
- **filter_class**: (optional) defines filtering rules for list endpoint (see point 15. for filters)   

Custom endpoints can be added using the **@action** decorator. This operates in the context of the ViewSet and allow extending standard CRUD behavior.
Assume we have Book and Page models (see point 6.). ViewSet's would look like:

    class BookViewSet(ModelViewSet):
       url_prefix = "books"
       model = Book
       serializer_class = BookSerializer  # (see point 13.)
       create_serializer_class = BookCreateSerializer
       update_serializer_class = BookUpdateSerializer  # (optional)
       filter_class = BookFilter  # (optional - see point 15.)
      
       @action(method="post", detail=True, url_path="add-page/")  # Custom endpoint - add page to book
       async def add_page(self, body: PageNestedSerializer):
           book = self.get_object()  # Fetch book object. see point 11.
           page = await self.create_from_serializer(  # Create a page object from input body. Connect it to book using **kwargs
               body, Page, add_and_commit=True, book_id=book.id
           )
           return self.serialize_from_object(page, PageSerializer)  # Return serializer newly create Page object as a response.
    
    
    class PageViewSet(GenericViewSet[Page], ListMixin, RetrieveMixin):  # Read only endpoints
       url_prefix = "pages"
       model = Page
       serializer_class = PageSerializer

To register a ViewSet, use the register class method and pass the router:
  
    router = APIRouter(prefix="api/v1")
    
    BookViewSet.register(router)  -> endpoints will be /api/v1/books/({pk})/. For custom action: /api/v1/books/{pk}/add-page/
    PageViewSet.register(router)  -> endpoints will be /api/v1/pages/({pk})/

#### 11. Django-style ViewSet lifecycle methods
There are several utilities available in ViewSets, that improve flexibility and control over request handling.

- self.action             -  (property async-safe) current endpoint name
- self.pk                 -  (property async-safe) primary key from request
- get_queryset()          -  (method) override to customize query logic
- get_object()            -  (method) retrieves the current object
- perform_create()        -  (method) override to customize POST create logic
- perfrom_update()        -  (method) override to customize PATCH update logic
- perform_destroy()        -  (method) override to customize DELETE delete logic
- create_from_serializer  -  (method) creates entity from serializer
- serialize_from_object   -  (method) converts entity to response serializer

**a) action** - Indicates which endpoint is being executed. For standard CRUD (mixins) endpoints the values are: list, retrieve, create, update, delete.
For custom action value uses the method name e.g 'add_page'.

Typically used inside 'qet_queryset()' to adjust queries per endpoint.
For example, when listing objects you typically want to return only lightweight fields (e.g for Book id and name).
However, for a detail view you may include related/nested data such a foreign key relations (e.g pages for a book).

In such cases, you should avoid loading related entities in the list endpoint to prevent slow queries, and only join/load them for the retrieve endpoint.
    
    def get_queryset(self):
       qs = select(Book)
       if self.action == "retrieve":
           qs = qs.options(joinedload(Book.pages))
       return qs

**b) pk** - returns the object identifier when detail=True is used on action (see point 12.)

**c) get_queryset()** - override this method to define different SQL queries depending on http method, action type and endpoint context.

**d) get_object()** - returns the entity instance for the current request. Used in detail=True actions, automatically fetches object by pk, raises 404 if not found.

**e) create_from_serializer** - this method creates an entity instance from serializer data (typically from the request body) and optionally persists it to the database.
Parameters add_and_commit=True if enabled, the entity is inserted into the database and the transaction is commited.
Parameter fetch_related=True resolves all 'PrimaryKeyRelation's fields defined in the serializer (see point 14.).

**f) serialize_from_object** - converts an entity instance into a serializer-ready response object.

**g) perform_create()** - it is commonly overridden to automatically inject data not provided by the client, such as assigning the currently logged-in user as the owner of the object.

**h) perfrom_update()** - developers typically override this to trigger post-update logic, send email notifications, or log changes right after an object is modified.

**i) perform_destroy()** - it is frequently overridden to implement soft deletes (marking an object as inactive instead of wiping it) or to handle cleanup tasks like deleting associated cloud storage files.

#### 12. Custom actions
The @action decorator allows defining custom endpoints inside a ViewSet. These endpoints can handle specific HTTP methods and operate either
on a single object or on a collection. All actions must be defined within a ViewSet and are automatically registered to the router when the ViewSet is registered.

Parameters:
- **url_path (str)** -> defines a final part of the URL, appended to viewset.url_prefix
- **method (str)** -> HTTP method used by the endpoint (get, post, patch, delete, etc.)
- **detail (bool)** -> Defines scope of the endpoint. If True operates on a single object (/{pk} is added automatically). If False operates on the entire collection.

@action is a thin abstraction over standard FastAPI endpoints. It adds automatic router registration, automatic handling of {pk} when detail=True and possibility of usage ViewSet's methods.
All standard FastAPI features remain available like: path parameters, query parameters, request body and dependency injection.

Example below presents how to return only one page from exact book:

    @action(method="get", detail=True, url="/page/{page_id}")  # Endpoint: /api/v1/books/{book_id}/page/{page_id}
    async def get_page(self, page_id: int):
       book = self.get_object()
       page = [p for p in book.pages if p.id == page_id]
       # Check if page exist ...
       return self.serialize_from_object(page, PageSerializer)

#### 13/14. Serializers and Advanced serializer fields
BaseSerializer supports two core features, that extend standard Pydantic validation with ORM-aware behavior.

ConvertableField - a custom Pydantic Field wrapper that attaches value conversion metadata.
It stores a conversion mapping inside JSON schema metadata, allowing external processing layers to transform values before validation. Example:

    rotate_90_degree: bool | None = ConvertableField(
       ...,
       conversion_mapping={None: False}
    )

PrimaryKeyRelation - a custom annotated field representing a foreign-key relationship resolved via a primary key.
It extends a simple integer input with metadata describing how related entities should be resolved from database level.

Key concept:
- Separates relationship resolution from validation logic
- Enables explicit loading of related ORM entities outside validation

The **'source'** attribute defines where the resolved object will be assigned. If source if provided, resolved entity is attached to the serializer instance.
If not provided, only existence validation is performed (no assignment).

To resolve all PrimaryKeyRelations you must explicitly call: await .fetch_related()

Example:

    class PageCreate(RelatedBaseModel):
       book_id:  Annotated[int, PrimaryKeyRelation(model=Book, source="book")]
    
    page = PageCreate(book_id=1)
    await book.fetch_related()  # Must be called explicitly; handled automatically in GenericViewSet
    page.book  # -> Book instance resolved from foreign key


#### 15. Advanced filtering support
BaseFilter specified and set on a ViewSet enables advanced filtering for the GET list endpoint using query parameters.
It is build on top of 'fastapi-filter' (https://pypi.org/project/fastapi-filter/),
so it supports all its features. Each filter must implement 'Constants.model[BaseEntity]',
which defines the entity the filter operates on and determines which fields are available for filtering.

BaseFilter also supports nested filtering using double underscore notation. For example:

    ?book__page__content_ilike=Search in content

This allows filtering across related entities in a chain, where operators like ilike can be applied to nested fields.
Once a BaseFilter is assigned to a ViewSet via 'filter_class ', it is automatically applied to the list endpoint.

BaseModelFilter also provides additional options:

##### Django-DRF
`BaseModelFilter` provides a filtering mechanism inspired by Django REST Framework.
By specifying the `fields` option, the framework automatically generates query parameters in the following format:

    {field_name}__{operator}

The available operators depend on the underlying field type.
Supported operators:

    STRING_OPERATORS = ["eq", "neq", "like", "ilike", "isnull"]
    NUMBER_OPERATORS = ["eq", "neq", "gt", "gte", "lt", "lte", "in"]
    DATETIME_OPERATORS = ["eq", "neq", "gt", "gte", "lt", "lte"]
    BOOL_OPERATORS = ["eq", "isnull"]


You can explicitly define which model fields should be exposed for filtering:
    
    class PageFilter(BaseModelFilter):
    
       class Constants(Filter.Constants):
           model = Page
           fields = ["chapter", "content"]

The example above will resolve the following filters:
    
    chapter__eq, chapter__neq, chapter__gt, chapter__gte, chapter__lt, chapter__lte, chapter__in
    content__eq, content__neq, content__like, content__ilike, content__isnull

If you want to enable filtering for every field of the model, set:
    
    class Constants(Filter.Constants):
       model = Page
       fields = "__all__"

Specific fields can then be excluded using `exclude_fields`:

    class Constants(Filter.Constants):
       model = Page
       fields = "__all__"
       exclude_fields = ["created_at", "updated_at"]

##### MUI X Grid filters
Possibility to filter instancer over very simple language using search parameter:

    TODO

#### 18. Automatic test database integration
The framework provides fixtures that automatically initialize and configure a database environment for tests.
A `context_db` fixture is available and returns an `AsyncSession` scoped to the currently executing test. Each test runs inside its own database transaction, ensuring complete isolation between tests.
During test setup, the fixture uses `DatabaseSessionManager` to initialize the test database schema based on all entities inheriting from `BaseEntity`.

Example usage:

    async def test_create_book(context_db: AsyncSession):

#### 20. Testing helper utilities

The framework provides a set of helper utilities designed to simplify writing database and API tests, reducing boilerplate and improving readability.

#### create_entity_factory
Utility function for creating database entities or Factory Boy model instances.
Missing attributes are automatically populated with realistic fake data using `faker`,
while specific values can be overridden using keyword arguments. The created object can optionally be persisted to the database.
The utility supports both:
- SQLAlchemy entities inheriting from `BaseEntity`
- Factory Boy factories inheriting from `SQLAlchemyModelFactory`

Signature:

    async def create_entity_factory(
       session: AsyncSession,
       entity_type: Type[BaseEntity] | Type[SQLAlchemyModelFactory],
       add_and_commit: bool = True,
       **overrides,
    ) -> T

Example factory-boy usage:


    from factory.alchemy import SQLAlchemyModelFactory
    
    class PageFactory(SQLAlchemyModelFactory):
       book_id = factory.LazyAttribute(lambda _: 1)  # For static value for example
    
       class Meta:
           model = Page
    
    
    page = create_entity_factory(context_db, PageFactory, add_and_commit=True, content="My custom content")

In the example above:
- `book_id` will always be set to `1` because it is defined in the factory.
- `content` will be set to `"My custom content"` only for this instance.
- Any remaining fields (for example, `chapter`) will be automatically generated using `faker`.

#### assert_status
Helper function that validates the response status code and provides detailed debugging information when the assertion fails.

Signature:

    def assert_status(response, status_code: int = 200, text=None)

Unlike a simple assertion such as: **assert response.status_code == 200**, this helper will include the response body in the failure output,
making it significantly easier to diagnose test failures.

#### convert_dict_to_query_params(d: dict)
Converts a dictionary into a URL query string. like: ?a=1&b=2. Useful when constructing query parameters dynamically in tests.

#### get_body_from_entity(entity: BaseEntity) -> dict
Converts an entity instance into a dictionary representation suitable for API request bodies.
This utility is particularly useful when testing create and update endpoints, as it eliminates the need to manually construct request payloads from existing entities.
