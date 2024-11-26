from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from .models import Product, Cart, CartItem, Order, Customer


def home(request):
    products = Product.objects.all()
    if not products:
        return render(request, 'shop/home.html', {'message': 'No products available.'})
    return render(request, 'shop/home.html', {'products': products})

# Product details page
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)  # Fetch product by id
    return render(request, 'shop/product_detail.html', {'product': product})

# Cart page
def cart(request):
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to login if the user is not authenticated

    try:
        customer = Customer.objects.get(user=request.user)  # Get the customer from the logged-in user
    except Customer.DoesNotExist:
        return HttpResponse("Customer does not exist. Please register as a customer.")  # Error if no customer exists
    
    cart = Cart.objects.filter(customer=customer, created_at__isnull=False).first()
    if cart:
        cart_items = CartItem.objects.filter(cart=cart)  # Get cart items related to the cart
        total_price = sum(item.total_price() for item in cart_items)  # Calculate the total price
        return render(request, 'shop/cart.html', {'cart_items': cart_items, 'total_price': total_price})
    else:
        return HttpResponse("Your cart is empty!")

# Add to cart
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to login if the user is not authenticated

    try:
        customer = Customer.objects.get(user=request.user)  # Get the customer
    except Customer.DoesNotExist:
        return HttpResponse("Customer does not exist. Please register as a customer.")  # Error if no customer exists

    product = get_object_or_404(Product, id=product_id)  # Get the product by its ID
    cart, created = Cart.objects.get_or_create(customer=customer)  # Get or create a cart for the customer

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)  # Get or create a cart item for the product
    if not created:
        cart_item.quantity += 1  # Increase quantity if the item already exists in the cart
    cart_item.save()

    return redirect('cart')  # Redirect to the cart page

# Delete cart item
def delete_cart_item(request, item_id):
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to login if the user is not authenticated

    cart_item = get_object_or_404(CartItem, id=item_id)  # Get the cart item to delete
    cart_item.delete()  # Delete the cart item

    return redirect('cart')  # Redirect to the cart page

# Checkout (Create an order)
def checkout(request):
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to login if the user is not authenticated

    try:
        customer = Customer.objects.get(user=request.user)  # Get the customer
    except Customer.DoesNotExist:
        return HttpResponse("Customer does not exist. Please register as a customer.")  # Error if no customer exists
    
    cart = Cart.objects.filter(customer=customer, created_at__isnull=False).first()
    if not cart:
        return HttpResponse("Your cart is empty!")  # Error if no cart exists
    
    cart_items = CartItem.objects.filter(cart=cart)  # Get cart items
    total_price = sum(item.total_price() for item in cart_items)  # Calculate total price

    # Create an order
    order = Order.objects.create(
        customer=customer,
        cart=cart,
        status='Pending',  # Default status is 'Pending'
    )
    
    # You could include payment processing logic here
    
    return render(request, 'shop/order_summary.html', {'order': order, 'total_price': total_price})

# Register a new user
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            customer = Customer(user=user, address="")
            customer.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Registration failed. Please check the form.")
    else:
        form = UserCreationForm()
    
    return render(request, 'shop/register.html', {'form': form})

# Login user
def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid login credentials.")
    else:
        form = AuthenticationForm()

    return render(request, 'shop/login.html', {'form': form})

# Logout user
def logout_user(request):
    logout(request)
    return redirect('home')
