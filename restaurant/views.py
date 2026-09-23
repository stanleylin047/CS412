# Name: Stanley
# Email: stanley0@bu.edu
# File: views.py
# Description: This file contains the view functions for the restaurant application.

from django.shortcuts import render
import random
from datetime import datetime, timedelta

# Create your views here.

daily_specials = ['Spicy Edamame',
                  'Karrage Chicken',
                  'Miso Soup',
                  'Shrimp Tempura',]

def main(request):
    """
    Display the restaurant's main page.

    Parameter:
        request: The HTTP request received from the client.

    Returns:
        An HTTP response that renders the restaurant main page.
    """
    return render(request, "restaurant/main.html")

def order(request):
    """
    Select a daily special and display the restaurant's ordering page.

    Parameter:
        request: The HTTP request received from the client.

    Returns:
        An HTTP response that renders the order page with a daily special.
    """
    selected_special = random.choice(daily_specials)
    context = {
        "daily_special": selected_special,
    }
    return render(request, "restaurant/order.html", context)

def confirmation(request):
    """
    Process submitted order data and display the order confirmation page.

    Parameter:
        request: The HTTP request containing the submitted form data.

    Returns:
        An HTTP response that renders the order confirmation page.
    """
    customer_name = request.POST.get("name")
    customer_phone = request.POST.get("phone")
    customer_email = request.POST.get("email")
    customer_address = request.POST.get("address")
    selected_tonkotsu = request.POST.get("tonkotsuRamen")
    selected_tonkotsu_size = request.POST.get("tonkotsuSize")
    selected_tonkotsu_extras = request.POST.getlist("tonkotsuExtras")
    selected_miso = request.POST.get("misoRamen")
    selected_soyu = request.POST.get("soyuRamen")
    selected_daily_special = request.POST.get("daily_special")
    customer_special_instructions = request.POST.get("special_instructions")
    total = 0.0
    if selected_tonkotsu:
        total += 13.99
    if selected_miso:
        total += 11.99
    if selected_soyu:
        total += 12.99
    if selected_daily_special:
        total += 5.99

    waitTime = datetime.now() + timedelta(minutes=random.randint(30, 60))
        
    context = {
        "estimated_wait_time": waitTime,
        "name": customer_name,
        "phone": customer_phone,
        "email": customer_email,
        "address": customer_address,
        "total": total,
        "tonkotsu": selected_tonkotsu,
        "tonkotsu_size": selected_tonkotsu_size,
        "tonkotsu_extras": selected_tonkotsu_extras,
        "miso": selected_miso,
        "soyu": selected_soyu,
        "daily_special": selected_daily_special,
        "special_instructions": customer_special_instructions
    }
    return render(request, "restaurant/confirmation.html", context)




