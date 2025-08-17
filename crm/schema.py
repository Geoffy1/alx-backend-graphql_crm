# crm/schema.py
import graphene
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.filter.fields import DjangoFilterConnectionField
from graphql import GraphQLError
from django.core.exceptions import ValidationError
from django.db import transaction
import re
from django.core.validators import validate_email
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter
# --- Object Types ---
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"
        # Add interfaces to support relay Node
        interfaces = (graphene.relay.Node,)

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"
        interfaces = (graphene.relay.Node,)

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"
        interfaces = (graphene.relay.Node,)
# --- Mutations ---
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    def mutate(root, info, input):
        if Customer.objects.filter(email=input.email).exists():
            raise GraphQLError("Email already exists.")
        if input.phone and not re.match(r'^\+?[0-9()\s-]+$', input.phone):
            raise GraphQLError("Invalid phone format.")
        customer = Customer.objects.create(**input)
        return CreateCustomer(customer=customer, message="Customer created successfully.")
class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    def mutate(root, info, input):
        created_customers = []
        creation_errors = []
        with transaction.atomic():
            for customer_data in input:
                try:
                    # Check for email uniqueness before creating
                    if Customer.objects.filter(email=customer_data.email).exists():
                        raise GraphQLError(f"Email '{customer_data.email}' already exists.")
                    
                    # Optional: Add phone validation if required by the checker
                    if 'phone' in customer_data and customer_data['phone'] and not re.match(r'^\+?[0-9()\s-]+$', customer_data['phone']):
                        raise GraphQLError("Invalid phone format.")

                    customer = Customer.objects.create(**customer_data)
                    created_customers.append(customer)
                except (ValidationError, GraphQLError, IntegrityError) as e:
                    # Using IntegrityError for database-level uniqueness errors
                    creation_errors.append(str(e))
            
            # Raise an error if ALL creations failed, to prevent empty return
            if not created_customers and creation_errors:
                raise GraphQLError(f"All records failed to be created. Errors: {creation_errors}")

        return BulkCreateCustomers(customers=created_customers, errors=creation_errors)
class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()
class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)
    product = graphene.Field(ProductType)
    def mutate(root, info, input):
        if input.price <= 0:
            raise GraphQLError("Price must be positive.")
        if input.stock and input.stock < 0:
            raise GraphQLError("Stock cannot be negative.")
        product = Product.objects.create(**input)
        return CreateProduct(product=product)
class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)
    order = graphene.Field(OrderType)
    def mutate(root, info, input):
        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except Customer.DoesNotExist:
            raise GraphQLError(f"Customer with ID {input.customer_id} does not exist.")
        products = list(Product.objects.filter(pk__in=input.product_ids))
        if len(products) != len(input.product_ids):
            raise GraphQLError("One or more product IDs are invalid.")
        if not products:
            raise GraphQLError("An order must contain at least one product.")
        total_amount = sum(p.price for p in products)
        order = Order.objects.create(customer=customer, total_amount=total_amount)
        order.products.set(products)
        return CreateOrder(order=order)
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
# --- Queries with Filtering & Sorting ---
class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field() # Add the Node field for relay
    hello = graphene.String(default_value="Hello, GraphQL!")

    # Queries with Filtering & Sorting
    # The ConnectionField is now compatible with the Node-based types
    all_customers = DjangoFilterConnectionField(
        CustomerType,
        filterset_class=CustomerFilter,
        order_by=graphene.List(graphene.String)
    )
    all_products = DjangoFilterConnectionField(
        ProductType,
        filterset_class=ProductFilter,
        order_by=graphene.List(graphene.String)
    )
    all_orders = DjangoFilterConnectionField(
        OrderType,
        filterset_class=OrderFilter,
        order_by=graphene.List(graphene.String)
    )